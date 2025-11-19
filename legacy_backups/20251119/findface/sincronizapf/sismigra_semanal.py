import paramiko
import os
from pathlib import Path

# Configurações de conexão SSH
hostname = 'sdf0990.pf.gov.br'
port = 22
username = 'leonardo.lad'

# Caminhos dos diretórios
remote_base_dir = '/mnt/mitra/nists/pf/sismigra/'
local_base_dir = '/mnt/mitra/nists/pf/sismigra/'

def copy_nst_files(sftp, remote_dir, local_dir):
    # Cria o diretório local se não existir
    Path(local_dir).mkdir(parents=True, exist_ok=True)

    # Lista os itens do diretório remoto
    remote_items = sftp.listdir(remote_dir)

    for item in remote_items:
        remote_item_path = f"{remote_dir}/{item}"
        local_item_path = os.path.join(local_dir, item)

        if is_directory(sftp, remote_item_path):
            # Se for um diretório, chama a função recursivamente
            copy_nst_files(sftp, remote_item_path, local_item_path)
        elif item.endswith('.nst'):
            # Se for um arquivo com extensão .nst e não existir localmente, copia
            if not os.path.exists(local_item_path):
                print(f"Copiando {remote_item_path} para {local_item_path}")
                sftp.get(remote_item_path, local_item_path)

def is_directory(sftp, path):
    try:
        return stat.S_ISDIR(sftp.stat(path).st_mode)
    except IOError:
        return False

def main():
    # Carrega as chaves SSH padrão do usuário (normalmente ~/.ssh/id_rsa ou ~/.ssh/id_dsa)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # Estabelece a conexão SSH usando a chave privada
    ssh.connect(hostname, port=port, username=username)

    sftp = ssh.open_sftp()

    # Começa a copiar os arquivos .nst do diretório remoto para o local
    copy_nst_files(sftp, remote_base_dir, local_base_dir)

    sftp.close()
    ssh.close()

if __name__ == '__main__':
    main()
