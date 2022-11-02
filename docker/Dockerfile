FROM python:3.8

ENV DEBIAN_FRONTEND=noniteractive
ENV FLATEHR_HOME=/opt/flatehr/
WORKDIR ${FLATEHR_HOME}
RUN pip install poetry==1.2.0
COPY poetry.lock pyproject.toml README.md  ${FLATEHR_HOME}
COPY flatehr ${FLATEHR_HOME}/flatehr
RUN poetry config virtualenvs.create false &&  poetry install

ENTRYPOINT ["/usr/local/bin/flatehr"]
