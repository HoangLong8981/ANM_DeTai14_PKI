#!/usr/bin/env bash
set -euo pipefail

echo "=========================================================="
echo "[*] Step 3: Revoking Certificates and Updating CRL Chain"
echo "=========================================================="

WORKSPACE="/workspace"
PKI_DIR="${WORKSPACE}/pki"
ROOT_DIR="${PKI_DIR}/root"
INTER_DIR="${PKI_DIR}/intermediate"
CONFIG_DIR="${PKI_DIR}/config"
ARTIFACTS_CERTS="${WORKSPACE}/artifacts/certs"

revoke_cert() {
    local cert_path="$1"
    local reason="$2"

    if [ ! -f "${cert_path}" ]; then
        echo "[-] Warning: Certificate ${cert_path} does not exist, skipping."
        return 0
    fi

    local serial
    serial=$(openssl x509 -in "${cert_path}" -noout -serial | cut -d'=' -f2)

    if awk -F'\t' -v s="${serial}" '$4 == s && $1 == "R" {found=1} END {exit !found}' "${INTER_DIR}/index.txt"; then
        echo "[!] Certificate ${cert_path} (Serial: ${serial}) is already Revoked."
    else
        echo "[+] Revoking ${cert_path} (Serial: ${serial}, Reason: ${reason})..."
        openssl ca -config "${CONFIG_DIR}/intermediate-ca.cnf" \
            -revoke "${cert_path}" \
            -crl_reason "${reason}" -batch
    fi
}

revoke_cert "${INTER_DIR}/certs/revoked.crt" "keyCompromise"
revoke_cert "${INTER_DIR}/certs/bob.crt" "keyCompromise"

echo "[+] Generating updated Intermediate CRL..."
openssl ca -config "${CONFIG_DIR}/intermediate-ca.cnf" \
    -gencrl -out "${INTER_DIR}/crl/inter.crl.pem"

echo "[+] Generating updated Root CRL..."
openssl ca -config "${CONFIG_DIR}/root-ca.cnf" \
    -gencrl -out "${ROOT_DIR}/crl/root.crl.pem"

cp "${INTER_DIR}/crl/inter.crl.pem" "${ARTIFACTS_CERTS}/inter.crl.pem"
cp "${ROOT_DIR}/crl/root.crl.pem" "${ARTIFACTS_CERTS}/root.crl.pem"
cat "${INTER_DIR}/crl/inter.crl.pem" "${ROOT_DIR}/crl/root.crl.pem" > "${ARTIFACTS_CERTS}/ca-chain.crl.pem"
chmod 644 "${ARTIFACTS_CERTS}/inter.crl.pem" "${ARTIFACTS_CERTS}/root.crl.pem" "${ARTIFACTS_CERTS}/ca-chain.crl.pem"

echo "[✓] Step 3 completed: CRL and ca-chain.crl.pem updated."
echo "[i] Nginx only reads ca-chain.crl.pem at (re)load time. Run on the HOST (not inside this container):"
echo "      docker compose exec web nginx -s reload"
