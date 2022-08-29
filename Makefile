INSTALL_STAMP := .install.stamp
TEST_STAMP := .test.stamp


.PHONY: install
install: $(INSTALL_STAMP)

$(INSTALL_STAMP): poetry.lock
	poetry install
	touch $(INSTALL_STAMP)

.PHONY: test
test: $(TEST_STAMP) 

$(TEST_STAMP): $(INSTALL_STAMP) tests flatehr
	poetry run pytest --junitxml=reports/junit/junit.xml tests
	poetry run tests/test_cli.sh
	touch $(TEST_STAMP)

.PHONY: badges
badges: reports/tests-badge.svg

reports/tests-badge.svg: $(TEST_STAMP)
	genbadge tests -o reports/tests-badge.svg

.PHONY: clean
clean:
	rm -rf $(INSTALL_STAMP)
	rm -rf $(TEST_STAMP)
	rm -rf reports

.PHONY: coverage
coverage:
	coverage run --source=flatehr/ -m pytest
	coverage report

