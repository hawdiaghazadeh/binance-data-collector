"""Split-trunk actor-critic network (G34)."""

from __future__ import annotations

from typing import Any

from quant_platform.rl_product.observation.schema import ObservationSchema


def _require_torch():
    try:
        import torch
        import torch.nn as nn
    except ImportError as exc:
        raise ImportError("torch is required for rl_product.agent") from exc
    return torch, nn


def _build_mlp(nn, in_dim: int, hidden: tuple[int, ...], out_dim: int):
    layers: list[Any] = []
    prev = in_dim
    for width in hidden:
        layers.extend([nn.Linear(prev, width), nn.Tanh()])
        prev = width
    layers.append(nn.Linear(prev, out_dim))
    return nn.Sequential(*layers)


class SplitTrunkActorCritic:
    """Price-wide / context-narrow trunks — context zeros when master_gate=0 in obs."""

    def __init__(
        self,
        schema: ObservationSchema,
        *,
        price_trunk_hidden: tuple[int, ...] = (256, 128),
        context_trunk_hidden: tuple[int, ...] = (32, 16),
        portfolio_trunk_hidden: tuple[int, ...] = (32, 16),
        action_dim: int = 1,
    ) -> None:
        torch, nn = _require_torch()
        self.schema = schema
        self.action_dim = action_dim
        slices = schema.block_slices()

        self._price_slice = slices["price_action"]
        self._context_slice = slices["context"]
        self._portfolio_slice = slices["portfolio"]

        price_dim = self._price_slice.stop - self._price_slice.start
        context_dim = self._context_slice.stop - self._context_slice.start
        portfolio_dim = self._portfolio_slice.stop - self._portfolio_slice.start

        self.price_trunk = _build_mlp(nn, price_dim, price_trunk_hidden, price_trunk_hidden[-1])
        self.context_trunk = _build_mlp(nn, context_dim, context_trunk_hidden, context_trunk_hidden[-1])
        self.portfolio_trunk = _build_mlp(
            nn, portfolio_dim, portfolio_trunk_hidden, portfolio_trunk_hidden[-1]
        )

        trunk_out = price_trunk_hidden[-1] + context_trunk_hidden[-1] + portfolio_trunk_hidden[-1]
        self.policy_head = nn.Linear(trunk_out, action_dim)
        self.value_head = nn.Linear(trunk_out, 1)
        self.log_std = nn.Parameter(torch.zeros(action_dim))

        self._torch = torch

    def _module_parameters(self):
        for module in (
            self.price_trunk,
            self.context_trunk,
            self.portfolio_trunk,
            self.policy_head,
            self.value_head,
        ):
            yield from module.parameters()
        yield self.log_std

    def trunk_features(self, obs, *, zero_context: bool = False, zero_price: bool = False):
        torch = self._torch
        price = obs[:, self._price_slice]
        context = obs[:, self._context_slice]
        if zero_price:
            price = torch.zeros_like(price)
        if zero_context:
            context = torch.zeros_like(context)
        portfolio = obs[:, self._portfolio_slice]
        price_h = self.price_trunk(price)
        context_h = self.context_trunk(context)
        portfolio_h = self.portfolio_trunk(portfolio)
        return torch.cat([price_h, context_h, portfolio_h], dim=-1)

    def forward(self, obs, *, zero_context: bool = False, zero_price: bool = False):
        torch = self._torch
        features = self.trunk_features(obs, zero_context=zero_context, zero_price=zero_price)
        mean = self.policy_head(features)
        value = self.value_head(features).squeeze(-1)
        std = torch.exp(self.log_std).expand_as(mean)
        return mean, std, value

    def act(self, obs, *, deterministic: bool = False, zero_context: bool = False, zero_price: bool = False):
        torch = self._torch
        mean, std, value = self.forward(obs, zero_context=zero_context, zero_price=zero_price)
        if deterministic:
            action = mean
            log_prob = torch.zeros(obs.shape[0], device=obs.device)
        else:
            dist = torch.distributions.Normal(mean, std)
            raw = dist.rsample()
            log_prob = dist.log_prob(raw).sum(dim=-1)
            action = raw
        return action, log_prob, value

    def evaluate_actions(self, obs, actions, *, zero_context: bool = False, zero_price: bool = False):
        torch = self._torch
        mean, std, value = self.forward(obs, zero_context=zero_context, zero_price=zero_price)
        dist = torch.distributions.Normal(mean, std)
        log_prob = dist.log_prob(actions).sum(dim=-1)
        entropy = dist.entropy().sum(dim=-1)
        return log_prob, value, entropy


class ActorCriticModule:
    """Optimizer/checkpoint wrapper around SplitTrunkActorCritic."""

    def __init__(self, core: SplitTrunkActorCritic) -> None:
        self._core = core
        self.price_trunk = core.price_trunk
        self.context_trunk = core.context_trunk
        self.portfolio_trunk = core.portfolio_trunk
        self.policy_head = core.policy_head
        self.value_head = core.value_head
        self.log_std = core.log_std

    def parameters(self, recurse: bool = True):
        yield from self._core._module_parameters()

    def state_dict(self):
        return {
            "price_trunk": self.price_trunk.state_dict(),
            "context_trunk": self.context_trunk.state_dict(),
            "portfolio_trunk": self.portfolio_trunk.state_dict(),
            "policy_head": self.policy_head.state_dict(),
            "value_head": self.value_head.state_dict(),
            "log_std": self.log_std.detach().cpu(),
        }

    def load_state_dict(self, state_dict, strict: bool = True):
        self.price_trunk.load_state_dict(state_dict["price_trunk"])
        self.context_trunk.load_state_dict(state_dict["context_trunk"])
        self.portfolio_trunk.load_state_dict(state_dict["portfolio_trunk"])
        self.policy_head.load_state_dict(state_dict["policy_head"])
        self.value_head.load_state_dict(state_dict["value_head"])
        self.log_std.data.copy_(state_dict["log_std"])

    def act(self, obs, **kwargs):
        return self._core.act(obs, **kwargs)

    def evaluate_actions(self, obs, actions, **kwargs):
        return self._core.evaluate_actions(obs, actions, **kwargs)

    @property
    def core(self) -> SplitTrunkActorCritic:
        return self._core
