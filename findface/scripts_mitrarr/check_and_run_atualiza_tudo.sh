#!/bin/bash

# Comando que deseja verificar e executar se não estiver rodando
CMD="/opt/findface/scripts_mitrarr/run_adiciona_nists.sh"
echo "Executando $CMD"

# Usar pgrep e grep para verificar se o processo está em execução
if ! pgrep -f "$CMD" > /dev/null 2>&1; then
    echo "Processo não encontrado, iniciando..."
    # Executar o comando usando nohup para que continue executando mesmo se o terminal for fechado
    nohup $CMD > /opt/findface/scripts_mitrarr/adiciona_nists.out &
else
    echo "Processo já em execução."
fi

# Comando que deseja verificar e executar se não estiver rodando
CMD="/opt/findface/scripts_mitrarr/check_and_run_relcionamentos.sh"
echo "Executando $CMD"

# Usar pgrep e grep para verificar se o processo está em execução
if ! pgrep -f "$CMD" > /dev/null 2>&1; then
    echo "Processo não encontrado, iniciando..."
    # Executar o comando usando nohup para que continue executando mesmo se o terminal for fechado
    nohup $CMD > /opt/findface/scripts_mitrarr/relacionamentos.out &
else
    echo "Processo já em execução."
fi


# Comando que deseja verificar e executar se não estiver rodando
CMD="/opt/findface/scripts_mitrarr/check_and_run_envia_nists_para_findface.sh"
echo "Executando $CMD"

# Usar pgrep e grep para verificar se o processo está em execução
if ! pgrep -f "$CMD" > /dev/null 2>&1; then
    echo "Processo não encontrado, iniciando..."
    # Executar o comando usando nohup para que continue executando mesmo se o terminal for fechado
    nohup $CMD > /opt/findface/scripts_mitrarr/envia_nists_para_findface.out &
else
    echo "Processo já em execução."
fi
