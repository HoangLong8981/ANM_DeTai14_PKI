#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="/workspace"
CERTS_DIR="${WORKSPACE}/artifacts/certs"

show_tc01() {
    echo "=========================================================================="
    echo " ẢNH 1: [TC01] XÁC MINH CHUỖI TIN CẬY (CHAIN OF TRUST) "
    echo " Lệnh: openssl verify -CAfile artifacts/certs/ca-chain.crt artifacts/certs/secure.crt"
    echo " Ý nghĩa: Chứng minh Intermediate CA ký bởi Root CA và Server Cert ký bởi Inter CA"
    echo "=========================================================================="
    openssl verify -CAfile "${CERTS_DIR}/ca-chain.crt" "${CERTS_DIR}/secure.crt"
    echo ""
}

show_tc02() {
    echo "=========================================================================="
    echo " ẢNH 2: [TC02] DỊCH VỤ HTTPS HỢP LỆ (SECURE.LAB.LOCAL) "
    echo " Lệnh: curl -i & openssl s_client tới https://secure.lab.local"
    echo " Ý nghĩa: Kết nối TLS 1.3 hợp lệ (Verify return code: 0) và HTTP 200 OK"
    echo "=========================================================================="
    echo "[1] Kiểm tra HTTP Response bằng cURL:"
    curl -i --cacert "${CERTS_DIR}/ca-chain.crt" https://secure.lab.local
    echo ""
    echo "[2] Kiểm tra bắt tay TLS 1.3 & Verify return code bằng OpenSSL s_client:"
    openssl s_client -connect secure.lab.local:443 -CAfile "${CERTS_DIR}/ca-chain.crt" -servername secure.lab.local </dev/null 2>&1 | grep -E "(depth=|Verification:|New, TLSv|Cipher is|Protocol  :|Cipher    :|Verify return code:)"
    echo ""
}

show_tc03() {
    echo "=========================================================================="
    echo " ẢNH 3: [TC03] XÁC THỰC HAI CHIỀU mTLS (API.LAB.LOCAL) "
    echo " Ý nghĩa: Chặn khi không có client cert; Thành công khi có Alice cert"
    echo "=========================================================================="
    echo "[Bước 1] Truy cập KHÔNG CÓ Client Certificate:"
    curl -i --cacert "${CERTS_DIR}/ca-chain.crt" https://api.lab.local/mtls
    echo ""
    echo "[Bước 2] Truy cập CÓ Client Certificate của Alice (alice.crt & alice.key):"
    curl -i --cacert "${CERTS_DIR}/ca-chain.crt" \
        --cert "${CERTS_DIR}/alice.crt" \
        --key "${CERTS_DIR}/alice.key" \
        https://api.lab.local/mtls
    echo ""
}

show_tc04() {
    echo "=========================================================================="
    echo " ẢNH 4: [TC04] CHỨNG THƯ HẾT HẠN (EXPIRED.LAB.LOCAL) "
    echo " Lệnh: openssl s_client -connect expired.lab.local:443 -CAfile ca-chain.crt"
    echo " Ý nghĩa: OpenSSL bắt đúng lỗi num=10:certificate has expired"
    echo "=========================================================================="
    openssl s_client -connect expired.lab.local:443 -CAfile "${CERTS_DIR}/ca-chain.crt" -servername expired.lab.local </dev/null 2>&1 | grep -E "verify (error|return):num=10" -A 1
    echo ""
    curl -i --cacert "${CERTS_DIR}/ca-chain.crt" https://expired.lab.local 2>&1 || true
    echo ""
}

show_tc05() {
    echo "=========================================================================="
    echo " ẢNH 5: [TC05] CHỨNG THƯ KHÔNG TIN CẬY / ROGUE CA (UNTRUSTED.LAB.LOCAL) "
    echo " Lệnh: openssl s_client -connect untrusted.lab.local:443 -CAfile ca-chain.crt"
    echo " Ý nghĩa: Bắt lỗi Rogue CA không nằm trong chuỗi tin cậy (num=20)"
    echo "=========================================================================="
    openssl s_client -connect untrusted.lab.local:443 -CAfile "${CERTS_DIR}/ca-chain.crt" -servername untrusted.lab.local </dev/null 2>&1 | grep -E "verify (error|return):num=20" -A 1
    echo ""
    curl -i --cacert "${CERTS_DIR}/ca-chain.crt" https://untrusted.lab.local 2>&1 || true
    echo ""
}

show_tc06() {
    echo "=========================================================================="
    echo " ẢNH 6: [TC06] THU HỒI CHỨNG THƯ QUA DANH SÁCH CRL (REVOKED.LAB.LOCAL) "
    echo " Lệnh: openssl verify & s_client với cờ -CRL -crl_check"
    echo " Ý nghĩa: Bắt lỗi chứng thư đã bị Intermediate CA thu hồi (num=23)"
    echo "=========================================================================="
    echo "[1] Kiểm tra bằng openssl verify:"
    openssl verify -CAfile "${CERTS_DIR}/ca-chain.crt" -CRLfile "${CERTS_DIR}/inter.crl.pem" -crl_check "${CERTS_DIR}/revoked.crt" || true
    echo ""
    echo "[2] Kiểm tra kết nối s_client kèm CRL:"
    openssl s_client -connect revoked.lab.local:443 -CAfile "${CERTS_DIR}/ca-chain.crt" -CRL "${CERTS_DIR}/inter.crl.pem" -crl_check -servername revoked.lab.local </dev/null 2>&1 | grep -E "verify (error|return):num=23" -A 1
    echo ""
    echo "[3] Kết nối cURL kèm --crlfile:"
    curl -i --cacert "${CERTS_DIR}/ca-chain.crt" --crlfile "${CERTS_DIR}/inter.crl.pem" https://revoked.lab.local 2>&1 || true
    echo ""
}

show_cert_details() {
    echo "=========================================================================="
    echo " ẢNH BỔ TRỢ: CHI TIẾT CHỨNG THƯ X.509 VỚI SAN (SECURE & API) "
    echo " Lệnh: openssl x509 -in artifacts/certs/{secure,api}.crt -text -noout"
    echo "=========================================================================="
    echo "--- Service 1: secure.crt ---"
    openssl x509 -in "${CERTS_DIR}/secure.crt" -text -noout | grep -E "(Issuer|Subject:|Not Before|Not After|Subject Alternative Name|DNS:|IP Address)" -A 1
    echo ""
    echo "--- Service 2: api.crt ---"
    openssl x509 -in "${CERTS_DIR}/api.crt" -text -noout | grep -E "(Serial Number:|Issuer|Subject:|Not Before|Not After|Subject Alternative Name|DNS:|IP Address)" -A 1
    echo ""
}

show_tc07() {
    echo "=========================================================================="
    echo " [TC07] NGINX CHẶN CLIENT CERT BỊ THU HỒI BẰNG CRL (API.LAB.LOCAL) "
    echo " Ý nghĩa: Nginx dùng ssl_crl + ssl_verify_client chặn Bob (400) & cho phép Alice (200)"
    echo "=========================================================================="
    local alice_serial bob_serial
    alice_serial=$(openssl x509 -in "${CERTS_DIR}/alice.crt" -noout -serial | cut -d= -f2)
    bob_serial=$(openssl x509 -in "${CERTS_DIR}/bob.crt" -noout -serial | cut -d= -f2)
    echo "[1] Bob (Serial ${bob_serial} - Đã thu hồi trong ca-chain.crl.pem):"
    curl -i --cacert "${CERTS_DIR}/ca-chain.crt" --cert "${CERTS_DIR}/bob.crt" --key "${CERTS_DIR}/bob.key" https://api.lab.local/mtls || true
    echo ""
    echo "[2] Alice (Serial ${alice_serial} - Hợp lệ):"
    curl -i --cacert "${CERTS_DIR}/ca-chain.crt" --cert "${CERTS_DIR}/alice.crt" --key "${CERTS_DIR}/alice.key" https://api.lab.local/mtls
    echo ""
}

show_tc07_alice_revoked() {
    echo "=========================================================================="
    echo " [TC07b] NGINX CHẶN CHỨNG THƯ ALICE CŨ ĐÃ THU HỒI (alice_<serial>_revoked.crt) "
    echo " Điều kiện: đã chạy 05_reissue_user.sh và đã thu hồi chứng thư cũ trước đó"
    echo "=========================================================================="
    local crt key serial
    crt=$(ls "${CERTS_DIR}"/alice_*_revoked.crt 2>/dev/null | head -n1 || true)
    if [ -z "${crt}" ]; then
        echo "[-] Chưa có alice_<serial>_revoked.crt (chưa từng thu hồi/cấp lại Alice)."
        return 0
    fi
    key="${crt%.crt}.key"
    serial=$(openssl x509 -in "${crt}" -noout -serial | cut -d= -f2)
    echo "[1] Trạng thái Serial ${serial} trong index.txt:"
    grep -w "${serial}" "${WORKSPACE}/pki/intermediate/index.txt" || true
    echo ""
    echo "[2] mTLS với chứng thư đã thu hồi (kỳ vọng HTTP 400, error 23 trong log Nginx):"
    curl -i -sS --cacert "${CERTS_DIR}/ca-chain.crt" --cert "${crt}" --key "${key}" https://api.lab.local/mtls || true
    echo ""
    echo "[3] openssl verify -crl_check:"
    openssl verify -crl_check -CAfile "${CERTS_DIR}/ca-chain.crt" -CRLfile "${CERTS_DIR}/ca-chain.crl.pem" "${crt}" || true
    echo ""
}

show_tc08() {
    echo "=========================================================================="
    echo " [TC08] GIA HẠN CHỨNG THƯ SỐ (CERTIFICATE RENEWAL - API.LAB.LOCAL) "
    echo "=========================================================================="
    cat "${WORKSPACE}/artifacts/logs/TC08_cert_renewal.log"
    echo ""
}

CASE="${1:-all}"
case "$CASE" in
    1|tc01|TC01) show_tc01 ;;
    2|tc02|TC02) show_tc02 ;;
    3|tc03|TC03) show_tc03 ;;
    4|tc04|TC04) show_tc04 ;;
    5|tc05|TC05) show_tc05 ;;
    6|tc06|TC06) show_tc06 ;;
    7|tc07|TC07) show_tc07 ;;
    7b|tc07b|TC07B) show_tc07_alice_revoked ;;
    8|tc08|TC08) show_tc08 ;;
    cert|x509)  show_cert_details ;;
    all)
        show_cert_details
        show_tc01
        show_tc02
        show_tc03
        show_tc04
        show_tc05
        show_tc06
        show_tc07
        show_tc07_alice_revoked
        show_tc08
        ;;
    *)
        echo "Cách dùng: $0 [tc01|tc02|tc03|tc04|tc05|tc06|tc07|tc07b|tc08|cert|all]"
        exit 1
        ;;
esac
