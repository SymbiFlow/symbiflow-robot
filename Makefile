env:
	virtualenv --python=python3 venv
	activate venv/bin/activate; pip install -r requirements.txt

run:
	activate venv/bin/activate; python github_robot.py
