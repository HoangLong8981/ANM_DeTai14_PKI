# 🧠 MEMORY.md — Sổ Tay Kỹ Thuật & Khắc Phục Sự Cố PKI Lab

Tài liệu này lưu lại các bài học kinh nghiệm, nguyên nhân gốc rễ (Root Causes) và giải pháp xử lý cho các vấn đề kỹ thuật liên quan đến OpenSSL, Nginx, Docker và tương thích môi trường Windows/Linux.

---

## 1. Danh Mục Các Lỗi Đã Ghi Nhận & Giải Pháp

### 1.1. Lỗi CRLF khi chạy script Bash trên Windows mount vào Linux Container
- **Hiện tượng**: `bash: ./script.sh: /bin/bash^M: bad interpreter: No such file or directory` hoặc cú pháp lỗi bất thường.
- **Nguyên nhân gốc rễ**: Tệp tin được soạn thảo trên Windows tự động dùng kết thúc dòng CRLF (`\r\n`). Khi mount vào Linux container, ký tự `\r` bị coi là một phần của lệnh/chuỗi.
- **Giải pháp dứt điểm**:
  - Viết file bằng định dạng LF (`\n`).
  - Trong kịch bản hoặc Dockerfile, sử dụng lệnh `sed -i 's/\r$//' <file>` hoặc kiểm tra bằng `grep -U $'\r'`.

### 1.2. Quyền Truy Cập Khóa Bí Mật (File Permissions)
- **Hiện tượng**: OpenSSL cảnh báo hoặc Nginx từ chối đọc khóa riêng, hoặc vi phạm tiêu chí bảo mật (quyền quá rộng).
- **Nguyên nhân gốc rễ**: File trên Windows NTFS mount vào Docker volume đôi khi kế thừa quyền mặc định `777` hoặc `755`.
- **Giải pháp dứt điểm**:
  - Trong container khởi tạo hoặc entrypoint, chủ động chạy `chmod 600` cho tất cả file `*.key` và `chmod 700` cho thư mục `private/`.

### 1.3. Lỗi Nginx kiểm tra CRL trong Kiến Trúc CA 2 Tầng (`ssl_crl` & `X509_V_FLAG_CRL_CHECK_ALL`)
- **Hiện tượng**:
  1. `ssl_crl` trong Nginx chỉ kiểm tra chứng thư **client** khi bật `ssl_verify_client on` (hoặc `optional`); đặt `ssl_crl` ở virtual host không bật `ssl_verify_client` (như `revoked.conf` ban đầu) không có tác dụng chặn chứng thư server.
  2. Khi bật `ssl_crl /etc/nginx/certs/inter.crl.pem;` trên `api.conf` (có `ssl_verify_client on; ssl_verify_depth 2;`), ngay cả client cert hợp lệ (`alice.crt`) cũng bị trả về `400 Bad Request - The SSL certificate error` với lỗi OpenSSL `error 3 at 1 depth lookup: unable to get certificate CRL`.
- **Nguyên nhân gốc rễ**: Trong mô hình 2 tầng (Root CA → Intermediate CA → Client), chỉ thị `ssl_crl` của Nginx kích hoạt cờ `X509_V_FLAG_CRL_CHECK | X509_V_FLAG_CRL_CHECK_ALL`, buộc OpenSSL phải tìm thấy tệp CRL của **cả Intermediate CA lẫn Root CA**. Nếu chỉ nạp `inter.crl.pem`, bước kiểm tra chuỗi tại tầng 1 (`inter-ca.crt`) không tìm thấy Root CRL nên bị từ chối. Ngoài ra, mức `error_log notice` mặc định của Nginx không in lỗi `(23:certificate revoked)` ở mức `info`.
- **Giải pháp dứt điểm**:
  - Sinh CRL cấp Root (`root.crl.pem`) từ `root-ca.cnf` và ghép chuỗi CRL `ca-chain.crl.pem = inter.crl.pem + root.crl.pem`.
  - Cấu hình `ssl_crl /etc/nginx/certs/ca-chain.crl.pem;` và `error_log /var/log/nginx/error.log info;` tại `api.conf` (nơi bật `ssl_verify_client on`), đồng thời gỡ `ssl_crl` khỏi `revoked.conf` để phản ánh đúng cơ chế client-side CRL check đối với server cert ở TC06.

### 1.8. Vấn Đề `sed -i "s/\r$//"` Qua PowerShell & OpenSSL Renewal (`unique_subject = no`)
- **Hiện tượng**:
  1. Truyền lệnh `docker compose exec client bash -c 'sed -i "s/\r$//" ...'` từ Windows PowerShell làm lớp parser bỏ dấu ngoặc kép và biến `\r` thành ký tự `r` thường (`s/r$//`), cắt mất chữ `r` cuối dòng (ví dụ `crlnumber` → `crlnumbe`, `server` → `serve`, `.csr` → `.cs`).
  2. Khi gia hạn chứng thư cùng Subject DN bằng `openssl ca`, OpenSSL mặc định `unique_subject = yes` trong `index.txt.attr` nên báo lỗi `TXT_DB error number 2` nếu chưa thu hồi chứng thư cũ.
- **Giải pháp dứt điểm**:
  - Chuyển đổi CRLF → LF bằng Python (`b.replace(b'\r\n', b'\n')`) hoặc pipe qua `tr -d '\r'` bên trong Linux thay vì truyền `sed` có `\r` qua tham số PowerShell.
  - Cấu hình `unique_subject = no` trong `pki/config/intermediate-ca.cnf` và `index.txt.attr`, kết hợp thu hồi chứng thư cũ với `-crl_reason superseded` trong `04_renew_cert.sh`.

### 1.4. Lỗi Thiếu Subject Alternative Name (SAN) trên Trình Duyệt & cURL Hiện Đại
- **Hiện tượng**: Trình duyệt hoặc OpenSSL cảnh báo `x509: certificate relies on legacy Common Name field, use SANs instead`.
- **Nguyên nhân gốc rễ**: Chuẩn RFC 2818 và TLS 1.3 không còn tin cậy chỉ Common Name (CN).
- **Giải pháp dứt điểm**:
  - Mọi cấu hình tạo cert server (`secure.lab.local`, `api.lab.local`, v.v.) bắt buộc cấu hình section `[ alt_names ]` với đầy đủ DNS và IP trong file `.cnf`.

### 1.5. Lỗi Chuỗi Tin Cậy (Chain of Trust) khi Xác Minh
- **Hiện tượng**: `openssl verify -CAfile ca-chain.crt secure.crt` lỗi `unable to get local issuer certificate`.
- **Nguyên nhân gốc rễ**: `ca-chain.crt` phải chứa cả Intermediate CA cert và Root CA cert theo đúng thứ tự (Intermediate CA trước, Root CA sau), hoặc cờ kiểm tra chưa nạp đủ untrusted/CAfile.
- **Giải pháp dứt điểm**:
  - Tạo `ca-chain.crt = inter-ca.crt + root-ca.crt`.

### 1.6. Khác biệt Cờ Chỉ Định CRL giữa `openssl verify` và `openssl s_client`
- **Hiện tượng**: `openssl s_client` báo lỗi `s_client: Unknown option: -CRLfile`.
- **Nguyên nhân gốc rễ**: Lệnh `openssl verify` dùng cờ `-CRLfile <file>`, trong khi lệnh `openssl s_client` trong OpenSSL 3 dùng cú pháp `-CRL <file>` kết hợp `-crl_check`.
- **Giải pháp dứt điểm**:
  - Với `openssl verify`: `openssl verify -CAfile ca-chain.crt -CRLfile inter.crl.pem -crl_check target.crt`
  - Với `openssl s_client`: `openssl s_client -connect host:443 -CAfile ca-chain.crt -CRL inter.crl.pem -crl_check`
  - Với `curl`: `curl --cacert ca-chain.crt --crlfile inter.crl.pem https://host`

### 1.7. Thứ Tự Khởi Chạy Nginx Phụ Thuộc Vào Chứng Thư Đã Sinh
- **Hiện tượng**: Container `web` (Nginx) crash loop nếu thư mục `./artifacts/certs` chưa có chứng thư và file CRL lúc khởi động.
- **Nguyên nhân gốc rễ**: Nginx đọc toàn bộ file `ssl_certificate` và `ssl_crl` ngay khi khởi tạo worker processes; nếu thiếu file, Nginx thoát với lỗi fatal error.
- **Giải pháp dứt điểm**:
  - Tách lệnh khởi động: chạy container `client` để sinh trọn vẹn PKI qua `init_all_pki.sh`, sau đó mới khởi chạy container `web`.

---
*Tài liệu này được cập nhật tự động bởi Agent trong quá trình hoàn thiện đồ án.*
