#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="/workspace"
LOGS_DIR="${WORKSPACE}/artifacts/logs"
CERTS_DIR="${WORKSPACE}/artifacts/certs"

mkdir -p "${LOGS_DIR}"

echo "=========================================================="
echo "    BẮT ĐẦU CHẠY BỘ KIỂM THỬ PKI LAB (TC01 -> TC06)"
echo "=========================================================="

# -------------------------------------------------------------------------
# TC01: Chain of Trust Verification
# -------------------------------------------------------------------------
echo "[*] Running TC01: Chain of Trust Verification..."
TC01_LOG="${LOGS_DIR}/TC01_chain_verify.log"
{
    echo "=== TC01: Chain of Trust Verification ==="
    echo "Command: openssl verify -CAfile ${CERTS_DIR}/ca-chain.crt ${CERTS_DIR}/secure.crt"
    openssl verify -CAfile "${CERTS_DIR}/ca-chain.crt" "${CERTS_DIR}/secure.crt"
} > "${TC01_LOG}" 2>&1 || true

# -------------------------------------------------------------------------
# TC02: Valid HTTPS Service (secure.lab.local)
# -------------------------------------------------------------------------
echo "[*] Running TC02: Valid HTTPS Service (secure.lab.local)..."
TC02_LOG="${LOGS_DIR}/TC02_valid_https.log"
{
    echo "=== TC02: Valid HTTPS Service ==="
    echo "--- 1. Testing with cURL ---"
    curl -i --cacert "${CERTS_DIR}/ca-chain.crt" https://secure.lab.local || true
    echo ""
    echo "--- 2. Testing with OpenSSL s_client ---"
    openssl s_client -connect secure.lab.local:443 -CAfile "${CERTS_DIR}/ca-chain.crt" -servername secure.lab.local </dev/null 2>&1 || true
} > "${TC02_LOG}" 2>&1

# -------------------------------------------------------------------------
# TC03: Mutual TLS Authentication (api.lab.local)
# -------------------------------------------------------------------------
echo "[*] Running TC03: Mutual TLS Authentication (api.lab.local)..."
TC03_LOG="${LOGS_DIR}/TC03_mtls_auth.log"
{
    echo "=== TC03: Mutual TLS (mTLS) Authentication ==="
    echo "--- Test 1: Accessing /mtls WITHOUT client certificate (Expected: 400 Bad Request) ---"
    curl -i --cacert "${CERTS_DIR}/ca-chain.crt" https://api.lab.local/mtls || true
    echo ""
    echo "--- Test 2: Accessing /mtls WITH Alice client certificate (Expected: 200 OK) ---"
    curl -i --cacert "${CERTS_DIR}/ca-chain.crt" \
        --cert "${CERTS_DIR}/alice.crt" \
        --key "${CERTS_DIR}/alice.key" \
        https://api.lab.local/mtls || true
} > "${TC03_LOG}" 2>&1

# -------------------------------------------------------------------------
# TC04: Expired Certificate (expired.lab.local)
# -------------------------------------------------------------------------
echo "[*] Running TC04: Expired Certificate (expired.lab.local)..."
TC04_LOG="${LOGS_DIR}/TC04_expired_cert.log"
{
    echo "=== TC04: Expired Certificate Verification ==="
    echo "--- 1. Testing with OpenSSL s_client ---"
    openssl s_client -connect expired.lab.local:443 -CAfile "${CERTS_DIR}/ca-chain.crt" -servername expired.lab.local </dev/null 2>&1 || true
    echo ""
    echo "--- 2. Testing with openssl verify ---"
    openssl verify -CAfile "${CERTS_DIR}/ca-chain.crt" "${CERTS_DIR}/expired.crt" 2>&1 || true
    echo ""
    echo "--- 3. Testing with cURL ---"
    curl -i --cacert "${CERTS_DIR}/ca-chain.crt" https://expired.lab.local 2>&1 || true
} > "${TC04_LOG}" 2>&1

# -------------------------------------------------------------------------
# TC05: Untrusted / Rogue CA Certificate (untrusted.lab.local)
# -------------------------------------------------------------------------
echo "[*] Running TC05: Untrusted / Rogue CA (untrusted.lab.local)..."
TC05_LOG="${LOGS_DIR}/TC05_untrusted_cert.log"
{
    echo "=== TC05: Untrusted Certificate Verification ==="
    echo "--- 1. Testing with OpenSSL s_client ---"
    openssl s_client -connect untrusted.lab.local:443 -CAfile "${CERTS_DIR}/ca-chain.crt" -servername untrusted.lab.local </dev/null 2>&1 || true
    echo ""
    echo "--- 2. Testing with openssl verify ---"
    openssl verify -CAfile "${CERTS_DIR}/ca-chain.crt" "${CERTS_DIR}/untrusted.crt" 2>&1 || true
    echo ""
    echo "--- 3. Testing with cURL ---"
    curl -i --cacert "${CERTS_DIR}/ca-chain.crt" https://untrusted.lab.local 2>&1 || true
} > "${TC05_LOG}" 2>&1

# -------------------------------------------------------------------------
# TC06: Revoked Certificate via CRL (revoked.lab.local)
# -------------------------------------------------------------------------
echo "[*] Running TC06: Revoked Certificate via CRL (revoked.lab.local)..."
TC06_LOG="${LOGS_DIR}/TC06_revoked_crl.log"
{
    echo "=== TC06: Revoked Certificate Verification via CRL ==="
    echo "--- 1. Testing with OpenSSL s_client with CRL check ---"
    openssl s_client -connect revoked.lab.local:443 \
        -CAfile "${CERTS_DIR}/ca-chain.crt" \
        -CRL "${CERTS_DIR}/inter.crl.pem" \
        -crl_check -servername revoked.lab.local </dev/null 2>&1 || true
    echo ""
    echo "--- 2. Testing with openssl verify with CRL check ---"
    openssl verify -CAfile "${CERTS_DIR}/ca-chain.crt" \
        -CRLfile "${CERTS_DIR}/inter.crl.pem" \
        -crl_check "${CERTS_DIR}/revoked.crt" 2>&1 || true
    echo ""
    echo "--- 3. Testing with cURL with CRL check ---"
    curl -i --cacert "${CERTS_DIR}/ca-chain.crt" \
        --crlfile "${CERTS_DIR}/inter.crl.pem" \
        https://revoked.lab.local 2>&1 || true
} > "${TC06_LOG}" 2>&1

echo "=========================================================="
echo "    HOÀN THÀNH TOÀN BỘ 6 KỊCH BẢN KIỂM THỬ"
echo "=========================================================="
