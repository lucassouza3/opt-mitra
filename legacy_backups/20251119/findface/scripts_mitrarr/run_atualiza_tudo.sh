#!/bin/bash
export ORACLE_USER=S_MITRARR
export ORACLE_PASSWORD=S_MITRARR
export ORACLE_DSN=eccpxv1102-scan.pf.gov.br/PDBDPF05P.pf.gov.br
export PG_USER=postgres
export PG_PASSWORD=Mitra2021
export PG_HOST=localhost
export FINDFACE_USER=s_mitra
export FINDFACE_PASSWORD=#MitraRR@2021!

cd /opt/findface/ws-nist/

# run_rsync_sismigra.sh
# /opt/findface/nist_downloader/venv/bin/python /opt/findface/nist_downloader/idnet_diario_civil.py
# /opt/findface/nist_downloader/venv/bin/python /opt/findface/nist_downloader/detranrr_diario.py
/opt/findface/ws-nist/venv/bin/python /opt/findface/ws-nist/adiciona_nists.py
/opt/findface/ws-nist/venv/bin/python /opt/findface/ws-nist/adiciona_relacionamentos.py
/opt/findface/ws-nist/venv/bin/python /opt/findface/ws-nist/stimar.py
/opt/findface/ws-nist/venv/bin/python /opt/findface/ws-nist/envia_para_findface.py
