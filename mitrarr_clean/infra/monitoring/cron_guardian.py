"""Verifica se os heartbeats estão atualizados e alerta jobs atrasados."""

from __future__ import annotations

import argparse
import sys
from datetime import timedelta
from pathlib import Path

from infra.container import get_data_dir
from infra.monitoring import HeartbeatMonitor


def build_parser() -> argparse.ArgumentParser:
    """Cria o parser para a execução em linha de comando."""
    parser = argparse.ArgumentParser(description="Verifica se existe job parado há mais de X dias.")
    parser.add_argument(
        "--threshold-days",
        type=int,
        default=7,
        help="Número de dias máximos sem receber heartbeat antes de alertar.",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Diretório base dos dados (por padrão usa MITRARR_DATA_DIR).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada para execução via cron."""
    parser = build_parser()
    args = parser.parse_args(argv)
    threshold = timedelta(days=args.threshold_days)
    base_dir = args.data_dir or get_data_dir()
    monitor_path = Path(base_dir) / "monitoring" / "heartbeats.json"

    monitor = HeartbeatMonitor(monitor_path)
    stale = monitor.get_stale_jobs(threshold)

    if stale:
        for job in stale:
            print(f"ALERTA: job '{job}' está sem execução há mais de {args.threshold_days} dias.")
        return 1

    print("Todos os jobs reportaram heartbeats dentro do prazo.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
