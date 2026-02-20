#!/bin/bash
set -e

# =============================================================================
# SSL Certificate Generation Script for Kafka
# =============================================================================
# This script generates SSL certificates for demonstration purposes.
# DO NOT use these certificates in production. In production, use certificates
# signed by a trusted Certificate Authority (CA).
#
# What this script creates:
#   1. A self-signed Certificate Authority (CA)
#   2. A broker keystore and truststore (for Kafka broker identity and trust)
#   3. A client keystore and truststore (for Kafka client identity and trust)
#
# Directory structure after running:
#   ssl/
#     ca-cert        - CA certificate (public, shared with all parties)
#     ca-key         - CA private key (keep secret)
#     kafka.broker.keystore.jks   - Broker's keystore (private key + signed cert)
#     kafka.broker.truststore.jks - Broker's truststore (CA cert it trusts)
#     kafka.client.keystore.jks   - Client's keystore (private key + signed cert)
#     kafka.client.truststore.jks - Client's truststore (CA cert it trusts)
#     client-cert.pem             - Client certificate in PEM format (for Python clients)
#     client-key.pem              - Client private key in PEM format (for Python clients)
#     ca-cert.pem                 - CA certificate in PEM format (for Python clients)
# =============================================================================

# Configuration
SSL_DIR="./ssl"
CA_PASSWORD="ca-password-demo"
BROKER_KEYSTORE_PASSWORD="broker-ks-password"
BROKER_KEY_PASSWORD="broker-key-password"
BROKER_TRUSTSTORE_PASSWORD="broker-ts-password"
CLIENT_KEYSTORE_PASSWORD="client-ks-password"
CLIENT_KEY_PASSWORD="client-key-password"
CLIENT_TRUSTSTORE_PASSWORD="client-ts-password"
VALIDITY_DAYS=365
BROKER_CN="kafka-broker"
CLIENT_CN="kafka-client"

echo "============================================"
echo "Kafka SSL Certificate Generation"
echo "============================================"
echo ""

# Clean up any previous certificates
if [ -d "$SSL_DIR" ]; then
    echo "Removing existing SSL directory..."
    rm -rf "$SSL_DIR"
fi

mkdir -p "$SSL_DIR"
cd "$SSL_DIR"

# =============================================
# Step 1: Create the Certificate Authority (CA)
# =============================================
# The CA is the root of trust. Both broker and client will trust certificates
# signed by this CA. In production, you would use your organization's CA or
# a commercial CA (e.g., Let's Encrypt, DigiCert).

echo ""
echo "Step 1: Creating Certificate Authority (CA)..."
echo "-----------------------------------------------"

# Generate a CA key pair and self-signed certificate
# -genkeypair: Generate a key pair (private + public key)
# -alias: Name for this entry in the keystore
# -keyalg: Key algorithm (RSA)
# -keysize: Key size in bits (2048 is minimum for production)
# -dname: Distinguished Name (identity information)
# -keystore: Output keystore file
# -storetype: PKCS12 format (modern standard)
# -ext: X.509 extension (bc=ca:true marks this as a CA certificate)
openssl req -new -x509 -keyout ca-key -out ca-cert -days $VALIDITY_DAYS \
    -subj "/CN=KafkaDemoCA/OU=DataStreamingMastery/O=Demo/L=Local/S=State/C=US" \
    -passout pass:$CA_PASSWORD

echo "  CA certificate created: ca-cert"
echo "  CA private key created: ca-key"

# =============================================
# Step 2: Create the Broker Keystore
# =============================================
# The keystore holds the broker's private key and certificate.
# This is the broker's identity -- it proves "I am the Kafka broker."

echo ""
echo "Step 2: Creating Broker Keystore..."
echo "------------------------------------"

# Generate a key pair for the broker inside a JKS keystore
keytool -genkeypair -alias broker \
    -keyalg RSA -keysize 2048 \
    -dname "CN=$BROKER_CN,OU=DataStreamingMastery,O=Demo,L=Local,S=State,C=US" \
    -keystore kafka.broker.keystore.jks \
    -storepass $BROKER_KEYSTORE_PASSWORD \
    -keypass $BROKER_KEY_PASSWORD \
    -validity $VALIDITY_DAYS

echo "  Broker keystore created: kafka.broker.keystore.jks"

# Create a Certificate Signing Request (CSR) for the broker
# The CSR contains the broker's public key and identity, ready to be signed by the CA
keytool -certreq -alias broker \
    -keystore kafka.broker.keystore.jks \
    -storepass $BROKER_KEYSTORE_PASSWORD \
    -keypass $BROKER_KEY_PASSWORD \
    -file broker-csr

echo "  Broker CSR created: broker-csr"

# Sign the broker's CSR with the CA
# This creates a certificate that says "the CA vouches for this broker's identity"
openssl x509 -req -CA ca-cert -CAkey ca-key -in broker-csr \
    -out broker-cert-signed -days $VALIDITY_DAYS \
    -CAcreateserial -passin pass:$CA_PASSWORD

echo "  Broker certificate signed by CA: broker-cert-signed"

# Import the CA certificate into the broker's keystore
# The broker needs to know about the CA to build the certificate chain
keytool -importcert -alias ca -file ca-cert \
    -keystore kafka.broker.keystore.jks \
    -storepass $BROKER_KEYSTORE_PASSWORD \
    -noprompt

echo "  CA certificate imported into broker keystore"

# Import the signed broker certificate back into the broker's keystore
# This replaces the self-signed cert with the CA-signed one
keytool -importcert -alias broker -file broker-cert-signed \
    -keystore kafka.broker.keystore.jks \
    -storepass $BROKER_KEYSTORE_PASSWORD \
    -keypass $BROKER_KEY_PASSWORD \
    -noprompt

echo "  Signed broker certificate imported into broker keystore"

# =============================================
# Step 3: Create the Broker Truststore
# =============================================
# The truststore holds certificates the broker trusts.
# By importing the CA cert, the broker will trust any certificate signed by the CA.

echo ""
echo "Step 3: Creating Broker Truststore..."
echo "--------------------------------------"

keytool -importcert -alias ca -file ca-cert \
    -keystore kafka.broker.truststore.jks \
    -storepass $BROKER_TRUSTSTORE_PASSWORD \
    -noprompt

echo "  Broker truststore created: kafka.broker.truststore.jks"

# =============================================
# Step 4: Create the Client Keystore
# =============================================
# Same process as the broker, but for the client.
# This is only needed for mutual TLS (mTLS) where the broker also verifies client identity.

echo ""
echo "Step 4: Creating Client Keystore..."
echo "------------------------------------"

# Generate client key pair
keytool -genkeypair -alias client \
    -keyalg RSA -keysize 2048 \
    -dname "CN=$CLIENT_CN,OU=DataStreamingMastery,O=Demo,L=Local,S=State,C=US" \
    -keystore kafka.client.keystore.jks \
    -storepass $CLIENT_KEYSTORE_PASSWORD \
    -keypass $CLIENT_KEY_PASSWORD \
    -validity $VALIDITY_DAYS

echo "  Client keystore created: kafka.client.keystore.jks"

# Create client CSR
keytool -certreq -alias client \
    -keystore kafka.client.keystore.jks \
    -storepass $CLIENT_KEYSTORE_PASSWORD \
    -keypass $CLIENT_KEY_PASSWORD \
    -file client-csr

echo "  Client CSR created: client-csr"

# Sign client certificate with CA
openssl x509 -req -CA ca-cert -CAkey ca-key -in client-csr \
    -out client-cert-signed -days $VALIDITY_DAYS \
    -CAcreateserial -passin pass:$CA_PASSWORD

echo "  Client certificate signed by CA: client-cert-signed"

# Import CA cert into client keystore
keytool -importcert -alias ca -file ca-cert \
    -keystore kafka.client.keystore.jks \
    -storepass $CLIENT_KEYSTORE_PASSWORD \
    -noprompt

echo "  CA certificate imported into client keystore"

# Import signed client certificate into client keystore
keytool -importcert -alias client -file client-cert-signed \
    -keystore kafka.client.keystore.jks \
    -storepass $CLIENT_KEYSTORE_PASSWORD \
    -keypass $CLIENT_KEY_PASSWORD \
    -noprompt

echo "  Signed client certificate imported into client keystore"

# =============================================
# Step 5: Create the Client Truststore
# =============================================

echo ""
echo "Step 5: Creating Client Truststore..."
echo "--------------------------------------"

keytool -importcert -alias ca -file ca-cert \
    -keystore kafka.client.truststore.jks \
    -storepass $CLIENT_TRUSTSTORE_PASSWORD \
    -noprompt

echo "  Client truststore created: kafka.client.truststore.jks"

# =============================================
# Step 6: Export PEM files for Python clients
# =============================================
# Python's confluent-kafka library uses PEM files, not JKS keystores.
# We export the certificates and keys in PEM format.

echo ""
echo "Step 6: Exporting PEM files for Python clients..."
echo "--------------------------------------------------"

# Copy CA cert as PEM (it is already in PEM format from openssl)
cp ca-cert ca-cert.pem
echo "  CA certificate (PEM): ca-cert.pem"

# Export client certificate from keystore to PKCS12, then to PEM
keytool -exportcert -alias client \
    -keystore kafka.client.keystore.jks \
    -storepass $CLIENT_KEYSTORE_PASSWORD \
    -rfc -file client-cert.pem

echo "  Client certificate (PEM): client-cert.pem"

# Export client private key: convert keystore to PKCS12, then extract key
keytool -importkeystore \
    -srckeystore kafka.client.keystore.jks \
    -srcstorepass $CLIENT_KEYSTORE_PASSWORD \
    -srckeypass $CLIENT_KEY_PASSWORD \
    -srcalias client \
    -destkeystore client-keystore.p12 \
    -deststoretype PKCS12 \
    -deststorepass $CLIENT_KEYSTORE_PASSWORD \
    -destkeypass $CLIENT_KEY_PASSWORD

openssl pkcs12 -in client-keystore.p12 -nocerts -nodes \
    -passin pass:$CLIENT_KEYSTORE_PASSWORD \
    -out client-key.pem

echo "  Client private key (PEM): client-key.pem"

# =============================================
# Step 7: Clean up intermediate files
# =============================================

echo ""
echo "Step 7: Cleaning up intermediate files..."
echo "------------------------------------------"

rm -f broker-csr broker-cert-signed client-csr client-cert-signed
rm -f client-keystore.p12 ca-cert.srl

echo "  Intermediate files removed"

# =============================================
# Summary
# =============================================

echo ""
echo "============================================"
echo "SSL Certificate Generation Complete"
echo "============================================"
echo ""
echo "Files created in $SSL_DIR/:"
echo ""
echo "  Certificate Authority:"
echo "    ca-cert              - CA certificate"
echo "    ca-key               - CA private key (KEEP SECRET)"
echo "    ca-cert.pem          - CA certificate (PEM format)"
echo ""
echo "  Broker:"
echo "    kafka.broker.keystore.jks   - Broker keystore (password: $BROKER_KEYSTORE_PASSWORD)"
echo "    kafka.broker.truststore.jks - Broker truststore (password: $BROKER_TRUSTSTORE_PASSWORD)"
echo ""
echo "  Client:"
echo "    kafka.client.keystore.jks   - Client keystore (password: $CLIENT_KEYSTORE_PASSWORD)"
echo "    kafka.client.truststore.jks - Client truststore (password: $CLIENT_TRUSTSTORE_PASSWORD)"
echo "    client-cert.pem             - Client certificate (PEM, for Python)"
echo "    client-key.pem              - Client private key (PEM, for Python)"
echo ""
echo "  Kafka Broker server.properties:"
echo "    ssl.keystore.location=$SSL_DIR/kafka.broker.keystore.jks"
echo "    ssl.keystore.password=$BROKER_KEYSTORE_PASSWORD"
echo "    ssl.key.password=$BROKER_KEY_PASSWORD"
echo "    ssl.truststore.location=$SSL_DIR/kafka.broker.truststore.jks"
echo "    ssl.truststore.password=$BROKER_TRUSTSTORE_PASSWORD"
echo ""
echo "  Python Client configuration:"
echo "    'security.protocol': 'SSL'"
echo "    'ssl.ca.location': '$SSL_DIR/ca-cert.pem'"
echo "    'ssl.certificate.location': '$SSL_DIR/client-cert.pem'"
echo "    'ssl.key.location': '$SSL_DIR/client-key.pem'"
echo ""
echo "WARNING: These certificates are for DEMONSTRATION ONLY."
echo "         Do NOT use in production environments."
echo "============================================"
