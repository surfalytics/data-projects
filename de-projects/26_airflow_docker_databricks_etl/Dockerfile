# Airflow 3.0.3, Python 3.12
FROM apache/airflow:3.0.3-python3.12

USER root

# uv just for building wheel
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
  && rm -rf /var/lib/apt/lists/* \
  && curl -LsSf https://astral.sh/uv/install.sh | sh \
  && ln -s /root/.local/bin/uv /usr/local/bin/uv

# Put code in place
ENV PYTHONPATH=/opt/python:${PYTHONPATH}
COPY ./scripts /opt/python/scripts/
COPY ./airflow ${AIRFLOW_HOME}/

# Build & install wheel
WORKDIR /tmp/src
COPY . /tmp/src
RUN if [ -f pyproject.toml ]; then \
      uv build && python -m pip install --no-cache-dir dist/*.whl ; \
    else \
      echo "No pyproject.toml found; skipping wheel build."; \
    fi \
 && rm -rf /tmp/src

# Install runtime deps into the Airflow interpreter
RUN python -m pip install --no-cache-dir \
      databricks-connect==16.3.2 \
      munch==4.0.0 \
      apache-airflow-providers-databricks 

# permissions
RUN chown -R airflow:0 ${AIRFLOW_HOME} /opt/python && chmod -R g=u ${AIRFLOW_HOME} /opt/python

USER airflow
WORKDIR ${AIRFLOW_HOME}
