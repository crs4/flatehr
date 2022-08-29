INSTALL_STAMP := .install.stamp
TEST_STAMP := .test.stamp
REPORTS := docs/reports


.PHONY: install
install: $(INSTALL_STAMP)

$(INSTALL_STAMP): poetry.lock
	poetry install
	touch $(INSTALL_STAMP)

.PHONY: test
test: $(TEST_STAMP) 

$(TEST_STAMP): $(INSTALL_STAMP) tests flatehr
	poetry run pytest --junitxml=$(REPORTS)/junit/junit.xml tests
	poetry run tests/test_cli.sh
	touch $(TEST_STAMP)

.PHONY: badges
badges: $(REPORTS)/tests-badge.svg $(REPORTS)/coverage-badge.svg $(REPORTS)/flake8-badge.svg

$(REPORTS)/tests-badge.svg: $(TEST_STAMP)
	genbadge tests -i $(REPORTS)/junit/junit.xml  -o $(REPORTS)/tests-badge.svg

$(REPORTS)/coverage-badge.svg: $(TEST_STAMP) coverage
	genbadge coverage -i $(REPORTS)/coverage/coverage.xml -o $(REPORTS)/coverage-badge.svg

$(REPORTS)/flake8-badge.svg: $(TEST_STAMP) docs/reports/flake8stats.txt
	genbadge flake8 -i docs/reports/flake8stats.txt -o $(REPORTS)/flake8-badge.svg

.PHONY: clean
clean:
	rm -rf $(INSTALL_STAMP)
	rm -rf $(TEST_STAMP)
	rm -rf $(REPORTS)

.PHONY: coverage
coverage: $(REPORTS)/coverage.xml

$(REPORTS)/coverage.xml:
	coverage run --source=flatehr/ -m pytest
	coverage report
	coverage xml -o $(REPORTS)/coverage/coverage.xml

docs/reports/flake8stats.txt:
	flake8 flatehr/ --exit-zero  --statistics --tee --output-file $(REPORTS)/flake8stats.txt
