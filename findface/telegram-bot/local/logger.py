import logging
import os
from pathlib import Path
import sys

# Obtém o nome do módulo __main__ para usá-lo como nome do arquivo de log
# parent_module = sys.modules['.'.join(__name__.split('.')[:-1]) or '__main__']
# parent_name = str(parent_module).split('\\')[-1].split(".")[0]

## Adaptado para suporte linux e Windows
# Por: Leonardo Dias
running_module = sys.modules['__main__']
module_path = str(running_module).split(' from ')[-1].replace('>', '').replace("'", '')
module_name = Path(module_path).stem
module_dir = Path(Path(module_path).parent)

log_filename = module_name + '.log'

# Logfile
logFile = module_dir / log_filename

# Configuração do Logger
date_format = '%Y.%m.%d %H:%M:%S'
text_format = '%(asctime)s [%(module)s] %(message)s'
console_text_format = '[%(module)s] %(message)s'
log_formatter = logging.Formatter(text_format, datefmt=date_format)
console_formatter = logging.Formatter(console_text_format, datefmt=date_format)
# console_formatter = logging.Formatter(console_text_format, datefmt=date_format)

# Configuração do debug logger
# debug_log_file = "Debug_DiariosOficiais.log"

# Setup File handler
file_handler = logging.FileHandler(str(logFile))
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.INFO)

# Setup Stream Handler (i.e. console)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(console_formatter)
stream_handler.setLevel(logging.INFO)

# Setup Debug File handler
#debug_handler = logging.FileHandler(debug_log_file, mode='w')
#debug_handler.setFormatter(log_formatter)
#debug_handler.setLevel(logging.DEBUG)

# This code will remove all handlers in logging.root.handlers. You must call this code before logging.basicConfig()
# for handler in logging.root.handlers[:]:
#     logging.root.removeHandler(handler)
#     print('Removeu o handler do root')

# Get our logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Add both Handlers
logger.addHandler(file_handler)
logger.addHandler(stream_handler)


if __name__ == '__main__':
    pass