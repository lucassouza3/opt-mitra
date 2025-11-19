#!/bin/bash

# Verificar se o compartilhamento NFS já está montado
if ! mountpoint -q /mnt/mitra_temp; then
    echo "Montando o compartilhamento NFS em /mnt/mitra_temp"
    mount -t nfs 10.95.4.61:/volume1/findface2 /mnt/mitra_temp
    if [ $? -ne 0 ]; then
        echo "Falha ao montar o compartilhamento NFS em /mnt/mitra_temp"
        exit 1
    fi
else
    echo "O compartilhamento NFS já está montado em /mnt/mitra_temp"
fi

# Montar com bindfs
echo "Montando com bindfs /mnt/mitra"
bindfs -o perms=0700,mirror-only=findface,nonempty /mnt/mitra_temp /mnt/mitra
if [ $? -ne 0 ]; then
    echo "Falha ao montar com bindfs /mnt/mitra"
    exit 1
fi

echo "Montagem concluída com sucesso"
