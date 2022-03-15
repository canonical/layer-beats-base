PYTHON_SCRIPTS = \
	./actions/* \
	./lib/elasticbeats.py \
	./reactive/beats_base.py \
	./unit_tests/*.py

all: unittest

.PHONY: clean
clean:
	@rm -f .coverage
	@rm -rf .tox
	@rm -f .unit-state.db
	@find . -name "*.pyc" -type f -exec rm -f '{}' \;
	@find . -name "__pycache__" -type d -prune -exec rm -rf '{}' \;

.PHONY: sysdeps
sysdeps:
	@which pip3 >/dev/null || (sudo apt-get install -y python3-pip)
	@which flake8 >/dev/null || (sudo pip3 install flake8)
	@which tox >/dev/null || (sudo pip3 install tox)

.PHONY: lint
lint: sysdeps
	@echo "Checking Python syntax..."
	@flake8 --max-complexity=10 --filename=\* --ignore=E501,E402 $(PYTHON_SCRIPTS)

.PHONY: unittest
unittest: sysdeps lint
	@echo "Running unit tests..."
	@tox
