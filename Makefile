# Makefile

# Variables
PYTHON = poetry run python

.PHONY: help install data test docs clean clean-data format lint

help:
	@echo "Available commands:"
	@echo "  install    - Don't use for user installation! Install project dependencies. Will use poetry.lock file."
	@echo "  data       - Download additional data"
	@echo "  test       - Run tests"
	@echo "  docs       - Generate documentation (README)"
	@echo "  clean      - Clean up temporary files"
	@echo "  clean-data - Remove additional data"
	@echo "  format     - Autoformat code"
	@echo "  lint       - Check formatting and PEP8 compliance"
	@echo "  lint-fix   - Same like lint but auto applies fixes"

install:
	poetry install

data:
	mkdir .data
	cd .data && git clone https://github.com/openPMD/openPMD-example-datasets.git
	cd .data/openPMD-example-datasets && tar -zxvf example-2d.tar.gz
	cd .data/openPMD-example-datasets && tar -zxvf example-3d.tar.gz

test:
	poetry run pytest --nbmake README.ipynb

docs:
	rm -rf README_files
	$(PYTHON) -m nbconvert --to notebook --execute README.ipynb --output README.executed.ipynb
	$(PYTHON) -m nbconvert --to markdown README.executed.ipynb --output README.md --TagRemovePreprocessor.enabled=True --TagRemovePreprocessor.remove_cell_tags remove_cell
	rm -f README.executed.ipynb
clean:
	find . -type d -name '__pycache__' -exec rm -rf {} +
	find . -type d -name '*.egg-info' -exec rm -rf {} +
	find . -type d -name '*.pytest_cache' -exec rm -rf {} +
	rm -rf .mypy_cache .pytest_cache
	nb-clean clean README.ipynb

clean-data:
	rm -r .data

# Format code and docstrings
format:
	poetry run ruff format
# Lint to check if code follows formatting standards
lint:
	poetry run ruff check
lint-fix:
	poetry run ruff check --fix

pre-commit-install:
	pre-commit install
	pre-commit autoupdate
