# Solutions: Exercise 02 - Security

## Solution 2.1: SSL/TLS Certificate Setup

### File Descriptions

| File | Description | Role in SSL Handshake |
|---|---|---|
| `ca-cert.pem` | The Certificate Authority's public certificate. Contains the CA's public key and identity. | Both client and broker use this to verify that the other party's certificate was signed by a trusted CA. |
| `kafka.broker.keystore.jks` | Java KeyStore containing the broker's private key and CA-signed certificate. This is the broker's identity. | During the handshake, the broker presents its certificate from this keystore to prove its identity to clients. |
| `kafka.broker.truststore.jks` | Java KeyStore containing the CA certificate that the broker trusts. | The broker uses this to verify client certificates (in mutual TLS). If the client's cert was signed by this CA, the broker trusts it. |
| `kafka.client.keystore.jks` | Java KeyStore containing the client's private key and CA-signed certificate. This is the client's identity. | In mutual TLS, the client presents its certificate from this keystore to prove its identity to the broker. |
| `kafka.client.truststore.jks` | Java KeyStore containing the CA certificate that the client trusts. | The client uses this to verify the broker's certificate. If the broker's cert was signed by this CA, the client trusts it. |
| `client-cert.pem` | The client's CA-signed certificate in PEM format (used by Python clients instead of JKS). | Same as client keystore certificate, but in PEM format for use with librdkafka-based clients. |
| `client-key.pem` | The client's private key in PEM format (used by Python clients). | The client uses this to prove ownership of client-cert.pem during the TLS handshake. |

### Certificate Inspection

```bash
$ openssl x509 -in ssl/ca-cert.pem -text -noout
```

**Answers:**
- **Subject:** `CN=KafkaDemoCA, OU=DataStreamingMastery, O=Demo, L=Local, ST=State, C=US`
- **Issuer:** Same as Subject. They are the same because this is a **self-signed certificate**. The CA signs its own certificate -- there is no higher authority. In production, you would use a CA whose certificate is signed by a root CA in a chain of trust.
- **Validity period:** 365 days from creation date.
- **Key algorithm and size:** RSA 2048-bit. This is the minimum recommended for production. Many organizations now require 4096-bit RSA or ECDSA P-256.

### SSL Producer Configuration Properties

```python
producer_config = {
    # security.protocol: Tells the client to use SSL for all communication.
    # Options: PLAINTEXT, SSL, SASL_PLAINTEXT, SASL_SSL
    "security.protocol": "SSL",

    # ssl.ca.location: Path to the CA certificate (PEM format).
    # Used to verify the broker's certificate is signed by a trusted CA.
    "ssl.ca.location": "/path/to/ca-cert.pem",

    # ssl.certificate.location: Path to the client's certificate (PEM format).
    # Required for mutual TLS. The broker uses this to verify client identity.
    "ssl.certificate.location": "/path/to/client-cert.pem",

    # ssl.key.location: Path to the client's private key (PEM format).
    # Proves ownership of the client certificate.
    "ssl.key.location": "/path/to/client-key.pem",

    # ssl.key.password: Password for the private key (if encrypted).
    # Optional -- only needed if the key file is password-protected.
    "ssl.key.password": "password",
}
```

### One-Way TLS vs Mutual TLS (mTLS)

**One-way TLS** (server authentication only) is the standard TLS model used by web browsers. The client verifies the server's identity by checking the server's certificate against trusted CAs, but the server does not verify the client's identity. In Kafka, this means the client confirms it is talking to the real Kafka broker (not an imposter), but the broker accepts connections from any client. This is sufficient when authentication is handled by another mechanism (e.g., SASL username/password) or when the network is already secured (e.g., private VPC).

**Mutual TLS** (mTLS, two-way authentication) requires both sides to present certificates. The broker verifies the client's certificate in addition to the client verifying the broker's certificate. This provides strong cryptographic identity for both parties. In Kafka, mTLS is enabled by setting `ssl.client.auth=required` on the broker. The client's certificate CN or SAN can be used as the principal for ACL authorization. mTLS is preferred when you need certificate-based authentication without managing passwords, or when operating in zero-trust network environments where every connection must be mutually authenticated.

---

## Solution 2.2: SASL Authentication and ACLs

### SASL Questions

**Difference between SASL_PLAINTEXT and SASL_SSL:**
- `SASL_PLAINTEXT`: SASL authentication over an unencrypted connection. Credentials (username/password for PLAIN mechanism) are sent in cleartext.
- `SASL_SSL`: SASL authentication over an SSL/TLS-encrypted connection. Credentials are encrypted in transit.

**Why SASL_PLAINTEXT is dangerous in production:**
With the PLAIN mechanism, the username and password are sent in cleartext over the network. Anyone who can capture network traffic (via packet sniffing, a compromised switch, or a man-in-the-middle attack) can read the credentials. This is acceptable only in isolated development environments or when the network is already encrypted at a lower layer (e.g., IPsec, WireGuard).

**SASL Mechanisms:**
| Mechanism | When to Use |
|---|---|
| PLAIN | Development only (or combined with SSL). Simplest to set up. |
| SCRAM-SHA-256/512 | Production without Kerberos. Password is never transmitted (challenge-response). Stored in ZooKeeper. |
| GSSAPI (Kerberos) | Enterprise environments with existing Kerberos/Active Directory infrastructure. |
| OAUTHBEARER | Cloud-native environments with OAuth 2.0 identity providers (Okta, Auth0, Azure AD). |

### ACL Policy

```bash
# ================================================
# ACL Policy for E-Commerce Kafka Applications
# ================================================

# --- order-service ---
# Produces to 'orders' topic
kafka-acls.sh --bootstrap-server localhost:9092 \
  --add --allow-principal User:order-service \
  --operation Write --topic orders

# Consumes from 'inventory-updates' topic
kafka-acls.sh --bootstrap-server localhost:9092 \
  --add --allow-principal User:order-service \
  --operation Read --topic inventory-updates

# Consumer group permission
kafka-acls.sh --bootstrap-server localhost:9092 \
  --add --allow-principal User:order-service \
  --operation Read --group order-service

# --- inventory-service ---
# Consumes from 'orders' topic
kafka-acls.sh --bootstrap-server localhost:9092 \
  --add --allow-principal User:inventory-service \
  --operation Read --topic orders

# Produces to 'inventory-updates' topic
kafka-acls.sh --bootstrap-server localhost:9092 \
  --add --allow-principal User:inventory-service \
  --operation Write --topic inventory-updates

# Consumer group permission
kafka-acls.sh --bootstrap-server localhost:9092 \
  --add --allow-principal User:inventory-service \
  --operation Read --group inventory-service

# --- analytics-service ---
# Consumes from 'orders' topic (read-only)
kafka-acls.sh --bootstrap-server localhost:9092 \
  --add --allow-principal User:analytics-service \
  --operation Read --topic orders

# Consumes from 'inventory-updates' topic (read-only)
kafka-acls.sh --bootstrap-server localhost:9092 \
  --add --allow-principal User:analytics-service \
  --operation Read --topic inventory-updates

# Consumer group permission
kafka-acls.sh --bootstrap-server localhost:9092 \
  --add --allow-principal User:analytics-service \
  --operation Read --group analytics-service

# --- Verify the ACLs ---
kafka-acls.sh --bootstrap-server localhost:9092 --list
```

### Principle of Least Privilege

The principle of least privilege dictates that each application should have only the minimum permissions required to perform its function. For Kafka ACLs, this means:

- `order-service` can write to `orders` but cannot read from it (it does not need to)
- `analytics-service` can read but cannot write to any topic (preventing accidental data corruption)
- No service can create or delete topics (preventing accidental topic deletion)

If you grant `User:*` full access (or do not enable ACLs at all), the risks include:
1. **Data corruption**: Any service can write to any topic, potentially producing malformed or incorrect data
2. **Data exfiltration**: Any service can read sensitive topics (PII, financial data)
3. **Accidental deletion**: Any service can delete topics, causing data loss
4. **Blast radius**: A single compromised service credential gives the attacker full access to all Kafka data
5. **Compliance violations**: Regulations like GDPR, SOC 2, and HIPAA require access controls on data stores
