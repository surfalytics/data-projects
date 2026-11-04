# Exercise 02: Security

## Exercise 2.1: SSL/TLS Certificate Setup

**Objective:** Generate SSL certificates and configure a producer to use SSL encryption.

**Tasks:**

1. Run the SSL setup script to generate certificates:
   ```bash
   cd config
   bash ssl-setup.sh
   cd ..
   ```

2. Examine the generated files in the `ssl/` directory. For each file, write a one-sentence description of what it contains and its role in the SSL handshake:
   - `ca-cert.pem`
   - `kafka.broker.keystore.jks`
   - `kafka.broker.truststore.jks`
   - `kafka.client.keystore.jks`
   - `kafka.client.truststore.jks`
   - `client-cert.pem`
   - `client-key.pem`

3. Inspect the CA certificate using openssl:
   ```bash
   openssl x509 -in ssl/ca-cert.pem -text -noout
   ```
   Answer these questions:
   - What is the Subject?
   - What is the Issuer? (Why are they the same?)
   - What is the validity period?
   - What key algorithm and size is used?

4. Verify the client certificate was signed by the CA:
   ```bash
   openssl verify -CAfile ssl/ca-cert.pem ssl/client-cert.pem
   ```

5. Review the `src/ssl_producer.py` code. List all SSL-related configuration properties and explain what each one does.

6. Write a brief comparison (5-10 sentences) of one-way TLS vs mutual TLS (mTLS). When would you use each?

**Deliverable:** A file `exercises/ssl-analysis.md` with your answers to all questions above.

---

## Exercise 2.2: SASL Authentication and ACLs

**Objective:** Understand SASL configuration and design an ACL policy.

**Tasks:**

1. Review the `src/sasl_producer.py` code. Answer these questions:
   - What is the difference between `SASL_PLAINTEXT` and `SASL_SSL`?
   - Why is `SASL_PLAINTEXT` dangerous in production?
   - What SASL mechanisms are available and when would you use each?

2. Design an ACL policy for the following scenario:

   Your team has three Kafka applications:
   - **order-service**: Produces to `orders` topic, consumes from `inventory-updates` topic
   - **inventory-service**: Consumes from `orders` topic, produces to `inventory-updates` topic
   - **analytics-service**: Consumes from both `orders` and `inventory-updates` topics (read-only)

   Each application uses a separate SASL username matching its service name.

   Write the `kafka-acls.sh` commands to:
   - Create the minimum necessary permissions for each service
   - Ensure no service can access topics it should not
   - Create a consumer group ACL for each service (use the service name as the group ID)

3. Explain why the principle of least privilege matters for Kafka ACLs. What could go wrong if you grant `User:*` full access?

**Deliverable:** A file `exercises/acl-policy.md` with the ACL commands and explanations.
