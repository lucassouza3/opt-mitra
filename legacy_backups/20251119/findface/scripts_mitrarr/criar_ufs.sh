#!/bin/bash

# Lista de siglas dos estados brasileiros
estados=("br" "pf" "ac" "al" "am" "ap" "ba" "ce" "df" "es" "go" "ma" "mg" "ms" "mt" "pa" "pb" "pe" "pi" "pr" "rj" "rn" "ro" "rr" "rs" "sc" "se" "sp" "to")

# Loop para criar diretórios
for estado in "${estados[@]}"
do
    mkdir -p "$estado"
    echo "Diretório $estado criado."
done

echo "Todos os diretórios foram criados."
