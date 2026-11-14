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

Chỉ cần chạy tuần tự các lệnh sau từ thư mục gốc dự án:

```bash
# 1. Khởi động môi trường kiểm thử
docker compose up -d client

# 2. Tự động khởi tạo hạ tầng CA, cấp chứng thư và tạo danh sách CRL
docker compose exec client bash /workspace/pki/scripts/init_all_pki.sh

# 3. Khởi chạy Web Server Nginx
docker compose up -d web

# 4. Kiểm tra cấu hình Nginx
docker compose exec web nginx -t

# 5. Chạy toàn bộ 6 kịch bản kiểm thử (TC01 -> TC06)
docker compose exec client bash /workspace/tests/run_all_tests.sh

# 6. Chạy bảng chấm điểm tự động (Eval Rubric 10/10)
docker compose exec client bash /workspace/tests/eval_rubric.sh
```

---

## 3. Ma Trận Kiểm Thử & Kết Quả Đạt Được (10.0 / 10.0)

| Mã TC | Kịch bản kiểm thử | Công cụ kiểm tra | Kết quả đạt được | Log minh chứng |
|---|---|---|---|---|
| **TC01** | Chuỗi tin cậy (Chain of Trust) | `openssl verify` | `secure.crt: OK` | `artifacts/logs/TC01_chain_verify.log` |
| **TC02** | Dịch vụ HTTPS hợp lệ | `curl`, `openssl s_client` | `HTTP 200 OK` & `Verify return code: 0 (ok)` | `artifacts/logs/TC02_valid_https.log` |
| **TC03** | Xác thực 2 chiều (mTLS) | `curl` (No cert vs Alice cert) | Không cert: `HTTP 400`; Có cert: `HTTP 200` | `artifacts/logs/TC03_mtls_auth.log` |
| **TC04** | Chứng thư hết hạn | `openssl s_client`, `curl` | `verify error:num=10:certificate has expired` | `artifacts/logs/TC04_expired_cert.log` |
| **TC05** | Chứng thư không tin cậy | `openssl s_client`, `curl` | `verify error:num=20:unable to get local issuer` | `artifacts/logs/TC05_untrusted_cert.log` |
| **TC06** | Chứng thư bị thu hồi (CRL) | `openssl verify -crl_check`, `curl` | `verify error:num=23:certificate revoked` | `artifacts/logs/TC06_revoked_crl.log` |

---

## 4. Cấu Trúc Thư Mục

```text
ANM_DeTai14_PKI/
├── AGENTS.md                  # Quy chuẩn và hành vi của AI Agent
├── feature-map.md             # Bản đồ định tuyến chứng thư & Nginx vhosts
├── verify-and-eval.md         # Quy chuẩn đánh giá & Rubric 10/10
├── MEMORY.md                  # Sổ tay kỹ thuật xử lý sự cố OpenSSL/Docker
├── docker-compose.yml         # Định nghĩa hệ thống dịch vụ cô lập (web, client)
├── artifacts/
│   ├── certs/                 # Chứa toàn bộ khóa, chứng thư, CA Chain và file CRL
│   └── logs/                  # 6 file log kết quả kiểm thử thực nghiệm
├── docker/
│   └── client/Dockerfile      # Container kiểm thử tích hợp OpenSSL & cURL
├── pki/
│   ├── config/                # Cấu hình OpenSSL (root-ca, inter-ca, server-ext, client-ext)
│   ├── root/                  # Không gian lưu trữ Root CA
│   ├── intermediate/          # Không gian lưu trữ Intermediate CA
│   └── scripts/               # Scripts tự động hóa (01_setup, 02_issue, 03_revoke, init_all)
├── services/
│   └── nginx/conf.d/          # Cấu hình Virtual Hosts (secure, api, expired, untrusted, revoked)
└── tests/
    ├── run_all_tests.sh       # Script thực thi toàn bộ 6 kịch bản kiểm thử
    └── eval_rubric.sh         # Script tự động tính điểm Rubric 10/10
```
