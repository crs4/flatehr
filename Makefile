INSTALL_STAMP := .install.stamp


.PHONY: install
install: $(INSTALL_STAMP)

$(INSTALL_STAMP): poetry.lock
	poetry install
	touch $(INSTALL_STAMP)

.PHONY: test
test: $(INSTALL_STAMP)
	poetry run pytest tests
	tests/test_cli.sh

.PHONY: clean
clean:
	rm -rf $(INSTALL_STAMP)
