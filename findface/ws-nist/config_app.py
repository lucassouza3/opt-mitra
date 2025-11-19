import os
from pathlib import Path


# Oracle
ORACLE_USER = os.environ["ORACLE_USER"]
ORACLE_PASSWORD = os.environ["ORACLE_PASSWORD"]
ORACLE_DSN = os.environ["ORACLE_DSN"]

# "dsn": "eccpxv1102-scan.pf.gov.br/PDBDPF05P.pf.gov.br"

# PostgreSQL connection string without password
PG_USER = os.environ["PG_USER"]
PG_PASSWORD = os.environ["PG_PASSWORD"]
PG_HOST = os.environ["PG_HOST"]

# FINDFACE
FINDFACE_USER = os.environ["FINDFACE_USER"]
FINDFACE_PASSWORD = os.environ["FINDFACE_PASSWORD"]

# Caminhos padrão
APP_DIR = Path(__file__).parent
NIST_DIR = str(APP_DIR / "nists")