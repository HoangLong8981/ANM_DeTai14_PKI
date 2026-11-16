#!/usr/bin/env bash
set -euo pipefail
trap 'rm -f /tmp/*_ext.cnf /tmp/rogue-ca.* /tmp/untrusted.csr' EXIT

echo "=========================================================="
echo "[*] Step 2: Issuing Certificates for Services and Users"
echo "=========================================================="

WORKSPACE="/workspace"
PKI_DIR="${WORKSPACE}/pki"
INTER_DIR="${PKI_DIR}/intermediate"
CONFIG_DIR="${PKI_DIR}/config"
ARTIFACTS_CERTS="${WORKSPACE}/artifacts/certs"

mkdir -p "${INTER_DIR}/certs" "${INTER_DIR}/private" "${INTER_DIR}/csr" "${ARTIFACTS_CERTS}"
chmod 700 "${INTER_DIR}/private"

# Function to generate server CSR and Certificate
issue_server_cert() {
    local name="$1"
    local domain="$2"
    local extra_flags="${3:-}"

    echo "[+] Processing Server Certificate: ${domain} (${name})..."
    if [ -f "${INTER_DIR}/certs/${name}.crt" ] && [ -f "${INTER_DIR}/private/${name}.key" ]; then
        echo "[!] Certificate ${name}.crt already exists, skipping re-issuance."
        cp "${INTER_DIR}/certs/${name}.crt" "${ARTIFACTS_CERTS}/${name}.crt"
        cp "${INTER_DIR}/private/${name}.key" "${ARTIFACTS_CERTS}/${name}.key"
        chmod 600 "${ARTIFACTS_CERTS}/${name}.key"
        return 0
    fi
    
    # Generate Key
    if [ ! -f "${INTER_DIR}/private/${name}.key" ]; then
        openssl genrsa -out "${INTER_DIR}/private/${name}.key" 2048
        chmod 600 "${INTER_DIR}/private/${name}.key"
    fi

    # Create SAN extension
    cat > "/tmp/${name}_ext.cnf" <<EOF
basicConstraints = CA:FALSE
nsCertType = server
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = DNS:${domain}, DNS:localhost, IP:127.0.0.1
EOF

    # Generate CSR
    openssl req -new -sha256 \
        -key "${INTER_DIR}/private/${name}.key" \
        -subj "/C=VN/ST=Ho Chi Minh/L=Ho Chi Minh City/O=UTH PKI Lab/OU=Server/CN=${domain}" \
        -out "${INTER_DIR}/csr/${name}.csr"

    # Sign with Intermediate CA
    openssl ca -config "${CONFIG_DIR}/intermediate-ca.cnf" \
        -extfile "/tmp/${name}_ext.cnf" \
        ${extra_flags} \
        -notext -md sha256 -batch \
        -in "${INTER_DIR}/csr/${name}.csr" \
        -out "${INTER_DIR}/certs/${name}.crt"
    
    chmod 644 "${INTER_DIR}/certs/${name}.crt"
    cp "${INTER_DIR}/certs/${name}.crt" "${ARTIFACTS_CERTS}/${name}.crt"
    cp "${INTER_DIR}/private/${name}.key" "${ARTIFACTS_CERTS}/${name}.key"
    chmod 600 "${ARTIFACTS_CERTS}/${name}.key"
    echo "[✓] Issued ${domain} -> ${name}.crt"
}

# 1. Service 1: secure.lab.local (Valid HTTPS)
issue_server_cert "secure" "secure.lab.local" "-days 365"

# 2. Service 2: api.lab.local (API + mTLS)
issue_server_cert "api" "api.lab.local" "-days 365"

# Reusable helper to generate client CSR and Certificate for mTLS
issue_client_cert() {
    local name="$1"
    local cn="$2"
    local email="$3"

    echo "[+] Processing Client Certificate: ${cn} (${email})..."
    if [ -f "${INTER_DIR}/certs/${name}.crt" ] && [ -f "${INTER_DIR}/private/${name}.key" ]; then
        echo "[!] Client certificate ${name}.crt already exists, skipping re-issuance."
        cp "${INTER_DIR}/certs/${name}.crt" "${ARTIFACTS_CERTS}/${name}.crt"
        cp "${INTER_DIR}/private/${name}.key" "${ARTIFACTS_CERTS}/${name}.key"
        chmod 600 "${ARTIFACTS_CERTS}/${name}.key"
        return 0
    fi

    if [ ! -f "${INTER_DIR}/private/${name}.key" ]; then
        openssl genrsa -out "${INTER_DIR}/private/${name}.key" 2048
        chmod 600 "${INTER_DIR}/private/${name}.key"
    fi

    cat > "/tmp/${name}_ext.cnf" <<EOF
basicConstraints = CA:FALSE
nsCertType = client, email
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = clientAuth
EOF

    openssl req -new -sha256 \
        -key "${INTER_DIR}/private/${name}.key" \
        -subj "/C=VN/ST=Ho Chi Minh/L=Ho Chi Minh City/O=UTH PKI Lab/OU=Engineering/CN=${cn}/emailAddress=${email}" \
        -out "${INTER_DIR}/csr/${name}.csr"

    openssl ca -config "${CONFIG_DIR}/intermediate-ca.cnf" \
        -extfile "/tmp/${name}_ext.cnf" \
        -days 365 -notext -md sha256 -batch \
        -in "${INTER_DIR}/csr/${name}.csr" \
        -out "${INTER_DIR}/certs/${name}.crt"

    chmod 644 "${INTER_DIR}/certs/${name}.crt"
    cp "${INTER_DIR}/certs/${name}.crt" "${ARTIFACTS_CERTS}/${name}.crt"
    cp "${INTER_DIR}/private/${name}.key" "${ARTIFACTS_CERTS}/${name}.key"
    chmod 600 "${ARTIFACTS_CERTS}/${name}.key"
    echo "[✓] Issued Client Certificate -> ${name}.crt"
}

# 3. User 1: alice (Valid Client Certificate for mTLS)
issue_client_cert "alice" "Alice" "alice@lab.local"

# 4. User 2: bob (Initially valid client certificate, revoked in Step 3 for Nginx CRL demo)
issue_client_cert "bob" "Bob" "bob@lab.local"

# 5. Service: expired.lab.local (Expired Certificate)
issue_server_cert "expired" "expired.lab.local" "-startdate 20200101000000Z -enddate 20200102000000Z"

# 6. Service: untrusted.lab.local (Rogue CA / Self-signed)
echo "[+] Processing Untrusted / Rogue CA Certificate: untrusted.lab.local..."
if [ -f "${INTER_DIR}/certs/untrusted.crt" ] && [ -f "${INTER_DIR}/private/untrusted.key" ]; then
    echo "[!] Certificate untrusted.crt already exists, skipping re-issuance."
    cp "${INTER_DIR}/certs/untrusted.crt" "${ARTIFACTS_CERTS}/untrusted.crt"
    cp "${INTER_DIR}/private/untrusted.key" "${ARTIFACTS_CERTS}/untrusted.key"
    chmod 600 "${ARTIFACTS_CERTS}/untrusted.key"
else
if [ ! -f "${INTER_DIR}/private/untrusted.key" ]; then
    openssl genrsa -out "${INTER_DIR}/private/untrusted.key" 2048
    chmod 600 "${INTER_DIR}/private/untrusted.key"
fi

# Create an untrusted rogue CA
openssl genrsa -out /tmp/rogue-ca.key 2048
chmod 600 /tmp/rogue-ca.key
openssl req -x509 -new -nodes -key /tmp/rogue-ca.key -sha256 -days 30 \
    -subj "/C=US/ST=Unknown/L=Unknown/O=Rogue Untrusted Entity/CN=Rogue Root CA" \
    -out /tmp/rogue-ca.crt

cat > "/tmp/untrusted_ext.cnf" <<EOF
basicConstraints = CA:FALSE
nsCertType = server
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = DNS:untrusted.lab.local, DNS:localhost, IP:127.0.0.1
EOF

openssl req -new -sha256 \
    -key "${INTER_DIR}/private/untrusted.key" \
    -subj "/C=US/ST=Unknown/L=Unknown/O=Rogue Untrusted Entity/CN=untrusted.lab.local" \
    -out /tmp/untrusted.csr

openssl x509 -req -in /tmp/untrusted.csr \
    -CA /tmp/rogue-ca.crt -CAkey /tmp/rogue-ca.key -CAcreateserial \
    -out "${INTER_DIR}/certs/untrusted.crt" \
    -days 365 -sha256 \
    -extfile "/tmp/untrusted_ext.cnf"

chmod 644 "${INTER_DIR}/certs/untrusted.crt"
cp "${INTER_DIR}/certs/untrusted.crt" "${ARTIFACTS_CERTS}/untrusted.crt"
cp "${INTER_DIR}/private/untrusted.key" "${ARTIFACTS_CERTS}/untrusted.key"
chmod 600 "${ARTIFACTS_CERTS}/untrusted.key"
echo "[✓] Issued Untrusted Certificate -> untrusted.crt"
fi

# 7. Service: revoked.lab.local (Initially valid, will be revoked in Step 3)
issue_server_cert "revoked" "revoked.lab.local" "-days 365"

# 8. Build full-chain files (leaf + Intermediate CA) so Nginx sends the complete chain.
#    Browsers/clients that only trust the Root CA need the Intermediate CA from the server.
echo "[+] Building fullchain files (leaf + Intermediate CA) for secure and api..."
for n in secure api; do
    cat "${ARTIFACTS_CERTS}/${n}.crt" "${ARTIFACTS_CERTS}/inter-ca.crt" > "${ARTIFACTS_CERTS}/${n}.fullchain.crt"
    chmod 644 "${ARTIFACTS_CERTS}/${n}.fullchain.crt"
done

echo "[✓] Step 2 completed successfully: All certificates issued."
