FROM confluentinc/cp-kafka-connect:8.4.1

# JDBC sink connector (also has the PostgreSQL driver) from Confluent Hub.
RUN confluent-hub install --no-prompt confluentinc/kafka-connect-jdbc:10.9.10

# Debezium MySQL source connector 3.7.1.Final from Maven Central.
# Confluent Hub only has Debezium 3.2.x, so we download the plugin archive.
# The image has no curl or tar, so python3 downloads and unpacks the archive.
RUN python3 -c "import urllib.request, tarfile, io; \
url = 'https://repo1.maven.org/maven2/io/debezium/debezium-connector-mysql/3.7.1.Final/debezium-connector-mysql-3.7.1.Final-plugin.tar.gz'; \
tarfile.open(fileobj=io.BytesIO(urllib.request.urlopen(url).read()), mode='r:gz').extractall('/usr/share/confluent-hub-components')"

ENV CONNECT_PLUGIN_PATH="/usr/share/java,/usr/share/confluent-hub-components"
