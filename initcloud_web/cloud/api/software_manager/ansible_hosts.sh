#!/bin/sh

DIR="$( cd "$(dirname "$0")" ; pwd -P )"
source $DIR/../../../../.venv/bin/activate

$DIR/ansible_hosts.py "$@"
