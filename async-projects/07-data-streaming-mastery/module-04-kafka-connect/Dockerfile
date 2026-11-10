FROM confluentinc/cp-kafka-connect:8.4.1

# The base image runs as a non-root user. Switch to root to install plugins.
USER root

# JDBC connector from Confluent Hub.
RUN confluent-hub install --no-prompt --component-dir /usr/share/confluent-hub-components confluentinc/kafka-connect-jdbc:10.9.10

# The JDBC connector does NOT include a MySQL driver. Add it to the connector's lib folder.
# The image has no curl, so we use ADD to download from Maven Central.
# Source: https://docs.confluent.io/kafka-connectors/jdbc/current/jdbc-drivers.html
ADD --chmod=644 https://repo1.maven.org/maven2/com/mysql/mysql-connector-j/9.7.0/mysql-connector-j-9.7.0.jar \
    /usr/share/confluent-hub-components/confluentinc-kafka-connect-jdbc/lib/mysql-connector-j-9.7.0.jar

# FileStreamSource and FileStreamSink ship with Kafka (connect-file jar).
# In this image the jar is in /usr/share/filestream-connectors, which is added to the plugin path
# in docker-compose.yml (CONNECT_PLUGIN_PATH).

# Create directory for file connector demo
RUN mkdir -p /tmp/connect-demo && chmod 777 /tmp/connect-demo

USER appuser
