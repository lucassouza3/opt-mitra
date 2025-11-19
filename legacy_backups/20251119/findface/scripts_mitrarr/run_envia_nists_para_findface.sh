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
/opt/findface/ws-nist/venv/bin/python /opt/findface/ws-nist/envia_para_findface.py
