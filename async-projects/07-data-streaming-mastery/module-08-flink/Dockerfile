# Flink 2.2.1 with the connector JARs used in this module.
# The same image runs the JobManager, the TaskManager and the SQL client,
# so every Flink process can load the Kafka and MySQL CDC connectors.
FROM flink:2.2.1-scala_2.12-java17

ARG MAVEN=https://repo1.maven.org/maven2/org/apache/flink
ADD --chown=flink:flink --chmod=644 ${MAVEN}/flink-sql-connector-kafka/5.0.0-2.2/flink-sql-connector-kafka-5.0.0-2.2.jar /opt/flink/lib/
ADD --chown=flink:flink --chmod=644 ${MAVEN}/flink-sql-connector-mysql-cdc/3.7.0-2.2/flink-sql-connector-mysql-cdc-3.7.0-2.2.jar /opt/flink/lib/
# The CDC connector does not include the MySQL JDBC driver. Add it.
ADD --chown=flink:flink --chmod=644 https://repo1.maven.org/maven2/com/mysql/mysql-connector-j/9.7.0/mysql-connector-j-9.7.0.jar /opt/flink/lib/
