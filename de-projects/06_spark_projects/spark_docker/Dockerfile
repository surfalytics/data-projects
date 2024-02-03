# Use the official Apache Spark image as a base
FROM python:3.11.7-bullseye

# Install dependencies
RUN apt-get update && \
    apt-get install -y openjdk-11-jdk-headless

# Set JAVA_HOME environment variable
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH

# Copy the contents of the host directory into the Docker container
COPY . .

# Copy the contents of the host directory into the Docker container
COPY . .

RUN pip install pyspark