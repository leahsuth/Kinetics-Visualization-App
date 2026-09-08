#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"
podman run --rm \
  --replace \
  --name merck-kinetics \
  --publish 8501:8501 \
  localhost/merck-kinetics:latest \
  streamlit run main.py --server.address=0.0.0.0 --server.port=8501