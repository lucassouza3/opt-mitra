import paramiko
import os
from pathlib import Path
import stat
from datetime import datetime

# Configurações de conexão SSH
hostname = 'sdf0990.pf.gov.br'
port = 22
username = 'leonardo.lad'

# Caminhos dos diretórios
remote_base_dir = '/mnt/mitra/nists/pf/sismigra/'
local_base_dir = '/mnt/mitra/nists/pf/sismigra/'

def sync_directories(sftp, remote_dir, local_dir):
    # Cria o diretório local se não existir
    Path(local_dir).mkdir(parents=True, exist_ok=True)

    # Lista os arquivos do diretório remoto
    remote_files = sftp.listdir(remote_dir)

    for remote_file in remote_files:
        remote_file_path = f"{remote_dir}/{remote_file}"
        local_file_path = os.path.join(local_dir, remote_file)

        if is_directory(sftp, remote_file_path):
            # Se for um diretório, chama a função recursivamente
            sync_directories(sftp, remote_file_path, local_file_path)
        else:
            # Se for um arquivo, copia se não existir ou se for diferente
            if not os.path.exists(local_file_path):
                print(f"Copiando {remote_file_path} para {local_file_path}")
                sftp.get(remote_file_path, local_file_path)

def is_directory(sftp, path):
    try:
        return stat.S_ISDIR(sftp.stat(path).st_mode)
    except IOError:
        return False

def get_latest_local_directory():
    """Retorna o subdiretório de data mais recente no diretório local."""
    dirs = [d for d in os.listdir(local_base_dir) if os.path.isdir(os.path.join(local_base_dir, d))]
    if not dirs:
        return None
    latest_dir = max(dirs, key=lambda d: datetime.strptime(d, '%Y%m%d'))
    return latest_dir

def main():
    # Carrega as chaves SSH padrão do usuário (normalmente ~/.ssh/id_rsa ou ~/.ssh/id_dsa)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # Estabelece a conexão SSH usando a chave privada
    ssh.connect(hostname, port=port, username=username)

    sftp = ssh.open_sftp()

    # Lista os subdiretórios do diretório remoto
    remote_dirs = sftp.listdir(remote_base_dir)

    # Obtém o diretório de data mais recente no local
    latest_local_dir = get_latest_local_directory()

    for remote_dir in remote_dirs:
        remote_dir_path = os.path.join(remote_base_dir, remote_dir)
        local_dir_path = os.path.join(local_base_dir, remote_dir)
        
        if is_directory(sftp, remote_dir_path):
            # Verifica se o diretório local já existe
            if not os.path.exists(local_dir_path) or remote_dir == latest_local_dir:
                print(f"Sincronizando diretório {remote_dir} para {local_dir_path}")
                sync_directories(sftp, remote_dir_path, local_dir_path)
            else:
                print(f"Diretório {local_dir_path} já existe localmente, ignorando.")

    sftp.close()
    ssh.close()

if __name__ == '__main__':
    main()
