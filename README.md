# 🛡️ Đồ Án Môn Học An Ninh Mạng — Đề Tài 14: PKI Lab

> **Trường**: Đại học Giao thông vận tải TP.HCM (UTH)  
> **Môn học**: An ninh Mạng  
> **Giảng viên**: TS. Lê Quốc Tuấn  
> **Đề tài 14**: **Xây dựng PKI thu nhỏ và quản lý vòng đời chứng thư**

---

## 1. Tổng Quan Kiến Trúc & Công Nghệ

Hệ thống được thiết kế hoàn toàn cô lập trong môi trường **Docker Compose** (`pki-net`), không phụ thuộc và không can thiệp vào máy chủ vật lý Windows:

- **Hạ tầng PKI 2 tầng**:
  - `Root CA`: Khóa RSA 4096-bit tự ký, thời hạn 10 năm.
  - `Intermediate CA`: Khóa RSA 2048-bit do Root CA ký, chuyên trách ký phát hành và ký danh sách thu hồi chứng thư (CRL).
- **Các Dịch Vụ Mạng (Container `pki-web` - Nginx 1.27)**:
  - `secure.lab.local`: Web HTTPS tiêu chuẩn, xác minh chuỗi tin cậy hoàn hảo.
  - `api.lab.local`: API bảo mật xác thực 2 chiều (mTLS - Mutual TLS) bằng Client Certificate của người dùng `Alice`.
  - `expired.lab.local`: Dịch vụ với chứng thư đã hết hạn để mô phỏng lỗi kiểm tra thời gian hiệu lực.
  - `untrusted.lab.local`: Dịch vụ với chứng thư cấp bởi Rogue CA không thuộc chuỗi tin cậy.
  - `revoked.lab.local`: Dịch vụ với chứng thư đã bị thu hồi qua CRL (`inter.crl.pem`).
- **Container Kiểm Thử (`pki-client`)**:
  - Tích hợp sẵn `openssl`, `curl`, `bash` để tự động hóa toàn bộ quá trình phát hành và kiểm chứng độc lập.

---

## 2. Hướng Dẫn Vận Hành Nhanh (Quick Start)

Chạy tuần tự từ thư mục gốc dự án (PowerShell hoặc bash trên máy có Docker Desktop):

```bash
# 1. Khởi động container kiểm thử (có OpenSSL, curl, bash)
docker compose up -d client

# 2. Khởi tạo PKI: Root CA, Intermediate CA, cấp chứng thư, thu hồi, tạo CRL
#    (idempotent: chạy lại nhiều lần an toàn; tự cấp lại Alice nếu chứng thư cũ đã bị thu hồi)
docker compose exec client bash /workspace/pki/scripts/init_all_pki.sh

# 3. Khởi chạy Nginx (phải sau bước 2 vì cần secure/api.fullchain.crt)
docker compose up -d web
docker compose exec web nginx -t

# 4. Chạy 6 kịch bản TC01 -> TC06 (ghi log vào artifacts/logs/)
docker compose exec client bash /workspace/tests/run_all_tests.sh

# 5. (Mở rộng) TC07 - TC09: CRL phía Nginx, gia hạn api.lab.local, kiểm tra X.509v3
docker compose exec client bash /workspace/tests/run_extended_tests.sh
docker compose exec web nginx -s reload      # nạp lại api.crt gia hạn / CRL mới

# 6. Chấm điểm tự động (Eval Rubric). Script này CHỈ đọc các file log ở bước 4,
#    nên luôn chạy lại bước 4 trước khi chấm.
docker compose exec client bash /workspace/tests/eval_rubric.sh
```

Chạy từng kịch bản để chụp minh chứng: `docker compose exec client bash /workspace/tests/demo_report.sh [tc01..tc08|tc07b|cert|all]`.

**Thu hồi và cấp lại người dùng**

- `03_revoke_crl.sh` thu hồi `revoked.crt` (server) và `bob.crt` (client) rồi tạo lại CRL. Nginx chỉ đọc CRL khi (re)load, nên sau bước này cần `docker compose exec web nginx -s reload` **chạy trên máy host** (container `client` không có Docker).
- Khi một chứng thư người dùng bị thu hồi (ví dụ giả lập lộ khóa Alice), chạy `05_reissue_user.sh alice Alice alice@lab.local` (hoặc `init_all_pki.sh`): chứng thư cũ được lưu thành `alice_<serial>_revoked.{crt,key}`, cặp khóa + chứng thư mới được cấp. `demo_report.sh tc07b` dùng cặp cũ để chứng minh Nginx chặn chứng thư đã thu hồi.
- Nginx gửi chuỗi đầy đủ (`*.fullchain.crt` = chứng thư lá + Intermediate CA). Nếu chỉ gửi chứng thư lá, trình duyệt chỉ tin Root CA sẽ báo lỗi `unable to get local issuer certificate`.

> **Lưu ý bảo mật:** toàn bộ khóa riêng trong repo chỉ dùng cho bài lab. Không dùng lại ở nơi khác. Container `web` không được mount thư mục `pki/` (nơi chứa khóa Root/Intermediate CA).

---

## 3. Ma Trận Kiểm Thử & Kết Quả Đạt Được (TC01–TC06 chấm 10.0 / 10.0)

| Mã TC | Kịch bản kiểm thử | Công cụ kiểm tra | Kết quả đạt được | Log minh chứng |
|---|---|---|---|---|
| **TC01** | Chuỗi tin cậy (Chain of Trust) | `openssl verify` | `secure.crt: OK` | `artifacts/logs/TC01_chain_verify.log` |
| **TC02** | Dịch vụ HTTPS hợp lệ | `curl`, `openssl s_client` | `HTTP 200 OK` & `Verify return code: 0 (ok)` | `artifacts/logs/TC02_valid_https.log` |
| **TC03** | Xác thực 2 chiều (mTLS) | `curl` (No cert vs Alice cert) | Không cert: `HTTP 400`; Có cert: `HTTP 200` | `artifacts/logs/TC03_mtls_auth.log` |
| **TC04** | Chứng thư hết hạn | `openssl s_client`, `curl` | `verify error:num=10:certificate has expired` | `artifacts/logs/TC04_expired_cert.log` |
| **TC05** | Chứng thư không tin cậy | `openssl s_client`, `curl` | `verify error:num=20:unable to get local issuer` | `artifacts/logs/TC05_untrusted_cert.log` |
| **TC06** | Chứng thư bị thu hồi (CRL) | `openssl verify -crl_check`, `curl` | `verify error:num=23:certificate revoked` | `artifacts/logs/TC06_revoked_crl.log` |
| **TC07** | Nginx kiểm tra CRL cho client cert (mTLS) | `curl` (Bob đã thu hồi vs Alice hợp lệ) | Bob: `HTTP 400` + `error 23` trong log Nginx; Alice: `HTTP 200` | `artifacts/logs/TC07_nginx_mtls_crl.log` |
| **TC08** | Gia hạn chứng thư `api.lab.local` | `04_renew_cert.sh`, `openssl verify` | Serial cũ `superseded` bị từ chối, Serial mới `OK` | `artifacts/logs/TC08_cert_renewal.log` |
| **TC09** | Kiểm tra hồ sơ X.509v3 (CA, server, client, CRL) | `openssl x509 -text`, `openssl crl` | SAN, KU/EKU, `pathlen:0` đúng thiết kế | `artifacts/logs/TC09_cert_profiles_inspection.log` |

---

## 4. Cấu Trúc Thư Mục

```text
ANM_DeTai14_PKI/
├── docker-compose.yml         # Hệ thống dịch vụ cô lập (web, client)
├── docker/client/Dockerfile   # Container kiểm thử tích hợp OpenSSL & cURL
├── pki/
│   ├── config/                # Cấu hình OpenSSL (root-ca, intermediate-ca, server-ext, client-ext)
│   ├── root/                  # Trạng thái Root CA (index, serial, CRL, khóa)
│   ├── intermediate/          # Trạng thái Intermediate CA
│   └── scripts/               # 01_setup_ca, 02_issue_certs, 03_revoke_crl,
│                              # 04_renew_cert, 05_reissue_user, init_all_pki
├── services/nginx/conf.d/     # Virtual Hosts (secure, api, expired, untrusted, revoked)
├── tests/
│   ├── run_all_tests.sh       # TC01 -> TC06
│   ├── run_extended_tests.sh  # TC07 -> TC09
│   ├── demo_report.sh         # In kết quả từng TC để chụp minh chứng
│   └── eval_rubric.sh         # Chấm điểm tự động dựa trên log
├── artifacts/
│   ├── certs/                 # Khóa, chứng thư, fullchain, CA chain, CRL
│   └── logs/                  # Log kết quả kiểm thử (TC01 -> TC09)
├── docs/report/               # Báo cáo và ảnh minh chứng
└── evidence_logs.txt          # Nhật ký lệnh/kết quả dùng làm minh chứng
```
