#!/usr/bin/env bash
set -euo pipefail

echo "=========================================================="
echo "[*] Step 4: Certificate Renewal Demo (api.lab.local)"
echo "=========================================================="

WORKSPACE="/workspace"
PKI_DIR="${WORKSPACE}/pki"
ROOT_DIR="${PKI_DIR}/root"
INTER_DIR="${PKI_DIR}/intermediate"
CONFIG_DIR="${PKI_DIR}/config"
ARTIFACTS_CERTS="${WORKSPACE}/artifacts/certs"
LOGS_DIR="${WORKSPACE}/artifacts/logs"

mkdir -p "${LOGS_DIR}"
RENEW_LOG="${LOGS_DIR}/TC08_cert_renewal.log"

if [ ! -f "${INTER_DIR}/certs/api.crt" ]; then
    echo "[-] Error: ${INTER_DIR}/certs/api.crt does not exist. Run 02_issue_certs.sh first!"
    exit 1
fi

{
    echo "=== TC08: Certificate Renewal Lifecycle (api.lab.local) ==="
    echo "--- 1. Current Certificate State BEFORE Renewal ---"
    openssl x509 -in "${INTER_DIR}/certs/api.crt" -noout -subject -issuer -serial -dates
    echo ""

    if [ ! -f "${INTER_DIR}/certs/api_old.crt" ] || [ "${1:-}" = "--force" ]; then
        cp "${INTER_DIR}/certs/api.crt" "${INTER_DIR}/certs/api_old.crt"
        OLD_SERIAL=$(openssl x509 -in "${INTER_DIR}/certs/api_old.crt" -noout -serial | cut -d'=' -f2)

        echo "--- 2. Generating New Key & CSR for Renewal ---"
        openssl genrsa -out "${INTER_DIR}/private/api_renew.key" 2048
        chmod 600 "${INTER_DIR}/private/api_renew.key"

        cat > "/tmp/api_renew_ext.cnf" <<EOF
basicConstraints = CA:FALSE
nsCertType = server
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = DNS:api.lab.local, DNS:localhost, IP:127.0.0.1
EOF

        openssl req -new -sha256 \
            -key "${INTER_DIR}/private/api_renew.key" \
            -subj "/C=VN/ST=Ho Chi Minh/L=Ho Chi Minh City/O=UTH PKI Lab/OU=Server/CN=api.lab.local" \
            -out "${INTER_DIR}/csr/api_renew.csr"

        echo "--- 3. Signing Renewed Certificate (Extended Validity: 730 days) ---"
        openssl ca -config "${CONFIG_DIR}/intermediate-ca.cnf" \
            -extfile "/tmp/api_renew_ext.cnf" \
            -days 730 -notext -md sha256 -batch \
            -in "${INTER_DIR}/csr/api_renew.csr" \
            -out "${INTER_DIR}/certs/api_renew.crt"
        chmod 644 "${INTER_DIR}/certs/api_renew.crt"

        echo "--- 4. Superseding Old Certificate (Serial: ${OLD_SERIAL}) & Updating CRL ---"
        openssl ca -config "${CONFIG_DIR}/intermediate-ca.cnf" \
            -revoke "${INTER_DIR}/certs/api_old.crt" \
            -crl_reason superseded -batch || true

        openssl ca -config "${CONFIG_DIR}/intermediate-ca.cnf" \
            -gencrl -out "${INTER_DIR}/crl/inter.crl.pem"

        cp "${INTER_DIR}/certs/api_renew.crt" "${INTER_DIR}/certs/api.crt"
        cp "${INTER_DIR}/private/api_renew.key" "${INTER_DIR}/private/api.key"
        chmod 600 "${INTER_DIR}/private/api.key"
        cp "${INTER_DIR}/certs/api.crt" "${ARTIFACTS_CERTS}/api.crt"
        cp "${INTER_DIR}/private/api.key" "${ARTIFACTS_CERTS}/api.key"
        chmod 600 "${ARTIFACTS_CERTS}/api.key"
        cat "${ARTIFACTS_CERTS}/api.crt" "${ARTIFACTS_CERTS}/inter-ca.crt" > "${ARTIFACTS_CERTS}/api.fullchain.crt"
        chmod 644 "${ARTIFACTS_CERTS}/api.fullchain.crt"
        cp "${INTER_DIR}/crl/inter.crl.pem" "${ARTIFACTS_CERTS}/inter.crl.pem"
        cat "${INTER_DIR}/crl/inter.crl.pem" "${ROOT_DIR}/crl/root.crl.pem" > "${ARTIFACTS_CERTS}/ca-chain.crl.pem"
    else
        echo "[!] Renewal already demonstrated (api_old.crt exists); displaying current renewal verification."
    fi

    echo "--- 5. New Certificate State AFTER Renewal ---"
    openssl x509 -in "${ARTIFACTS_CERTS}/api.crt" -noout -subject -issuer -serial -dates
    echo ""
    echo "--- 6. Verification Comparison (Old Superseded vs Renewed Valid) ---"
    echo "[Old Certificate (${INTER_DIR}/certs/api_old.crt)]:"
    openssl verify -CAfile "${ARTIFACTS_CERTS}/ca-chain.crt" \
        -CRLfile "${ARTIFACTS_CERTS}/ca-chain.crl.pem" \
        -crl_check_all "${INTER_DIR}/certs/api_old.crt" 2>&1 || true
    echo ""
    echo "[Renewed Certificate (${ARTIFACTS_CERTS}/api.crt)]:"
    openssl verify -CAfile "${ARTIFACTS_CERTS}/ca-chain.crt" \
        -CRLfile "${ARTIFACTS_CERTS}/ca-chain.crl.pem" \
        -crl_check_all "${ARTIFACTS_CERTS}/api.crt" 2>&1
    echo ""
    echo "--- 7. Intermediate CA Database (index.txt) Snapshot ---"
    cat "${INTER_DIR}/index.txt"
} > "${RENEW_LOG}" 2>&1

cat "${RENEW_LOG}"
echo "[✓] Certificate renewal completed. Log saved to ${RENEW_LOG}"
