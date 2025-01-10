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
	rm -r README_files
	$(PYTHON) -m nbconvert --to markdown README.ipynb --output README.md --TagRemovePreprocessor.enabled=True --TagRemovePreprocessor.remove_cell_tags remove_cell

clean:
	find . -type d -name '__pycache__' -exec rm -rf {} +
	find . -type d -name '*.egg-info' -exec rm -rf {} +
	find . -type d -name '*.pytest_cache' -exec rm -rf {} +
	rm -rf .mypy_cache .pytest_cache

clean-data:
	rm -r .data

# Format code and docstrings
format:
	poetry run black .
	poetry run docformatter -r --in-place .

# Lint to check if code follows formatting standards
lint:
	poetry run black --check .
	poetry run docformatter -r --check .
	poetry run ruff check .
