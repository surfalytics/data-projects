FROM confluentinc/cp-kafka-connect:7.5.0

# Install connector plugins via Confluent Hub
RUN confluent-hub install --no-prompt confluentinc/kafka-connect-jdbc:10.7.4 && \
    confluent-hub install --no-prompt confluentinc/kafka-connect-filestream:0.1.0.0

# The FileStreamSource and FileStreamSink connectors are bundled with Kafka,
# but we install them explicitly to ensure they appear in the plugin path.

# Create directory for file connector demo
RUN mkdir -p /tmp/connect-demo

ENV CONNECT_PLUGIN_PATH="/usr/share/java,/usr/share/confluent-hub-components"
