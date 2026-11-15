#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="/workspace"
CERTS_DIR="${WORKSPACE}/artifacts/certs"
LOGS_DIR="${WORKSPACE}/artifacts/logs"
PKI_DIR="${WORKSPACE}/pki"

mkdir -p "${LOGS_DIR}"

echo "=========================================================="
echo "    CHẠY KIỂM THỬ MỞ RỘNG (TC07: mTLS CRL, TC08: RENEW, TC09: PROFILES)"
echo "=========================================================="

# -------------------------------------------------------------------------
# TC08: Certificate Renewal Lifecycle (api.lab.local)
# -------------------------------------------------------------------------
echo "[*] Running TC08: Certificate Renewal Lifecycle (api.lab.local)..."
bash "${PKI_DIR}/scripts/04_renew_cert.sh" >/dev/null

# Verify mTLS still works against the renewed api.crt
{
    echo ""
    echo "--- 8. Live mTLS Verification Against Renewed api.lab.local Server Cert ---"
    openssl s_client -connect api.lab.local:443 \
        -CAfile "${CERTS_DIR}/ca-chain.crt" \
        -cert "${CERTS_DIR}/alice.crt" -key "${CERTS_DIR}/alice.key" \
        -servername api.lab.local </dev/null 2>&1 | grep -E "(depth=|subject=|Verification:|New, TLSv|Verify return code:)" || true
    curl -i --cacert "${CERTS_DIR}/ca-chain.crt" \
        --cert "${CERTS_DIR}/alice.crt" --key "${CERTS_DIR}/alice.key" \
        https://api.lab.local/mtls || true
} >> "${LOGS_DIR}/TC08_cert_renewal.log" 2>&1

# -------------------------------------------------------------------------
# TC07 (Post-Revocation Verification): Nginx Server-Side CRL Check
# -------------------------------------------------------------------------
echo "[*] Verifying TC07: Nginx blocks revoked client cert (Bob) and permits Alice..."
{
    echo "--- Post-Revocation Live Check ---"
    curl -i --cacert "${CERTS_DIR}/ca-chain.crt" \
        --cert "${CERTS_DIR}/bob.crt" --key "${CERTS_DIR}/bob.key" \
        https://api.lab.local/mtls || true
    echo ""
    curl -i --cacert "${CERTS_DIR}/ca-chain.crt" \
        --cert "${CERTS_DIR}/alice.crt" --key "${CERTS_DIR}/alice.key" \
        https://api.lab.local/mtls || true
} > "${LOGS_DIR}/TC07_post_revocation_check.log" 2>&1

# -------------------------------------------------------------------------
# TC09: Comprehensive X.509v3 Profile Inspection (CA + 2 Services + 2 Users)
# -------------------------------------------------------------------------
echo "[*] Running TC09: Inspecting all CA, Server, Client Certificates & CRL..."
TC09_LOG="${LOGS_DIR}/TC09_cert_profiles_inspection.log"
{
    echo "=== TC09: Comprehensive X.509v3 Profile Inspection ==="
    echo "--- 1. Root CA Certificate (4096-bit, Self-Signed) ---"
    openssl x509 -in "${CERTS_DIR}/root-ca.crt" -noout -subject -issuer -serial -dates
    openssl x509 -in "${CERTS_DIR}/root-ca.crt" -text -noout | grep -E "(Public-Key:|Basic Constraints|CA:TRUE|Key Usage)" -A 1
    echo ""
    echo "--- 2. Intermediate CA Certificate (2048-bit, pathlen:0) ---"
    openssl x509 -in "${CERTS_DIR}/inter-ca.crt" -noout -subject -issuer -serial -dates
    openssl x509 -in "${CERTS_DIR}/inter-ca.crt" -text -noout | grep -E "(Public-Key:|Basic Constraints|CA:TRUE|pathlen|Key Usage)" -A 1
    echo ""
    echo "--- 3. Service 1: secure.lab.local (X.509v3 SAN + serverAuth) ---"
    openssl x509 -in "${CERTS_DIR}/secure.crt" -noout -subject -issuer -serial -dates
    openssl x509 -in "${CERTS_DIR}/secure.crt" -text -noout | grep -E "(Extended Key Usage|Subject Alternative Name|DNS:)" -A 1
    echo ""
    echo "--- 4. Service 2: api.lab.local (Renewed Cert, X.509v3 SAN + serverAuth) ---"
    openssl x509 -in "${CERTS_DIR}/api.crt" -noout -subject -issuer -serial -dates
    openssl x509 -in "${CERTS_DIR}/api.crt" -text -noout | grep -E "(Extended Key Usage|Subject Alternative Name|DNS:)" -A 1
    echo ""
    echo "--- 5. User 1: Alice Client Certificate (Valid, clientAuth) ---"
    openssl x509 -in "${CERTS_DIR}/alice.crt" -noout -subject -issuer -serial -dates
    openssl x509 -in "${CERTS_DIR}/alice.crt" -text -noout | grep -E "(Extended Key Usage|TLS Web Client)" -A 1
    echo ""
    echo "--- 6. User 2: Bob Client Certificate (Revoked, clientAuth) ---"
    openssl x509 -in "${CERTS_DIR}/bob.crt" -noout -subject -issuer -serial -dates
    echo ""
    echo "--- 7. Intermediate CRL Current Summary ---"
    openssl crl -in "${CERTS_DIR}/inter.crl.pem" -noout -text | grep -E "(Issuer:|Last Update:|Next Update:|Serial Number:|CRL Reason Code:|Key Compromise|Superseded)" -A 1
} > "${TC09_LOG}" 2>&1

echo "[✓] Extended tests TC08 & TC09 completed. Remember to run 'docker compose exec web nginx -s reload' and re-run TC07 verification!"
