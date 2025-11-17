#!/bin/bash
# Helper script to run the search agent graph

cd "$(dirname "$0")"
conda activate testing
export PYTHONPATH="${PWD}:${PYTHONPATH}"
python search_agent/graph.py "$@"

