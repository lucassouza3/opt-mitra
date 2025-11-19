#!/bin/bash

# Comando que deseja verificar e executar se não estiver rodando
# CMD="/opt/findface/scripts_mitrarr/run-manual-upload.sh"
# Caminho do script que queremos manter rodando
CMD="/opt/findface/scripts_mitrarr/run_agendador.sh"

# Caminho do arquivo de log
LOG="/opt/findface/scripts_mitrarr/agendador.out"

# Usar pgrep e grep para verificar se o processo está em execução
if ! pgrep -f "$CMD" > /dev/null 2>&1; then
    echo "$(date '+%F %T') - Agendador não encontrado. Iniciando..." >> "$LOG"
    # Executar o comando usando nohup para que continue executando mesmo se o terminal for fechado
    nohup $CMD >> "$LOG" 2>&1 &
else
    echo "$(date '+%F %T') - Agendador já está em execução." >> "$LOG"
fi
