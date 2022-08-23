install:
	poetry install

test: install
	poetry run pytest tests
