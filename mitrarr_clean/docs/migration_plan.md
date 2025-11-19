# Fase 5 – Migração / Go-Live

## Pré-requisitos
1. Confirmar backups recentes em `legacy_backups/<data>/`.
2. Garantir que o `run-schedule` está configurado para todos os jobs (`configs/*.json`).
3. Cron antigo (`check_and_run_*`) deve estar documentado para comparação.

## Passos de migração
1. **Parar cron antigo**: comentar/pausar todas as entradas `check_and_run_*`.
2. **Aplicar config do scheduler**: copiar os arquivos JSON para `/opt/findface/configs/` e validar via CLI:
   ```
   python -m infra.cli.main run-schedule --config /opt/findface/configs/prod_schedule.json --dry-run
   ```
3. **Atualizar crontab**: substituir linhas antigas por chamadas ao novo scheduler (exemplo abaixo).
4. **Ativar monitoramento**: garantir que `cron_guardian` e `emit-alert` estejam agendados.
5. **Alerta de go-live**: registrar via `emit-alert` o início da nova rotina.

## Validações Pós-Deploy
1. Executar `python -m infra.cli.main run-schedule --config ...` manualmente e checar logs/outputs.
2. Monitorar `logs/alerts.log` por 24h para verificar ausência de erros críticos.
3. Conferir a API (`/jobs` + pause/resume) para garantir que o store esteja funcional.

## Rollback
1. Reverter o crontab para as entradas `check_and_run_*`.
2. Pausar `run-schedule` e reativar o legado até análise final.
3. Restaurar arquivos de configuração a partir de `legacy_backups`.

## Modelo de Crontab
```
# Midnight runs
00 00 * * * python -m infra.cli.main run-schedule --config /opt/findface/configs/prod_midnight.json
# Monitoramento
*/5 * * * * python -m infra.cli.main check-volume --history /opt/findface/configs/volumes.json --label adiciona_nists --current $(python get_volume.py)
0 * * * * python -m infra.cli.main emit-alert --type heartbeat --job scheduler --severity info --message "scheduler ok"
```
