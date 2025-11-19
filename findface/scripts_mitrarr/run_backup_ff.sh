#!/bin/bash

export FINDFACE_URL="https://10.95.7.19"
export FINDFACE_USER="s_mitra"
export FINDFACE_PASSWORD="#MitraRR@2021!"


cd /opt/findface/backup-nist-from-ff/

/opt/findface/backup-nist-from-ff/venv/bin/python /opt/findface/backup-nist-from-ff/backup_nists_ff2.py
