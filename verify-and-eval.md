# 🎯 SKILL: Verification & Self-Healing Eval Loop (Thang điểm 10/10)

## 1. Nguyên tắc "Không Đoán Mò" (Anti-Hallucination Rule)
- Trước khi sửa bất kỳ lỗi nào của OpenSSL hoặc Nginx, Agent BẮT BUỘC phải:
  1. Đọc file log lỗi thực tế trong `artifacts/logs/` hoặc chạy `docker compose logs web`.
  2. Tra cứu `feature-map.md` để tìm đúng file `.cnf`, `.sh` hoặc `.conf` liên quan.
  3. Ghi nhận nguyên nhân gốc rễ (Root Cause) và cách khắc phục vào `MEMORY.md` để không lặp lại lỗi.

## 2. Chốt chặn Phân tích Tĩnh (Hard Constraints Linter)
Trước khi chạy kiểm thử kết nối, Agent phải chạy kiểm tra tĩnh bên trong container:
1. Kiểm tra không có ký tự `CRLF` (`\r`) trong `pki/` và `tests/`: `grep -U $'\r' pki/scripts/*.sh tests/*.sh` (phải trả về rỗng).
2. Kiểm tra X.509v3 SAN extension trong cert: `openssl x509 -in secure.crt -text -noout | grep -A1 "Subject Alternative Name"`.
3. Kiểm tra cú pháp Nginx: `docker compose exec web nginx -t`.

## 3. Bảng chấm điểm Eval Rubric (Hill-Climbing tới 10/10)
Sau mỗi lần chạy `tests/run_all_tests.sh`, Agent phải tự chấm điểm theo Rubric sau:
- **[2.0 điểm] Linter & Build**: Tất cả containers `Up`, `nginx -t` thành công, không dính lỗi CRLF, khóa `.key` có quyền `600`.
- **[1.5 điểm] TC01 (Chain of Trust)**: File `artifacts/logs/TC01_chain_verify.log` có dòng `OK`.
- **[1.5 điểm] TC02 (Valid HTTPS)**: File `artifacts/logs/TC02_valid_https.log` có `HTTP/1.1 200 OK` (hoặc `HTTP/2 200`) và `Verify return code: 0 (ok)`.
- **[1.5 điểm] TC03 (mTLS Auth)**: File `artifacts/logs/TC03_mtls_auth.log` chứng minh rõ 2 vế: Không có client cert -> bị từ chối (`400 Bad Request`); Có `alice.crt` -> `200 OK`.
- **[1.0 điểm] TC04 (Expired Cert)**: File `artifacts/logs/TC04_expired_cert.log` bắt được chuỗi `verify error:num=10:certificate has expired`.
- **[1.0 điểm] TC05 (Untrusted Cert)**: File `artifacts/logs/TC05_untrusted_cert.log` bắt được chuỗi `num=18` hoặc `num=20`.
- **[1.5 điểm] TC06 (Revoked CRL)**: File `artifacts/logs/TC06_revoked_crl.log` bắt được chuỗi `verify error:num=23:certificate revoked` và kết nối HTTPS vào `revoked.lab.local` bị Nginx chặn.

> **Vòng lặp Hill-Climbing**: Nếu tổng điểm < **10.0 / 10.0**, Agent KHÔNG ĐƯỢC DỪNG LẠI hỏi người dùng mà phải tự động phân tích log, sửa code, tái tạo cert/reload Nginx và chạy lại Eval cho đến khi đạt tuyệt đối **10.0 / 10.0**.