# Tutorial MITRARR (Reescrita)

## Visão Geral
O novo MITRARR é composto pelo scheduler (`run-schedule`), casos de uso (`RegisterNist`, `SendToFindFace`, etc.), monitoramento (`cron_guardian`, `VolumeValidator`, `AlertDispatcher`) e uma API para pausar/resumir jobs. Todo fluxo roda em servidores Linux acessados via MobaXterm.

## Passo a Passo
1. **Preparar Ambiente**
   - Acesse via MobaXterm (`ssh findface@servidor`).
   - Ative a venv: `source /opt/findface/mitrarr_clean/.venv/bin/activate`.
   - Rode `python -m infra.cli.main help` para verificar comandos disponíveis.

2. **Registrar e enviar NISTs**
   ```
   python -m infra.cli.main register-nist --id TESTE --source DETRAN --file /caminho/arquivo.nst
   python -m infra.cli.main send-to-findface --batch-size 50
   ```

3. **Monitoramento**
   - `cron_guardian`: verifica heartbeats. Configurar no cron com `*/30 * * * * python -m infra.cli.main run-schedule --config /opt/findface/configs/guardian.json`.
   - `check-volume`: `python -m infra.cli.main check-volume --history /opt/findface/configs/volumes.json --label adiciona_nists --current 120`.
   - Alertas manuais: `python -m infra.cli.main emit-alert --type manual --job jobX --message "..."`.

4. **Scheduler**
   - Configurar JSONs em `/opt/findface/configs/*.json`.
   - Executar manualmente: `python -m infra.cli.main run-schedule --config /opt/findface/configs/prod.json`.
   - Pausar job pelo API: `POST /jobs/<nome>/pause`.

5. **Troubleshooting**
   - **Reiniciar**: `sudo systemctl restart cron`.
   - **Limpar filas**: `scheduler-cli pause job`, limpar diretório e `scheduler-cli resume`.
   - **Ver volume baixo**: usar `check-volume` e `emit-alert`.

## Contatos / Logs
- Logs em `/opt/findface/mitrarr_clean/logs`.
- Alertas: `/opt/findface/mitrarr_clean/logs/alerts.log`.
