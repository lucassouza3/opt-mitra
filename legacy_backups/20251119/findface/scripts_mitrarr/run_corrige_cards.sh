#!/bin/bash
export FINDFACE_URL=https://10.95.7.19
export FINDFACE_USER=leonardo.lad
export FINDFACE_PASSWORD=Macuxi2009

cd /opt/findface/ws-nist/
/opt/findface/ws-nist/venv/bin/python /opt/findface/ws-nist/corrige_cards.py
