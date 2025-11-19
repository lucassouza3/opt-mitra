"""Interface de linha de comando para operar o MITRARR reescrito."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from core.entities import RelationshipRecord
from core.exceptions import UseCaseError
from core.use_cases import RegisterNistInput
from infra.auto_recovery import RetryRunner
from infra.container import build_container, get_data_dir
from infra.monitoring import VolumeValidator
from infra.scheduler import JobScheduler, SchedulerResult, load_schedule


def build_parser() -> argparse.ArgumentParser:
    """Cria o parser com todos os subcomandos suportados."""
    parser = argparse.ArgumentParser(
        description="Ferramenta de orquestração das rotinas MITRARR (versão clean)."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    register = subparsers.add_parser("register-nist", help="Registra um novo arquivo NIST.")
    register.add_argument("--id", required=True, help="Identificador único do arquivo.")
    register.add_argument("--source", required=True, help="Fonte de origem (ex.: DETRAN).")
    register.add_argument("--file", required=True, type=Path, help="Caminho completo do arquivo .nst.")
    register.add_argument(
        "--created-at",
        help="Data de criação em ISO 8601. Se omitido, utiliza o horário atual.",
    )

    send = subparsers.add_parser(
        "send-to-findface",
        help="Envia registros pendentes para o FindFace utilizando o gateway configurado.",
    )
    send.add_argument("--batch-size", type=int, default=50, help="Quantidade máxima por envio.")

    rels = subparsers.add_parser(
        "sync-relationships",
        help="Sincroniza relacionamentos fornecidos via arquivo JSON.",
    )
    rels.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Arquivo JSON contendo uma lista com person_id, related_person_id e relation_type.",
    )

    volume = subparsers.add_parser(
        "check-volume",
        help="Verifica volume processado de acordo com o histórico.",
    )
    volume.add_argument("--history", type=Path, required=True, help="Arquivo JSON com histórico.")
    volume.add_argument("--label", required=True, help="Identificador do job.")
    volume.add_argument("--current", type=int, required=True, help="Quantidade processada hoje.")
    volume.add_argument(
        "--ratio",
        type=float,
        default=0.5,
        help="Percentual mínimo aceito em relação ao último volume registrado.",
    )

    retry = subparsers.add_parser(
        "run-with-retry",
        help="Executa um comando com tentativas automáticas em caso de falha.",
    )
    retry.add_argument("--max-attempts", type=int, default=3)
    retry.add_argument("--delay", type=float, default=5.0)
    retry.add_argument("--label", required=True, help="Nome do job.")
    retry.add_argument("cmd", nargs=argparse.REMAINDER, help="Comando a ser executado.")

    run_schedule = subparsers.add_parser(
        "run-schedule",
        help="Executa o scheduler baseado em um arquivo de configuração JSON.",
    )
    run_schedule.add_argument("--config", type=Path, required=True, help="Arquivo JSON com os jobs.")

    return parser


def handle_register(container, args: argparse.Namespace) -> None:
    """Executa o fluxo de registro de NIST."""
    created_at = datetime.fromisoformat(args.created_at) if args.created_at else datetime.now(UTC)
    input_data = RegisterNistInput(
        identifier=args.id,
        source=args.source,
        path=args.file,
        created_at=created_at,
    )
    container.register_nist.execute(input_data)
    container.heartbeat_monitor.record("register-nist")
    print(f"NIST {args.id} registrado com sucesso.")


def handle_send(container, args: argparse.Namespace) -> None:
    """Envia registros pendentes ao FindFace."""
    count = container.send_to_findface.execute(args.batch_size)
    container.heartbeat_monitor.record("send-to-findface")
    print(f"{count} registro(s) enviados ao FindFace.")


def handle_relationships(container, args: argparse.Namespace) -> None:
    """Sincroniza relacionamentos a partir de um arquivo JSON."""
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    records = [
        RelationshipRecord(
            person_id=item["person_id"],
            related_person_id=item["related_person_id"],
            relation_type=item["relation_type"],
        )
        for item in payload
    ]
    synced = container.sync_relationships.execute(records)
    container.heartbeat_monitor.record("sync-relationships")
    print(f"{synced} relacionamento(s) sincronizado(s).")


def handle_volume_check(args: argparse.Namespace) -> int:
    """Executa o validador de volume e retorna código de status."""
    validator = VolumeValidator(history_path=args.history, min_ratio=args.ratio)
    alerts = validator.validate(current_count=args.current, label=args.label)
    if alerts:
        for alert in alerts:
            print(
                f"[ALERTA] Volume '{alert.label}' esperado ~{alert.expected}, atual={alert.current}",
                file=sys.stderr,
            )
        return 1
    print("Volume dentro dos limites esperados.")
    return 0


def handle_run_with_retry(args: argparse.Namespace) -> int:
    """Executa um comando arbitrário com tentativas automáticas."""
    cmd = list(args.cmd)
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]
    if not cmd:
        raise ValueError("Nenhum comando informado.")
    runner = RetryRunner(max_attempts=args.max_attempts, delay_seconds=args.delay)

    def task() -> None:
        result = subprocess.run(cmd, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"Comando retornou {result.returncode}")

    result = runner.run(task, label=args.label)
    return 0 if result.success else 1


def handle_run_schedule(args: argparse.Namespace) -> int:
    """Executa o agendador com base na configuração informada."""
    jobs = load_schedule(args.config)
    scheduler = JobScheduler()
    result = scheduler.run(jobs)
    if not jobs:
        print("Nenhum job definido na configuração.")
    if result.failures:
        print(f"Falha nos jobs: {', '.join(result.failures)}", file=sys.stderr)
    return 0 if result.success else 1


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada principal utilizado pelo CLI e pelos testes."""
    parser = build_parser()
    args = parser.parse_args(argv)
    data_dir = get_data_dir()
    container = build_container(data_dir)

    try:
        if args.command == "register-nist":
            handle_register(container, args)
        elif args.command == "send-to-findface":
            handle_send(container, args)
        elif args.command == "sync-relationships":
            handle_relationships(container, args)
        elif args.command == "check-volume":
            return handle_volume_check(args)
        elif args.command == "run-with-retry":
            return handle_run_with_retry(args)
        elif args.command == "run-schedule":
            return handle_run_schedule(args)
        else:  # pragma: no cover
            parser.error("Comando desconhecido.")
    except (UseCaseError, ValueError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
