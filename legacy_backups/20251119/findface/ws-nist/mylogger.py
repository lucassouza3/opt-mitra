import logging
from logging.handlers import RotatingFileHandler


def configurar_logger(nome_arquivo: str) -> logging.Logger:
    """
    Configura um logger para registrar logs no console e em arquivos, com rotação quando o arquivo atinge 5MB.

    Parâmetros:
        nome_arquivo (str): Nome do arquivo onde os logs serão armazenados.

    Retorno:
        logging.Logger: Objeto Logger configurado.
    """
    if not isinstance(nome_arquivo, str):
        raise TypeError("O nome do arquivo deve ser uma string.")

    # Criando o logger
    logger = logging.getLogger("app_logger")
    logger.setLevel(logging.DEBUG)  # Define o nível mínimo de log

    # Criando formato do log
    formato_log = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    # Criando handler para o console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # Exibe INFO e acima no console
    console_handler.setFormatter(formato_log)

    # Criando handler para arquivo com rotação de logs
    file_handler = RotatingFileHandler(nome_arquivo, maxBytes=5_000_000, backupCount=3, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)  # Registra todos os logs no arquivo
    file_handler.setFormatter(formato_log)

    # Adicionando handlers ao logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger

# Exemplo de uso
if __name__ == "__main__":
    logger = configurar_logger("app.log")

    logger.debug("Este é um log de depuração (debug).")
    logger.info("A aplicação iniciou corretamente.")
    logger.warning("Atenção! Algo pode estar errado.")
    logger.error("Erro encontrado no processo.")
    logger.critical("Falha crítica! A aplicação pode falhar.")
