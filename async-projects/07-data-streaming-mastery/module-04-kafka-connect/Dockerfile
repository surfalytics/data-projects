FROM confluentinc/cp-kafka-connect:7.5.0

# JDBC connector from Confluent Hub.
RUN confluent-hub install --no-prompt confluentinc/kafka-connect-jdbc:10.7.4

# The JDBC connector does NOT include a MySQL driver. Add it to the connector's lib folder.
# Source: https://docs.confluent.io/kafka-connectors/jdbc/current/jdbc-drivers.html
RUN curl -fsSL -o /usr/share/confluent-hub-components/confluentinc-kafka-connect-jdbc/lib/mysql-connector-j-8.0.33.jar \
    https://repo1.maven.org/maven2/com/mysql/mysql-connector-j/8.0.33/mysql-connector-j-8.0.33.jar

# FileStreamSource and FileStreamSink are bundled with Kafka (connect-file jar).
# They are not on Confluent Hub, so we do not install them.

# Create directory for file connector demo
RUN mkdir -p /tmp/connect-demo

ENV CONNECT_PLUGIN_PATH="/usr/share/java,/usr/share/confluent-hub-components"
