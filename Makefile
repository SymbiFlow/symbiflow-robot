ORGANIZATION = SymbiFlow
export ORGANIZATION

env:
	virtualenv --python=python3 venv
	source venv/bin/activate; pip install -r requirements.txt

run:
	source venv/bin/activate; python github_robot.py
