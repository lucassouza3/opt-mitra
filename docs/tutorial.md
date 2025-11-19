# Tutorial MITRARR (Reescrita)

## Visão Geral
O MITRARR reescrito centraliza ingestão de NISTs, agendamento e monitoramento em torno do scheduler (`run-schedule`), comandos da CLI e serviços de apoio (API, alertas). Todos os passos abaixo assumem que você está em servidores Linux acessados via MobaXterm, com TDD obrigatório e logs centralizados.

## 1. Preparar Ambiente
1. Conecte via MobaXterm (`ssh findface@servidor`).
2. Ative a venv do projeto novo:
   ```bash
   cd /opt/findface/mitrarr_clean
   source .venv/bin/activate
   ```
3. Liste os comandos disponíveis:
   ```bash
   python -m infra.cli.main --help
   ```

## 2. Operações Diárias
- **Registrar NIST**:
  ```bash
  python -m infra.cli.main register-nist --id 2025001 --source DETRAN --file /dados/arquivo.nst
  ```
- **Enviar ao FindFace**:
  ```bash
  python -m infra.cli.main send-to-findface --batch-size 50
  ```
- **Scheduler**:
  ```bash
  python -m infra.cli.main run-schedule --config /opt/findface/configs/prod_schedule.json
  ```
- **Pausar job via API**:
  ```bash
  curl -X POST http://localhost:8000/jobs/job_a/pause
  ```

## 3. Monitoramento
1. **Volume**:
   ```bash
   python -m infra.cli.main check-volume --history /opt/findface/configs/volumes.json --label adiciona_nists --current 120
   ```
2. **Heartbeats**:
   - Cron sugerido: `*/30 * * * * python -m infra.cli.main run-schedule --config /opt/findface/configs/guardian.json`
3. **Alertas**:
   ```bash
   python -m infra.cli.main emit-alert --type manual --job job_a --severity warning --message "Verificar volume"
   ```

## 4. Troubleshooting
- **Reiniciar scheduler/cron**:
  ```bash
  sudo systemctl restart cron
  ```
- **Filas congestionadas**:
  1. Pause job (`scheduler-cli pause job_a`).
  2. Limpe diretórios temporários ou registros travados.
  3. Retome (`scheduler-cli resume job_a`).
- **Volumes abaixo do esperado**: rode `check-volume` e, se necessário, `emit-alert`.

## 5. Logs / Contatos
- Logs principais: `/opt/findface/mitrarr_clean/logs`.
- Alertas registrados em `/opt/findface/mitrarr_clean/logs/alerts.log`.
- Para dúvidas de dados sensíveis, consulte o responsável pela operação de inteligência ou o DPO.
