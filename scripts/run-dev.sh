#!/bin/bash
set -e
cd "$(dirname "$0")/.."
source .venv/bin/activate
python src/parin_pdf_viewer.py
