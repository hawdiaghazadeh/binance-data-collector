"""RL environment bridge — episode bars + execution + obs + reward (G33)."""

from __future__ import annotations

from typing import Any

from quant_platform.rl_product.env.execution import SimpleExecutionModel
from quant_platform.rl_product.env.portfolio import PortfolioTracker
from quant_platform.rl_product.env.protocols import ExecutionModelProtocol
from quant_platform.rl_product.graph import RLProductGraph
from quant_platform.rl_product.observation.vector import ObservationVector
from quant_platform.rl_product.protocols import Episode, EpisodeCursor
from services.shared.models import KlineRow


class RLEnvironmentBridge:
    """Connect episode cache, frozen graph phases, and portfolio simulation."""

    __slots__ = (
        "_episode",
        "_bars",
        "_cursor",
        "_graph",
        "_execution",
        "_portfolio",
        "_market",
        "_config",
        "_initial_equity",
        "_leverage",
    )

    def __init__(
        self,
        episode: Episode,
        graph: RLProductGraph,
        execution: ExecutionModelProtocol | None = None,
        *,
        market: str = "spot",
        initial_equity: float = 10_000.0,
        leverage: float = 5.0,
        config: dict[str, Any] | None = None,
    ) -> None:
        if market not in {"spot", "futures"}:
            raise ValueError("market must be spot or futures")
        self._episode = episode
        self._bars = tuple(episode.bars)
        self._graph = graph
        self._execution = execution or SimpleExecutionModel()
        self._market = market
        self._config = config or graph.config
        self._initial_equity = initial_equity
        self._leverage = leverage if market == "futures" else 1.0
        self._cursor = EpisodeCursor(self._bars, start=0)
        self._portfolio = PortfolioTracker.initial(
            market=market,
            initial_equity=initial_equity,
            leverage=self._leverage,
        )

    @property
    def episode(self) -> Episode:
        return self._episode

    @property
    def graph(self) -> RLProductGraph:
        return self._graph

    @property
    def portfolio(self) -> PortfolioTracker:
        return self._portfolio

    @property
    def cursor(self) -> EpisodeCursor:
        return self._cursor

    @property
    def market(self) -> str:
        return self._market

    def reset(self) -> tuple[list[float], dict[str, Any]]:
        self._cursor.reset(start=0)
        self._portfolio = PortfolioTracker.initial(
            market=self._market,
            initial_equity=self._initial_equity,
            leverage=self._leverage,
        )
        obs = self._graph.build_observation(self._bars, 0, self._portfolio)
        return obs.to_list(), {"episode_id": self._episode.episode_id, "step": 0}

    def step(self, action: float) -> tuple[list[float], float, bool, dict[str, Any]]:
        t = self._cursor.t
        bar = self._cursor.current_bar()
        price = bar.close

        target_exposure = float(action)
        if self._market == "spot":
            target_exposure = max(0.0, min(1.0, target_exposure))
        else:
            target_exposure = max(-1.0, min(1.0, target_exposure))

        equity = self._portfolio.equity(price)
        fill = self._execution.simulate_fill(
            target_exposure=target_exposure,
            price=price,
            position=self._portfolio.position,
            equity=equity,
            bar_volume=bar.volume,
            market=self._market,
            leverage=self._leverage,
        )
        step_pnl = self._portfolio.apply_fill(fill, price)

        obs, hints = self._graph.run_phases(self._bars, t, self._portfolio, price=price)
        hint_conf = sum(env.value for env in hints.values()) / max(len(hints), 1)
        reward, components = self._graph.compute_reward(
            step_pnl=step_pnl,
            portfolio=self._portfolio,
            hint_conf=hint_conf,
        )

        done = self._cursor.is_done()
        if not done:
            self._cursor.advance()
        obs = self._graph.build_observation(
            self._bars,
            self._cursor.t,
            self._portfolio,
            price=self._bars[self._cursor.t].close,
        )

        info = {
            "episode_id": self._episode.episode_id,
            "step": self._cursor.t,
            "price": price,
            "fill_price": fill.fill_price,
            "fee": fill.fee,
            "spread_cost": fill.spread_cost,
            "slippage_cost": fill.slippage_cost,
            "step_pnl": step_pnl,
            "reward_components": components,
            "market": self._market,
        }
        return obs.to_list(), reward, done, info

    def build_observation_at(self, t: int) -> ObservationVector:
        bar = self._bars[t]
        return self._graph.build_observation(self._bars, t, self._portfolio, price=bar.close)
