#!/bin/bash

# pytest + pytest-json-ctrf are baked into the environment image
# (environment/Dockerfile), so this installs nothing at verify time.
mkdir -p /logs/verifier
pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA
code=$?

if [ $code -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
