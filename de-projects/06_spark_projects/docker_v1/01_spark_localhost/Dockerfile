# Use the official Apache Spark image as a base
FROM python:3.11.7-bullseye

# Install dependencies, including OpenJDK 11
RUN apt-get update && \
    apt-get install -y openjdk-11-jdk-headless

# Set JAVA_HOME environment variable.
# The JDK folder name depends on the CPU (arm64 or amd64), so link it to a fixed path.
RUN ln -s /usr/lib/jvm/java-11-openjdk-$(dpkg --print-architecture) /usr/lib/jvm/java-11
ENV JAVA_HOME=/usr/lib/jvm/java-11
ENV PATH=$JAVA_HOME/bin:$PATH

# Ensure that Python is installed and upgrade pip
RUN apt-get install -y python3 python3-pip && \
    python3 -m pip install --upgrade pip

# Set up a default volume mount point
VOLUME ["/opt/spark_projects"]

# Copy the contents of the host directory into the Docker container
COPY . .

# Install PySpark
RUN pip install pyspark

# Start PySpark when the container runs
CMD ["pyspark"]
