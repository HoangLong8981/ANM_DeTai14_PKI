#!/usr/bin/env bash
# Reissue a client certificate after the previous one was revoked (key-compromise recovery).
#   Usage: 05_reissue_user.sh <name> <CN> <email>
#   Example: 05_reissue_user.sh alice Alice alice@lab.local
# Idempotent: if <name>.crt is still valid in index.txt, nothing is changed.
set -euo pipefail

NAME="${1:?Usage: $0 <name> <CN> <email>}"
CN="${2:?Usage: $0 <name> <CN> <email>}"
EMAIL="${3:?Usage: $0 <name> <CN> <email>}"

WORKSPACE="/workspace"
INTER_DIR="${WORKSPACE}/pki/intermediate"
CONFIG_DIR="${WORKSPACE}/pki/config"
ARTIFACTS_CERTS="${WORKSPACE}/artifacts/certs"

CRT="${INTER_DIR}/certs/${NAME}.crt"
if [ ! -f "${CRT}" ]; then
    echo "[-] ${CRT} does not exist. Run 02_issue_certs.sh first."
    exit 1
fi

OLD_SERIAL=$(openssl x509 -in "${CRT}" -noout -serial | cut -d= -f2)
if ! awk -v s="${OLD_SERIAL}" '$1 == "R" && $4 == s {found=1} END {exit !found}' "${INTER_DIR}/index.txt"; then
    echo "[=] ${NAME}.crt (Serial ${OLD_SERIAL}) is still valid; nothing to reissue."
    exit 0
fi

ARCHIVE="${NAME}_${OLD_SERIAL}_revoked"
echo "[+] ${NAME}.crt (Serial ${OLD_SERIAL}) is revoked -> archiving as ${ARCHIVE}.{crt,key} and issuing a new certificate..."

# Keep the revoked pair as evidence (used by 'demo_report.sh tc07b')
cp -p "${ARTIFACTS_CERTS}/${NAME}.crt" "${ARTIFACTS_CERTS}/${ARCHIVE}.crt" 2>/dev/null || cp -p "${CRT}" "${ARTIFACTS_CERTS}/${ARCHIVE}.crt"
cp -p "${INTER_DIR}/private/${NAME}.key" "${ARTIFACTS_CERTS}/${ARCHIVE}.key"
mv "${CRT}" "${INTER_DIR}/certs/${ARCHIVE}.crt"
mv "${INTER_DIR}/private/${NAME}.key" "${INTER_DIR}/private/${ARCHIVE}.key"
chmod 600 "${INTER_DIR}/private/${ARCHIVE}.key" "${ARTIFACTS_CERTS}/${ARCHIVE}.key"

# New key + CSR (the private key never leaves the user in a real deployment; simulated here)
openssl genrsa -out "${INTER_DIR}/private/${NAME}.key" 2048
chmod 600 "${INTER_DIR}/private/${NAME}.key"

cat > "/tmp/${NAME}_ext.cnf" <<EXT
basicConstraints = CA:FALSE
nsCertType = client, email
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = clientAuth
EXT

openssl req -new -sha256 \
    -key "${INTER_DIR}/private/${NAME}.key" \
    -subj "/C=VN/ST=Ho Chi Minh/L=Ho Chi Minh City/O=UTH PKI Lab/OU=Engineering/CN=${CN}/emailAddress=${EMAIL}" \
    -out "${INTER_DIR}/csr/${NAME}.csr"

openssl ca -config "${CONFIG_DIR}/intermediate-ca.cnf" \
    -extfile "/tmp/${NAME}_ext.cnf" \
    -days 365 -notext -md sha256 -batch \
    -in "${INTER_DIR}/csr/${NAME}.csr" \
    -out "${CRT}"
chmod 644 "${CRT}"

cp "${CRT}" "${ARTIFACTS_CERTS}/${NAME}.crt"
cp "${INTER_DIR}/private/${NAME}.key" "${ARTIFACTS_CERTS}/${NAME}.key"
chmod 600 "${ARTIFACTS_CERTS}/${NAME}.key"

NEW_SERIAL=$(openssl x509 -in "${CRT}" -noout -serial | cut -d= -f2)
echo "[✓] Reissued ${NAME}.crt: Serial ${OLD_SERIAL} (revoked) -> ${NEW_SERIAL} (valid)."
echo "[i] The CRL is unchanged, so Nginx does not need a reload."
