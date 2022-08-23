INSTALL_STAMP := .install.stamp


.PHONY: install
install: $(INSTALL_STAMP)
$(INSTALL_STAMP): pyproject.toml poetry.lock
	poetry install
	touch $(INSTALL_STAMP)

.PHONY: test
test: install
	poetry run pytest tests

.PHONY: clean
clean:
	rm -rf $(INSTALL_STAMP)
