#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="/workspace"
LOGS_DIR="${WORKSPACE}/artifacts/logs"
TOTAL_SCORE=0

echo "=========================================================="
echo "    BẢNG ĐÁNH GIÁ CHẤM ĐIỂM TỰ ĐỘNG (EVAL RUBRIC 10/10)"
echo "=========================================================="

# 1. Linter & Build (2.0 pts)
LINTER_SCORE=0
CRLF_COUNT=$(grep -l -U $'\r' "${WORKSPACE}"/pki/scripts/*.sh "${WORKSPACE}"/tests/*.sh 2>/dev/null | wc -l || true)
if [ "${CRLF_COUNT}" -eq 0 ]; then
    echo "[PASS] [1.0 pt] Không có ký tự CRLF trong các file script."
    LINTER_SCORE=$(awk "BEGIN {print $LINTER_SCORE + 1.0}")
else
    echo "[FAIL] [0.0 pt] Phát hiện file có ký tự CRLF!"
fi

KEY_PERM_OK=1
for k in "${WORKSPACE}"/artifacts/certs/*.key; do
    if [ -f "$k" ]; then
        PERM=$(stat -c "%a" "$k" 2>/dev/null || stat -f "%Op" "$k" 2>/dev/null || echo "600")
        if [ "$PERM" != "600" ] && [ "$PERM" != "400" ] && [ "$PERM" != "700" ]; then
            KEY_PERM_OK=0
        fi
    fi
done

if [ "$KEY_PERM_OK" -eq 1 ]; then
    echo "[PASS] [1.0 pt] Quyền bảo mật khóa riêng tư hợp lệ (600/400)."
    LINTER_SCORE=$(awk "BEGIN {print $LINTER_SCORE + 1.0}")
else
    echo "[FAIL] [0.0 pt] Quyền khóa riêng tư chưa đúng tiêu chuẩn bảo mật."
fi
TOTAL_SCORE=$(awk "BEGIN {print $TOTAL_SCORE + $LINTER_SCORE}")

# 2. TC01 (1.5 pts)
TC01_SCORE=0
if [ -f "${LOGS_DIR}/TC01_chain_verify.log" ] && grep -q "OK" "${LOGS_DIR}/TC01_chain_verify.log"; then
    echo "[PASS] [1.5 pt] TC01 (Chain of Trust): Xác minh chuỗi tin cậy thành công (OK)."
    TC01_SCORE=1.5
else
    echo "[FAIL] [0.0 pt] TC01: Không tìm thấy kết quả OK trong TC01_chain_verify.log."
fi
TOTAL_SCORE=$(awk "BEGIN {print $TOTAL_SCORE + $TC01_SCORE}")

# 3. TC02 (1.5 pts)
TC02_SCORE=0
if [ -f "${LOGS_DIR}/TC02_valid_https.log" ] && \
   (grep -q "200 OK" "${LOGS_DIR}/TC02_valid_https.log" || grep -q "HTTP/.* 200" "${LOGS_DIR}/TC02_valid_https.log") && \
   grep -q "Verify return code: 0 (ok)" "${LOGS_DIR}/TC02_valid_https.log"; then
    echo "[PASS] [1.5 pt] TC02 (Valid HTTPS): HTTP 200 OK và Verify return code: 0 (ok)."
    TC02_SCORE=1.5
else
    echo "[FAIL] [0.0 pt] TC02: Thiếu HTTP 200 hoặc Verify return code 0 trong TC02_valid_https.log."
fi
TOTAL_SCORE=$(awk "BEGIN {print $TOTAL_SCORE + $TC02_SCORE}")

# 4. TC03 (1.5 pts)
TC03_SCORE=0
if [ -f "${LOGS_DIR}/TC03_mtls_auth.log" ] && \
   (grep -q "400 Bad Request" "${LOGS_DIR}/TC03_mtls_auth.log" || grep -q "HTTP/.* 400" "${LOGS_DIR}/TC03_mtls_auth.log") && \
   (grep -q "200 OK" "${LOGS_DIR}/TC03_mtls_auth.log" || grep -q "HTTP/.* 200" "${LOGS_DIR}/TC03_mtls_auth.log"); then
    echo "[PASS] [1.5 pt] TC03 (mTLS Auth): Chặn 400 khi không có cert và Cho phép 200 khi có Alice cert."
    TC03_SCORE=1.5
else
    echo "[FAIL] [0.0 pt] TC03: Không thỏa điều kiện mTLS trong TC03_mtls_auth.log."
fi
TOTAL_SCORE=$(awk "BEGIN {print $TOTAL_SCORE + $TC03_SCORE}")

# 5. TC04 (1.0 pt)
TC04_SCORE=0
if [ -f "${LOGS_DIR}/TC04_expired_cert.log" ] && \
   grep -q "verify error:num=10:certificate has expired" "${LOGS_DIR}/TC04_expired_cert.log"; then
    echo "[PASS] [1.0 pt] TC04 (Expired Cert): Bắt đúng lỗi verify error:num=10:certificate has expired."
    TC04_SCORE=1.0
else
    echo "[FAIL] [0.0 pt] TC04: Không bắt được lỗi certificate has expired."
fi
TOTAL_SCORE=$(awk "BEGIN {print $TOTAL_SCORE + $TC04_SCORE}")

# 6. TC05 (1.0 pt)
TC05_SCORE=0
if [ -f "${LOGS_DIR}/TC05_untrusted_cert.log" ] && \
   (grep -q "num=18" "${LOGS_DIR}/TC05_untrusted_cert.log" || grep -q "num=20" "${LOGS_DIR}/TC05_untrusted_cert.log"); then
    echo "[PASS] [1.0 pt] TC05 (Untrusted Cert): Bắt đúng lỗi Rogue/Untrusted CA (num=18 hoặc num=20)."
    TC05_SCORE=1.0
else
    echo "[FAIL] [0.0 pt] TC05: Không bắt được lỗi untrusted/self-signed trong TC05_untrusted_cert.log."
fi
TOTAL_SCORE=$(awk "BEGIN {print $TOTAL_SCORE + $TC05_SCORE}")

# 7. TC06 (1.5 pts)
TC06_SCORE=0
if [ -f "${LOGS_DIR}/TC06_revoked_crl.log" ] && \
   grep -q "verify error:num=23:certificate revoked" "${LOGS_DIR}/TC06_revoked_crl.log"; then
    echo "[PASS] [1.5 pt] TC06 (Revoked CRL): Bắt đúng lỗi verify error:num=23:certificate revoked."
    TC06_SCORE=1.5
else
    echo "[FAIL] [0.0 pt] TC06: Không bắt được lỗi certificate revoked."
fi
TOTAL_SCORE=$(awk "BEGIN {print $TOTAL_SCORE + $TC06_SCORE}")

echo "=========================================================="
echo "    TỔNG ĐIỂM ĐÁNH GIÁ (RUBRIC SCORE): ${TOTAL_SCORE} / 10.0"
echo "=========================================================="

if [ "$(echo "${TOTAL_SCORE} >= 10.0" | awk '{print ($1 >= 10.0)}')" -eq 1 ]; then
    echo ">>> KẾT QUẢ: ĐẠT ĐIỂM TUYỆT ĐỐI 10/10! <<<"
    exit 0
else
    echo ">>> KẾT QUẢ: CHƯA ĐẠT 10/10 (Hiện tại: ${TOTAL_SCORE}/10). CẦN SỬA LỖI! <<<"
    exit 1
fi
