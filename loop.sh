#!/bin/bash

set -x
set -e

while true; do
	make update
	make run
	sleep 30
done
