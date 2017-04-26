#!/bin/sh

# This script will set the environments for running ansible_hosts.py

DIR="$( cd "$(dirname "$0")" ; pwd -P )"
source $DIR/../../../../.venv/bin/activate

$DIR/ansible_hosts.py "$@"
