#!/bin/bash
set -e

# =============================================================================
# SSL certificate script for Kafka (demo only)
# =============================================================================
# DO NOT use these certificates in production. Use a trusted CA.
#
# Needs: openssl and keytool (keytool comes with any JDK).
#
# Creates in ./ssl:
#   ca-cert.pem, ca-key.pem          Certificate Authority (CA)
#   kafka.broker.keystore.p12        Broker private key + CA-signed certificate
#   kafka.broker.truststore.p12      CA certificate the broker trusts
#   kafka.client.keystore.p12        Client private key + certificate (for mutual TLS)
#   kafka.client.truststore.p12      CA certificate the client trusts
#   client-cert.pem, client-key.pem  Client certificate and key in PEM (for Python)
#   store-password                   The password of all stores (one line)
#
# Stores use the PKCS12 format (the default since Java 9). PKCS12 uses one
# password for the store and the key, so there is one password here.
#
# The broker certificate has a Subject Alternative Name (SAN) list. Clients check
# that the broker host name is in this list. In Kafka 4.x, hostname checking
# is on by default (ssl.endpoint.identification.algorithm=https).
# =============================================================================

# Always create ./ssl in the module folder, wherever you run the script from.
cd "$(dirname "${BASH_SOURCE[0]}")/.."
SSL_DIR="./ssl"
PASSWORD="changeit-demo"
VALIDITY_DAYS=365
SAN="DNS:kafka,DNS:localhost,IP:127.0.0.1"
DN_SUFFIX="OU=DataStreamingMastery,O=Demo,L=Local,ST=State,C=US"

echo "Kafka SSL certificate generation"

rm -rf "$SSL_DIR"
mkdir -p "$SSL_DIR"
cd "$SSL_DIR"

# --- Step 1: CA ---------------------------------------------------------------
echo "Step 1: create the CA"
openssl req -new -x509 -newkey rsa:2048 -nodes \
    -keyout ca-key.pem -out ca-cert.pem -days $VALIDITY_DAYS \
    -subj "/CN=KafkaDemoCA/OU=DataStreamingMastery/O=Demo/L=Local/ST=State/C=US"

# --- Steps 2 and 3: one keystore per identity -------------------------------
# For each identity (broker, client):
#   1. keytool creates a key pair in a keystore.
#   2. keytool makes a certificate signing request (CSR).
#   3. openssl signs the CSR with the CA key.
#   4. keytool imports the CA certificate and the signed certificate.
make_keystore() {
    local name="$1" cn="$2" san="$3"
    echo "Create the $name keystore (CN=$cn)"
    keytool -genkeypair -alias "$name" -keyalg RSA -keysize 2048 \
        -dname "CN=$cn,$DN_SUFFIX" -ext "san=$san" \
        -keystore "kafka.$name.keystore.p12" -storetype PKCS12 \
        -storepass "$PASSWORD" -validity $VALIDITY_DAYS
    keytool -certreq -alias "$name" -ext "san=$san" \
        -keystore "kafka.$name.keystore.p12" -storepass "$PASSWORD" \
        -file "$name.csr"
    # openssl does not copy the SAN from the CSR, so we pass it again.
    printf "subjectAltName=%s\n" "$san" > "$name.ext"
    openssl x509 -req -CA ca-cert.pem -CAkey ca-key.pem -in "$name.csr" \
        -out "$name-signed.pem" -days $VALIDITY_DAYS -CAcreateserial \
        -extfile "$name.ext"
    keytool -importcert -alias CARoot -file ca-cert.pem \
        -keystore "kafka.$name.keystore.p12" -storepass "$PASSWORD" -noprompt
    keytool -importcert -alias "$name" -file "$name-signed.pem" \
        -keystore "kafka.$name.keystore.p12" -storepass "$PASSWORD" -noprompt
    # The truststore holds only the CA certificate.
    keytool -importcert -alias CARoot -file ca-cert.pem \
        -keystore "kafka.$name.truststore.p12" -storetype PKCS12 \
        -storepass "$PASSWORD" -noprompt
}

make_keystore broker kafka "$SAN"
make_keystore client kafka-client "DNS:kafka-client,DNS:localhost"

# --- Step 4: PEM files for Python (librdkafka does not read PKCS12 stores) ----
echo "Step 4: export PEM files for Python clients"
cp "client-signed.pem" client-cert.pem
# Older JDKs protect the store with RC2, which OpenSSL 3 only reads with -legacy.
# Newer JDKs do not need it (and LibreSSL has no -legacy), so we try both.
openssl pkcs12 -in kafka.client.keystore.p12 -nocerts -nodes \
    -passin pass:"$PASSWORD" -out client-key.pem -legacy 2>/dev/null ||
openssl pkcs12 -in kafka.client.keystore.p12 -nocerts -nodes \
    -passin pass:"$PASSWORD" -out client-key.pem
# The Confluent Docker image reads the store password from this file.
printf "%s" "$PASSWORD" > store-password

rm -f ./*.csr ./*.ext ./*-signed.pem ./*.srl
chmod 644 ./*   # the Kafka container user must read the files (demo only)

echo ""
echo "Done. Files in $SSL_DIR/:"
ls -1
echo ""
echo "Store password: $PASSWORD"
echo "Python client config:"
echo "  'security.protocol': 'SSL',"
echo "  'ssl.ca.location': '$SSL_DIR/ca-cert.pem',"
echo "  'ssl.certificate.location': '$SSL_DIR/client-cert.pem',"
echo "  'ssl.key.location': '$SSL_DIR/client-key.pem'"
echo ""
echo "WARNING: demo only. Do not use these certificates in production."
