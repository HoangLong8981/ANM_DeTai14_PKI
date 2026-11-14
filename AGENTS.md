# 🤖 AGENTS.md — Quy Chuẩn & Kỹ Năng Tự Kiểm Chứng (Đề Tài 14: PKI)

> **Dự án**: Đồ án Môn học An ninh Mạng — Trường ĐH Giao thông vận tải TP.HCM (UTH)  
> **Đề tài 14**: **Xây dựng PKI thu nhỏ và quản lý vòng đời chứng thư**  
> **Mục tiêu**: Nghiên cứu lý thuyết và hiện thực mô hình thực nghiệm (Lab) hoàn toàn bằng Docker Compose cho vòng đời chứng thư số (tạo khóa, ký duyệt, phát hành, cài đặt HTTPS/mTLS, xác minh, thu hồi CRL).

Tài liệu này đóng vai trò là **Bộ chỉ dẫn tối cao (System Context, Hard Constraints & Verification Loop)** cho AI Agent trong workspace `ANM_DeTai14_PKI`.

---

## 1. Mục Tiêu & Tiêu Chí Nghiệm Thu (Acceptance Criteria)

Theo yêu cầu chính thức từ đề cương môn học (TS. Lê Quốc Tuấn):

| Hạng mục | Yêu cầu chi tiết | Tiêu chuẩn hoàn thành |
|---|---|---|
| **Mô hình CA** | Tạo CA gốc nội bộ (Root CA) và Intermediate CA (kiến trúc 2 tầng chuẩn) | Đầy đủ cấu trúc thư mục, tệp cấu hình `openssl.cnf`, database `index.txt`, `serial`, `crlnumber`. |
| **Phát hành chứng thư** | Phát hành cho **2 dịch vụ** (`secure.lab.local`, `api.lab.local`) và **1 người dùng** (`alice`) | Cert có phần mở rộng X.509v3, Subject Alternative Name (SAN), KeyUsage, ExtendedKeyUsage. |
| **Triển khai HTTPS** | Cấu hình dịch vụ Web/API an toàn (Nginx trên Docker) sử dụng cert đã phát hành | Truy cập thành công qua giao thức HTTPS (TLS 1.2 / TLS 1.3), xác minh chuỗi tin cậy thành công. |
| **Xác thực mTLS** | Cấu hình xác thực 2 chiều (Mutual TLS) bằng Client Certificate của người dùng `alice` | Cho phép truy cập khi có client cert hợp lệ; từ chối (HTTP 400/403) khi không có cert. |
| **Quản lý vòng đời** | Trình diễn đầy đủ 4 trạng thái: (1) Hợp lệ, (2) Hết hạn, (3) Không tin cậy, (4) Thu hồi | Có cơ chế thu hồi qua danh sách **CRL** (Certificate Revocation List) gắn trực tiếp vào Nginx và kiểm tra bằng OpenSSL. |
| **Bằng chứng (Artifacts)** | Tự động thu thập log và output dòng lệnh vào `./artifacts/logs/` | Bằng chứng xác minh rõ ràng từ `openssl verify`, `openssl s_client`, và `curl`. |

---

## 2. Kiến Trúc Hệ Thống (Architecture)

```mermaid
flowchart TD
    subgraph PKI_Core ["Hạ Tầng PKI Nội Bộ"]
        RootCA["Root CA (Tự Ký - 4096 bit)"]
        InterCA["Intermediate CA (Issuing CA - 2048 bit)"]
        CRLFile["CRL (Danh sách thu hồi chứng thư)"]
        RootCA -->|Ký cấp chứng thư| InterCA
        InterCA -->|Ký xuất & Cập nhật| CRLFile
    end

    subgraph Services ["Các Dịch Vụ Mạng (Nginx Docker)"]
        WebService["Service 1: Web Server (secure.lab.local)"]
        ApiService["Service 2: API + mTLS (api.lab.local)"]
        EdgeCases["Endpoints Test Lỗi: expired / untrusted / revoked.lab.local"]
    end

    subgraph Clients ["Container Kiểm Thử (client-tester)"]
        UserClient["User 1: Alice (Có Client Cert hợp lệ)"]
        GuestClient["Guest / Tester (Chạy script kiểm thử)"]
    end

    InterCA -->|Phát hành Server Cert| WebService
    InterCA -->|Phát hành Server Cert| ApiService
    InterCA -->|Phát hành Client Cert| UserClient

    UserClient -->|HTTPS + mTLS Thành công| ApiService
    GuestClient -->|Kiểm thử 6 kịch bản TC01-TC06| Services
    Services -.->|Nạp ssl_crl| CRLFile
    ---

## 3. Quy Ước Cấu Trúc Thư Mục Chuẩn

Mọi thành phần của đồ án phải tuân thủ đúng cấu trúc sau:
- `AGENTS.md`: Tài liệu định hướng tổng thể cho AI Agent.
- `feature-map.md`: Bản đồ định tuyến các chứng thư, cấu hình Nginx và script.
- `verify-and-eval.md`: Kỹ năng tự kiểm chứng, Linter và thang điểm Eval Rubric 10/10.
- `MEMORY.md`: Sổ tay ghi nhớ các lỗi kỹ thuật OpenSSL/Docker đã xử lý.
- `docker-compose.yml`: Khởi chạy môi trường mạng cô lập (`web`, `client`).
- `pki/config/`: Chứa `root-ca.cnf`, `intermediate-ca.cnf`, `server-ext.cnf`, `client-ext.cnf`.
- `pki/root/` & `pki/intermediate/`: Không gian lưu trữ `private/`, `certs/`, `crl/`, `index.txt`, `serial`.
- `pki/scripts/`: Chứa `01_setup_ca.sh`, `02_issue_certs.sh`, `03_revoke_crl.sh`.
- `services/nginx/conf.d/` & `html/`: Cấu hình virtual hosts cho `secure`, `api`, `expired`, `untrusted`, `revoked`.
- `tests/run_all_tests.sh`: Script tự động chạy toàn bộ 6 kịch bản TC01 -> TC06.
- `artifacts/certs/` & `artifacts/logs/`: Lưu các chứng thư công khai và 6 file `.log` kết quả kiểm thử.

---

## 4. Ràng Buộc Cứng (Hard Constraints)

1. **Cô lập hoàn toàn trong Docker**: TUYỆT ĐỐI KHÔNG cài đặt trực tiếp OpenSSL/Nginx hay sửa file `hosts` trên máy Windows Host. Mọi thao tác tạo khóa, chạy dịch vụ và kiểm thử phải diễn ra bên trong Docker containers thuộc mạng nội bộ `pki-net`.
2. **Xử lý tương thích Windows Host (CRLF & Permissions)**:
   - Mọi file `.sh` và `.cnf` tạo ra bắt buộc dùng ký tự xuống dòng chuẩn **LF** (không dùng CRLF).
   - Đặt cờ `set -euo pipefail` ở đầu mọi script Bash và chạy không tương tác (`-batch`, `-nodes`).
3. **Chuẩn kỹ thuật X.509v3**:
   - Khóa RSA: 4096-bit cho Root CA, 2048-bit cho Intermediate CA và các chứng thư thành phần; thuật toán băm `SHA-256`.
   - Mọi Server Certificate bắt buộc có `subjectAltName` (SAN) khớp với tên miền kiểm thử.
   - Trước khi khởi động lại Nginx, bắt buộc kiểm tra bằng `nginx -t`.

---

## 5. Vòng Lặp Tự Kiểm Chứng (Verification Skill & Test Matrix)

Sau khi sinh code và khởi chạy `docker compose up -d`, Agent **BẮT BUỘC** phải đọc `verify-and-eval.md` và `feature-map.md`, tự thực thi script `tests/run_all_tests.sh` bên trong container `client` và tự động sửa lỗi cho đến khi **cả 6 kịch bản dưới đây đều PASS và xuất đủ 6 file log vào `./artifacts/logs/`**:

| ID | Kịch Bản Kiểm Thử | Lệnh Thực Thi & Kiểm Chứng | Điều Kiện PASS (Expected Output) | File Minh Chứng |
|---|---|---|---|---|
| **TC01** | **Chuỗi tin cậy (Chain of Trust)** | `openssl verify -CAfile ca-chain.crt secure.crt` | Trả về `OK` | `artifacts/logs/TC01_chain_verify.log` |
| **TC02** | **Dịch vụ HTTPS Hợp lệ (Valid)** | `curl -i --cacert ca-chain.crt https://secure.lab.local` và `openssl s_client` | HTTP `200 OK` và `Verify return code: 0 (ok)` | `artifacts/logs/TC02_valid_https.log` |
| **TC03** | **Xác thực 2 chiều (mTLS Client Cert)** | Gọi `https://api.lab.local/mtls` (Lần 1: Không cert; Lần 2: Có `--cert alice.crt --key alice.key`) | Lần 1: Bị chặn (`400`/`403`); Lần 2: `200 OK` | `artifacts/logs/TC03_mtls_auth.log` |
| **TC04** | **Chứng thư Hết hạn (Expired Cert)** | Cấp 1 cert có `-startdate` và `-enddate` trong quá khứ cho `expired.lab.local`, kiểm tra bằng `openssl s_client` | Bắt đúng lỗi `verify error:num=10:certificate has expired` | `artifacts/logs/TC04_expired_cert.log` |
| **TC05** | **Chứng thư Không tin cậy (Untrusted)** | Tạo 1 Rogue CA tự ký cấp cert cho `untrusted.lab.local`, kiểm tra với `ca-chain.crt` chính thống | Bắt đúng lỗi `num=18` (self-signed) hoặc `num=20` (unable to get local issuer) | `artifacts/logs/TC05_untrusted_cert.log` |
| **TC06** | **Chứng thư Bị thu hồi (Revoked / CRL)** | Thu hồi cert `revoked.lab.local` bằng `openssl ca -revoke`, xuất CRL, kiểm tra bằng `openssl verify -crl_check` và Nginx | Báo rõ `verify error:num=23:certificate revoked` và `curl` bị từ chối kết nối | `artifacts/logs/TC06_revoked_crl.log` |
---
