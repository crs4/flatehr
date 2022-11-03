INSTALL_STAMP := .install.stamp
TEST_STAMP := .test.stamp
REPORTS := docs/reports
DOCKER_STAMP := .docker_stamp
DOCKER_CONTEXT := docker/.docker-context


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

$(REPORTS)/coverage-badge.svg: $(TEST_STAMP) $(REPORTS)/coverage/coverage.xml
	genbadge coverage -i $(REPORTS)/coverage/coverage.xml -o $(REPORTS)/coverage-badge.svg

$(REPORTS)/flake8-badge.svg: $(TEST_STAMP) docs/reports/flake8stats.txt
	genbadge flake8 -i docs/reports/flake8stats.txt -o $(REPORTS)/flake8-badge.svg

.PHONY: clean
clean:
	rm -rf $(INSTALL_STAMP)
	rm -rf $(TEST_STAMP)
	rm -rf $(REPORTS)
	rm -rf $(DOCKER_STAMP)
	rm -rf $(DOCKER_CONTEXT)

.PHONY: coverage
coverage: $(REPORTS)/coverage.xml

$(REPORTS)/coverage/coverage.xml:
	coverage run --source=flatehr/ -m pytest
	coverage report
	coverage xml -o $(REPORTS)/coverage/coverage.xml

docs/reports/flake8stats.txt:
	flake8 flatehr/ --exit-zero  --statistics --tee --output-file $(REPORTS)/flake8stats.txt

$(DOCKER_STAMP): flatehr poetry.lock docker/Dockerfile
	mkdir -p $(DOCKER_CONTEXT)
	cp -r flatehr  docker/.docker-context
	cp poetry.lock docker/.docker-context
	cp pyproject.toml docker/.docker-context
	cp README.md docker/.docker-context
	$(eval version=$(shell semantic-release print-version))
	docker build -f docker/Dockerfile docker/.docker-context -t flatehr:$(version)
	docker tag flatehr:$(version) flatehr
	touch $(DOCKER_STAMP)

.PHONY: docker
docker: $(DOCKER_STAMP)

.PHONY: docker-test tests/test_docker.sh
docker-test: docker
	tests/test_docker.sh


.PHONY: docker-push
docker-push: docker-test
	docker tag flatehr:$(shell poetry run flatehr --version) crs4/flatehr:$(shell poetry run flatehr --version)
	docker tag flatehr crs4/flatehr
	docker push crs4/flatehr:$(shell poetry run flatehr --version)
	docker push crs4/flatehr
