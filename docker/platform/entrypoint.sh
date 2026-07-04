#!/bin/sh
set -e

case "$1" in
  downloader)
    exec python -m services.downloader.main
    ;;
  importer)
    exec python -m services.importer.main
    ;;
  train)
    exec quant-train train \
      --config "${TRAIN_CONFIG:-/config/training/smoke.yaml}" \
      --app-config "${CONFIG_PATH:-/config/config.yaml}" \
      --checkpoint-dir "${CHECKPOINT_DIR:-/app/data/checkpoints}" \
      --steps "${TRAIN_STEPS:-128}"
    ;;
  shell)
    exec /bin/sh
    ;;
  help|*)
    echo "Usage: entrypoint.sh {downloader|importer|train|shell|help}"
    echo "  TRAIN_CONFIG   default /config/training/smoke.yaml"
    echo "  TRAIN_STEPS    default 128"
    echo "  CHECKPOINT_DIR default /app/data/checkpoints"
    exit 0
    ;;
esac
