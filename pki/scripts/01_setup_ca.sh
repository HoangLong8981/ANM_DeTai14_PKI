#!/usr/bin/env bash
set -euo pipefail

echo "=========================================================="
echo "[*] Step 1: Initializing Root CA and Intermediate CA"
echo "=========================================================="

WORKSPACE="/workspace"
PKI_DIR="${WORKSPACE}/pki"
ROOT_DIR="${PKI_DIR}/root"
INTER_DIR="${PKI_DIR}/intermediate"
CONFIG_DIR="${PKI_DIR}/config"
ARTIFACTS_CERTS="${WORKSPACE}/artifacts/certs"

mkdir -p "${ROOT_DIR}/certs" "${ROOT_DIR}/private" "${ROOT_DIR}/newcerts" "${ROOT_DIR}/crl"
mkdir -p "${INTER_DIR}/certs" "${INTER_DIR}/private" "${INTER_DIR}/newcerts" "${INTER_DIR}/crl" "${INTER_DIR}/csr"
mkdir -p "${ARTIFACTS_CERTS}"

chmod 700 "${ROOT_DIR}/private" "${INTER_DIR}/private"

# Initialize databases
touch "${ROOT_DIR}/index.txt"
if [ ! -f "${ROOT_DIR}/serial" ]; then
    echo 1000 > "${ROOT_DIR}/serial"
fi
if [ ! -f "${ROOT_DIR}/crlnumber" ]; then
    echo 1000 > "${ROOT_DIR}/crlnumber"
fi

touch "${INTER_DIR}/index.txt"
if [ ! -f "${INTER_DIR}/serial" ]; then
    echo 1000 > "${INTER_DIR}/serial"
fi
if [ ! -f "${INTER_DIR}/crlnumber" ]; then
    echo 1000 > "${INTER_DIR}/crlnumber"
fi

# 1. Root CA Key & Self-signed Certificate
if [ ! -f "${ROOT_DIR}/private/root-ca.key" ]; then
    echo "[+] Generating Root CA Private Key (4096-bit RSA)..."
    openssl genrsa -out "${ROOT_DIR}/private/root-ca.key" 4096
    chmod 600 "${ROOT_DIR}/private/root-ca.key"
fi

if [ ! -f "${ROOT_DIR}/certs/root-ca.crt" ]; then
    echo "[+] Generating Root CA Self-Signed Certificate..."
    openssl req -config "${CONFIG_DIR}/root-ca.cnf" \
        -key "${ROOT_DIR}/private/root-ca.key" \
        -new -x509 -days 3650 -sha256 \
        -extensions v3_ca \
        -out "${ROOT_DIR}/certs/root-ca.crt"
    chmod 644 "${ROOT_DIR}/certs/root-ca.crt"
fi

# 2. Intermediate CA Key & Certificate signed by Root CA
if [ ! -f "${INTER_DIR}/private/inter-ca.key" ]; then
    echo "[+] Generating Intermediate CA Private Key (2048-bit RSA)..."
    openssl genrsa -out "${INTER_DIR}/private/inter-ca.key" 2048
    chmod 600 "${INTER_DIR}/private/inter-ca.key"
fi

if [ ! -f "${INTER_DIR}/certs/inter-ca.crt" ]; then
    echo "[+] Generating Intermediate CA CSR..."
    openssl req -config "${CONFIG_DIR}/intermediate-ca.cnf" \
        -new -sha256 \
        -key "${INTER_DIR}/private/inter-ca.key" \
        -out "${INTER_DIR}/csr/inter-ca.csr"

    echo "[+] Root CA signing Intermediate CA certificate..."
    openssl ca -config "${CONFIG_DIR}/root-ca.cnf" \
        -extensions v3_intermediate_ca \
        -days 1825 -notext -md sha256 -batch \
        -in "${INTER_DIR}/csr/inter-ca.csr" \
        -out "${INTER_DIR}/certs/inter-ca.crt"
    chmod 644 "${INTER_DIR}/certs/inter-ca.crt"
fi

# 3. Create initial CRLs for Root CA and Intermediate CA
echo "[+] Generating Initial CRL for Root CA..."
openssl ca -config "${CONFIG_DIR}/root-ca.cnf" \
    -gencrl -out "${ROOT_DIR}/crl/root.crl.pem"

echo "[+] Generating Initial CRL for Intermediate CA..."
openssl ca -config "${CONFIG_DIR}/intermediate-ca.cnf" \
    -gencrl -out "${INTER_DIR}/crl/inter.crl.pem"

# 4. Construct CA Chain and CRL Chain (Intermediate CA + Root CA)
echo "[+] Constructing CA Chain and CRL Chain..."
cat "${INTER_DIR}/certs/inter-ca.crt" "${ROOT_DIR}/certs/root-ca.crt" > "${ARTIFACTS_CERTS}/ca-chain.crt"
cat "${INTER_DIR}/crl/inter.crl.pem" "${ROOT_DIR}/crl/root.crl.pem" > "${ARTIFACTS_CERTS}/ca-chain.crl.pem"
cp "${ROOT_DIR}/certs/root-ca.crt" "${ARTIFACTS_CERTS}/root-ca.crt"
cp "${INTER_DIR}/certs/inter-ca.crt" "${ARTIFACTS_CERTS}/inter-ca.crt"
cp "${ROOT_DIR}/crl/root.crl.pem" "${ARTIFACTS_CERTS}/root.crl.pem"
cp "${INTER_DIR}/crl/inter.crl.pem" "${ARTIFACTS_CERTS}/inter.crl.pem"

echo "[✓] Setup CA completed successfully."
