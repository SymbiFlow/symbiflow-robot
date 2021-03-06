ORGANIZATION = SymbiFlow
export ORGANIZATION

SHELL=/bin/bash

env:
	virtualenv --python=python3 venv
	source venv/bin/activate; pip install -r requirements.txt

update:
	git pull

run:
	source venv/bin/activate; python robot_merge_if_green.py

maintain-repos:
	source venv/bin/activate; python maintain-repos.py
