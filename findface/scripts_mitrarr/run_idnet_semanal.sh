#!/bin/bash

export http_proxy=http://proxy.dpf.gov.br:8080

cd /opt/findface/nist_downloader/

/opt/findface/nist_downloader/venv/bin/python /opt/findface/nist_downloader/idnet_semanal.py
