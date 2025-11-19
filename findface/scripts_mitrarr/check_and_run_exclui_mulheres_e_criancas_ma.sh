#!/bin/bash

# Comando que deseja verificar e executar se não estiver rodando
# CMD="/opt/findface/scripts_mitrarr/run-manual-upload.sh"
CMD="/opt/findface/scripts_mitrarr/run_exclui_mulheres_e_criancas_ma.sh"

# Usar pgrep e grep para verificar se o processo está em execução
if ! pgrep -f "$CMD" > /dev/null 2>&1; then
    echo "Processo não encontrado, iniciando..."
    # Executar o comando usando nohup para que continue executando mesmo se o terminal for fechado
    nohup $CMD > /opt/findface/scripts_mitrarr/exclui_mulheres_e_criancas_ma.out &
else
    echo "Processo já em execução."
fi

