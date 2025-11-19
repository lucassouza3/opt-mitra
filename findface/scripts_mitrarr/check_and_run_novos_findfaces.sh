#!/bin/bash

# Comando que deseja verificar e executar se não estiver rodando
CMD="/opt/findface/scripts_mitrarr/run_novos_findfaces.sh"

# Usar pgrep e grep para verificar se o processo está em execução
if ! pgrep -f "$CMD" > /dev/null 2>&1; then
    echo "Processo não encontrado, iniciando..."
    # Executar o comando usando nohup para que continue executando mesmo se o terminal for fechado
    nohup $CMD > /opt/findface/scripts_mitrarr/novos_findfaces.out &
else
    echo "Processo já em execução."
fi

