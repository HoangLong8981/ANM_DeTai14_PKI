#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="/workspace"
echo "[*] Normalizing line endings across all .sh and .cnf files..."
for f in "${WORKSPACE}"/pki/scripts/*.sh "${WORKSPACE}"/tests/*.sh "${WORKSPACE}"/pki/config/*.cnf; do
    if [ -f "$f" ]; then
        sed -i 's/\r$//' "$f"
        chmod +x "$f" 2>/dev/null || true
    fi
done

echo "[*] Step 1: Setting up Root CA & Intermediate CA..."
bash "${WORKSPACE}/pki/scripts/01_setup_ca.sh"

echo "[*] Step 2: Issuing certificates for services and clients..."
bash "${WORKSPACE}/pki/scripts/02_issue_certs.sh"

echo "[*] Step 3: Revoking revoked.crt and updating CRL..."
bash "${WORKSPACE}/pki/scripts/03_revoke_crl.sh"

echo "[*] Ensuring correct file permissions..."
chmod 700 "${WORKSPACE}/pki/root/private" "${WORKSPACE}/pki/intermediate/private"
chmod 600 "${WORKSPACE}"/pki/root/private/*.key "${WORKSPACE}"/pki/intermediate/private/*.key "${WORKSPACE}"/artifacts/certs/*.key 2>/dev/null || true
chmod 644 "${WORKSPACE}"/artifacts/certs/*.crt "${WORKSPACE}"/artifacts/certs/*.pem 2>/dev/null || true

echo "[✓] PKI Initialization completed successfully."
