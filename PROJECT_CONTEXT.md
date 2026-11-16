# PROJECT_CONTEXT.md — Master Context Window (`ANM_DeTai14_PKI`)

> **Course:** An ninh Mạng (3 tín chỉ) — Trường ĐH Giao thông vận tải TP.HCM (UTH)  
> **Instructor:** TS. Lê Quốc Tuấn  
> **Topic 14:** Xây dựng PKI thu nhỏ và quản lý vòng đời chứng thư (`Nhóm 14`)  
> **Workspace:** `c:\Users\admin\Downloads\STUDY\ANM\ANM_DeTai14_PKI` (Docker mount: `/workspace`)  
> **Git Baseline:** `3b82eb1` (`Merge pull request #1 from HoangLong8981/fix-pki-chain-and-reissue`)  
> **Audit Snapshot:** `2026-11-16` (synthesized from `#40`–`#44` across Project/Content/Images/Code/Tests)

---

## 1. Project Identity & Current State

### 1.1. Team & Cover Metadata Status
- **Filled & Synchronized (`2026-11-16` update)** in `scripts/generate_docx.py`, `BaoCao_DeTai14_PKI_UTH.docx`, `PROJECT_ANM.docx`, and `README.md`:
  - **Faculty:** `KHOA CÔNG NGHỆ SỐ` — Trường ĐH Giao thông vận tải TP.HCM (UTH)
  - **Group / Class:** `Nhóm 14 — Đề tài 14`, Mã lớp học phần: `012012303804`
  - **Members & 3-Role Assignment:**
    1. **Lô Nguyễn Hoàng Long** (`019206004121`) — `Kiến trúc / chuẩn bị` (PKI theory, 2-tier CA & `pki-net` diagrams, OpenSSL `.cnf`, report editing)
    2. **Nguyễn Minh Hoàng** (`082206001298`) — `Triển khai` (Docker Compose, PKI lifecycle scripts `01`–`05` + `init_all_pki.sh`, cert issuance, 5 Nginx vhosts)
    3. **Phạm Văn Đạt** (`051206011533`) — `Kiểm thử / minh chứng` (Test suites `run_all_tests`, `run_extended_tests`, `demo_report`, `eval_rubric`, logs `TC01–TC09`, 13 screenshots, verification matrix)

### 1.2. Git & Working Tree State
- **Commits (3 total):**
  1. `fb330d5` — Initial Mini-PKI Lab & report (`2026-11-14`)
  2. `69672fd` — Fix: send full cert chain (`*.fullchain.crt`), reissue revoked user cert (`05_reissue_user.sh`), `demo_report.sh tc07b`, remove `./pki` mount on `web` (`2026-11-15`)
  3. `3b82eb1` — Merge PR #1 (`HoangLong8981/fix-pki-chain-and-reissue`)
- **Branches:** `main`, `origin/main`, `origin/fix-pki-chain-and-reissue`.
- **Dirty Working Tree (46 items: 38 modified + 8 untracked, from `2026-11-16 10:32+07` PKI/test run and `20:14+07` `.docx`/PNG rebuild):**
  - **Modified (38):** `BaoCao_DeTai14_PKI_UTH.docx`, `PROJECT_ANM.docx`, `docs/report/BaoCao_DeTai14_PKI_UTH.docx`, `docs/report/PROJECT_ANM.docx`, 9 PNGs (`docs/report/images/image{1,2,4,5,6,7,9,10,12}.png`), 8 logs (`artifacts/logs/TC0{2,3,4,5,6,8,9}*.log`), `artifacts/certs/{alice.crt,alice.key,ca-chain.crl.pem,inter.crl.pem,root.crl.pem}`, `pki/intermediate/{certs/alice.crt,crl/inter.crl.pem,crlnumber*,csr/alice.csr,index.txt*,private/alice.key,serial*}`, `pki/root/{crl/root.crl.pem,crlnumber*}`.
  - **Untracked (8):** `artifacts/certs/{alice_1002_revoked.{crt,key},api.fullchain.crt,secure.fullchain.crt}`, `artifacts/logs/TC07_post_revocation_check.log`, `pki/intermediate/{certs/alice_1002_revoked.crt,newcerts/1007.pem,private/alice_1002_revoked.key}`.
- **Key Runtime Facts (Working Tree vs Stale Docs):**
  - `alice.crt` was reissued via `05_reissue_user.sh`: **active `alice.crt` is Serial `1007`** (`V`, `Nov 16 03:32:17 2026–2027`); revoked `1002` is archived as `alice_1002_revoked.{crt,key}`.
  - Current **`.key` count = 19** (`1` root + `10` intermediate + `8` artifacts/certs; stale docs still say `17`).
  - Current CRLs (valid until `Dec 16 2026 GMT`): `root.crl.pem` **CRL #4097** (`0` revoked), `inter.crl.pem` **CRL #4102** (revoked: `1001, 1002, 1004, 1005`), `ca-chain.crl.pem` SHA-256 `eed5c4997772aec821aaff8a654676ca73647c5d04cde3e18c529c9f05b50582` (stale docs say `4096`/`4100`/`daf93b27...`).
  - **Clean-clone blocker in `3b82eb1`:** `secure.fullchain.crt` and `api.fullchain.crt` are NOT committed in `HEAD`, yet `secure.conf` & `api.conf` reference them (`docker compose up -d` on fresh clone crash-loops `web` until `init_all_pki.sh` runs).

---

## 2. Quick Architecture & File Map

### 2.1. Runtime Topology (`docker-compose.yml`, bridge network `pki-net`)
- **`pki-web` (`nginx:1.27-alpine` / `nginx/1.27.5`):** Port `8443:443`. Mounts `./services/nginx/conf.d:ro`, `./services/nginx/html:ro`, `./artifacts/certs:ro` (does NOT mount `./pki`). Aliases: `secure.lab.local`, `api.lab.local`, `expired.lab.local`, `untrusted.lab.local`, `revoked.lab.local`.
- **`pki-client` (`docker/client/Dockerfile` — `alpine:3.20`):** Packages `bash curl openssl coreutils grep sed`; OpenSSL `3.3.7`, cURL `8.14.1`. Mounts `.:/workspace`. Runs PKI lifecycle scripts and test suites.

### 2.2. Certificate & Serial Registry (`pki/intermediate/index.txt` — 8 entries)
| Entity / File | Role / Domain | Serial | Status (`index.txt`) | Validity / Key Facts |
|---|---|---|---|---|
| `root-ca.crt` | `UTH Root CA` (Trust Anchor) | `052AEA4DDC6A7F1B...FB4765BE` | Self-signed | RSA 4096-bit, `CA:TRUE`, `Nov 5 2026–Nov 2 2036 GMT` |
| `inter-ca.crt` | `UTH Intermediate CA` | `1000` (Root DB) | `V` | RSA 2048-bit, `CA:TRUE, pathlen:0`, `Nov 5 2026–Nov 4 2031 GMT` |
| `secure.crt` (+ `.fullchain.crt`) | Service 1: `secure.lab.local` | `1000` (Inter DB) | `V` | `serverAuth`, SAN: `DNS:secure.lab.local, DNS:localhost, IP:127.0.0.1` |
| `api_old.crt` | Old Service 2 (`api.lab.local`) | `1001` | `R` (`superseded`) | Revoked during `04_renew_cert.sh` -> `error 23` |
| `alice_1002_revoked.crt` | Archived revoked Alice | `1002` | `R` (`keyCompromise`) | Tested via `demo_report.sh tc07b` -> `400` / `error 23` |
| `expired.crt` | Expired service (`expired.lab.local`) | `1003` | `V` (expired date) | `Jan 1–Jan 2 2020 GMT` -> `error 10` |
| `revoked.crt` | Revoked service (`revoked.lab.local`) | `1004` | `R` (`keyCompromise`) | Client CRL check (TC06) -> `error 23` |
| `bob.crt` | Revoked User 2 (`Bob`) | `1005` | `R` (`keyCompromise`) | Server mTLS CRL check (TC07) -> `400` / `error 23` |
| `api.crt` (+ `.fullchain.crt`) | Service 2: `api.lab.local` (Renewed) | `1006` | `V` (730d) | `Nov 14 2026–Nov 13 2028 GMT`, SAN: `DNS:api.lab.local, localhost, 127.0.0.1` |
| `alice.crt` | Valid User 1 (`Alice`, Reissued) | `1007` | `V` (365d) | `Nov 16 2026–Nov 16 2027 GMT`, `clientAuth`, no SAN -> `200 OK` |
| `untrusted.crt` | Rogue CA test (`untrusted.lab.local`) | `26EC0F9C...59068065` | Rogue self-signed | Issuer `CN=Rogue Root CA` -> `error 20` |

### 2.3. Complete Directory & File Map
| Path | Purpose & Contents |
|---|---|
| `docker-compose.yml`, `docker/client/Dockerfile` | Isolated Docker stack (`web`, `client`, `pki-net`). |
| `pki/config/` | `root-ca.cnf`, `intermediate-ca.cnf`, plus unused `server-ext.cnf`, `client-ext.cnf`. |
| `pki/root/` | Root CA state (`certs/root-ca.crt`, `private/root-ca.key`, `crl/root.crl.pem`, `newcerts/1000.pem`, `index.txt`, `serial`, `crlnumber`). |
| `pki/intermediate/` | Intermediate CA state (`certs/`, `private/`, `csr/`, `crl/inter.crl.pem`, `newcerts/1000..1007.pem`, `index.txt`, `serial`, `crlnumber`). |
| `pki/scripts/` | `init_all_pki.sh` orchestrator; `01_setup_ca.sh`, `02_issue_certs.sh`, `03_revoke_crl.sh`, `04_renew_cert.sh`, `05_reissue_user.sh`. |
| `services/nginx/conf.d/` | 5 Virtual Hosts: `secure.conf` (`*.fullchain.crt`), `api.conf` (`*.fullchain.crt` + mTLS + `ssl_crl ca-chain.crl.pem`), `expired.conf`, `untrusted.conf`, `revoked.conf`. |
| `services/nginx/html/index.html` | Unused HTML page (mounted in `docker-compose.yml:18`, shadowed by `return 200` in all vhosts). |
| `tests/` | `run_all_tests.sh` (TC01–TC06), `run_extended_tests.sh` (TC07–TC09), `eval_rubric.sh` (10/10 grader on TC01–TC06 logs), `demo_report.sh` (interactive CLI demo menu). |
| `artifacts/certs/` | Exported cert/key/CRL bundle (24 files: leaf certs, 8 `.key` files, `root-ca.crt`, `inter-ca.crt`, `ca-chain.crt`, `{secure,api}.fullchain.crt`, `root.crl.pem`, `inter.crl.pem`, `ca-chain.crl.pem`, `alice_1002_revoked.{crt,key}`). |
| `artifacts/logs/` | 10 logs: `TC01_chain_verify.log` .. `TC06_revoked_crl.log`, `TC07_nginx_mtls_crl.log` (stale 14/11), `TC07_post_revocation_check.log` (current 16/11), `TC08_cert_renewal.log`, `TC09_cert_profiles_inspection.log`. |
| `scripts/` | `generate_docx.py` (generates both `.docx` files), `generate_diagrams.py` (generates `arch_diagram.png` & `lifecycle_diagram.png`), `generate_evidence_screenshots.py`. |
| `docs/report/` | Canonical location for `BaoCao_DeTai14_PKI_UTH.docx`, `PROJECT_ANM.docx`, and `images/` (13 screenshots + 2 diagrams). |
| Root Docs & Metadata | `README.md`, `PROJECT_CONTEXT.md`, `evidence_logs.txt`, `.gitignore`, `.gitattributes`. *(Antigravity skill/agent files removed).* |
| `.vscode/settings.json` | Office viewer association (`cweijan.officeViewer`). |

### 2.4. Exact Duplicate Files Map (Byte-for-Byte Identical SHA-256)
- `BaoCao_DeTai14_PKI_UTH.docx` == `docs/report/BaoCao_DeTai14_PKI_UTH.docx`
- `PROJECT_ANM.docx` == `docs/report/PROJECT_ANM.docx`
*(Duplicate `.agent/`, `.agents/`, `skills/`, `verify-and-eval.md` were removed).*

---

## 3. Status Matrix Across Domains

### 3.1. Nội dung & Báo cáo (`generate_docx.py`, `.docx`, Markdown docs)
| Phần đã ổn | Phần cần sửa / bổ sung |
|---|---|
| - Report covers 2-tier CA, `TBSCertificate` equations `(1)–(4)`, RA/CSR, `TABLE I` (X.509v3), `TABLE II` (5-criteria CRL vs OCSP), 3-level key compromise + 5-step response, TLS 1.3 linkage, and correctly notes SAN is X.509v3/HTTPS rule (not TLS 1.3-only) & Docker `pki/root/` simulation vs physical offline/HSM.<br>- `word/document.xml` of both `.docx` matches `scripts/generate_docx.py` 100%.<br>- `README.md` documents PR #1 workflow (`client` -> `init_all_pki.sh` -> `web`, `*.fullchain.crt`, `05_reissue_user.sh`, `tc07b`).<br>- `MEMORY.md` captures CRLF, `.key` perms, `X509_V_FLAG_CRL_CHECK_ALL` (`ca-chain.crl.pem`), `unique_subject=no`, and OpenSSL CRL flags. | - **Outdated vs PR #1 & `11/16` state (`generate_docx.py`):** snippets `secure.conf`/`api.conf` (`1158,1181`) print `secure.crt`/`api.crt` instead of `*.fullchain.crt`; omits `05_reissue_user.sh`, `tc07b`, `TC07`–`TC09`; hardcodes `alice`=`1002` revoked (now `1007` valid), `17` `.key` files (now `19`), CRL `#4100/#4096` (now `#4102/#4097`), SHA-256 `daf93b27` (now `eed5c499`), and old `s_client` `1629 bytes` log (`1249-1262`).<br>- **Technical & IEEE errors (`generate_docx.py`):** wrong Windows warning explanation (`55,1271-1273`: `DNS:localhost` IS in SAN; root cause is untrusted `root-ca.crt` / Avast interception); wrong flag `s_client -CRLfile` (`1328`); `III.A.1` (`981-998`) omits CRL creation; `TABLE III` (`1125`) lacks prior in-text citation; `Fig. X:` (`389`) uses colon instead of period.<br>- **Refs & Theory gaps:** `[1]` Stallings `2017` & `[2]` Stallings & Brown `2012` instead of `2021`/`2023`; `[3, tr. 53, 99]` cites wrong slide page (`53` has TLS ciphers/PFS, SAN is on `56, 99`); `missing_sections.md:318` strict `[1]–[3]` whitelist conflicts with citing core vs extended docs; missing dedicated Asymmetric Crypto/Keys foundation & explicit `Limitations` section.<br>- **Markdown drift:** `AGENTS.md:56` has unclosed `mermaid` fence (`---` swallows sections 3–5), wrong container `client-tester`, wrong `ssl_crl` arrow, missing `04_renew`/`05_reissue`/`TC07-09`; `README.md:78` points TC07 to stale `TC07_nginx_mtls_crl.log`, omits `Bob` (`19`) & root/script files (`87-106`); `MEMORY.md` numbering out of order (`1.1..1.3, 1.8, 1.4..1.7`); `feature-map.md`, `verify-and-eval.md` outdated & CRLF (`verify-and-eval.md:23` falsely claims Nginx blocks `revoked.lab.local`); `evidence_logs.txt` & `missing_sections.md` retain internal `Worker 1/2` / `Ghi chú biên tập` notes. |

### 3.2. Hình ảnh & Minh chứng (`docs/report/images/` & `generate_evidence_screenshots.py`)
| Phần đã ổn | Phần cần sửa / bổ sung |
|---|---|
| - All 4 `.docx` files embed 13 PNGs matching `docs/report/images/image1..13.png` 100% by SHA-256. Zero leftover Markov images.<br>- **12 images verified OK (`2026-11-16` update):** `image1.png` (Fig. 10, `TC04`), `image2.png` (Fig. 11, `TC05`), `image3.png` (Fig. 13, `eval_rubric` 10/10), `image4.png` (Fig. 12, `TC06` with top command & `ẢNH 6` banner), `image5.png` (Fig. 3, `TC01`), `image6.png` (Fig. 4, `TC02` curl), `image7.png` (Fig. 1, `secure.crt` X.509/SAN), `image8.png` (Fig. 7, browser cert details matching `secure.crt` SHA-256), `image9.png` (Fig. 6, zoomed Windows browser `https://localhost:8443`), `image11.png` (Fig. 2, live `index.txt` 8 entries `1000..1007` + 19 `.key` mode `600`), `image12.png` (Fig. 5, full `s_client -tls1_3` with command, `depth=2..0`, 2-cert chain `2888 bytes`, `Verify return code: 0`), `image13.png` (Fig. 9, `demo_report.sh tc07b` blocking `alice_1002_revoked.crt` with `400` + `error 23`).<br>- `image10.png` (Fig. 8, `TC03` live `serial: 1007`): now synced with `generate_docx.py` captions, `image11.png`, and `image13.png`. | - **`image10.png` (Fig. 8, `TC03`):** Valid content & synced with report, though full `1920x1020` screen (could optionally be cropped tighter for larger Word font).<br>- **`image9.png` (Fig. 6):** Zoomed and readable, though Cốc Cốc bookmark/sidebar icons remain visible.<br>- **Missing visuals:** **Zero Architecture / Lifecycle Diagrams**; optional screenshots for `api.crt` (`1006`), `alice.crt` (`1007`), `tc07` (Bob `1005`), `tc08` (Renewal).<br>- `scripts/generate_evidence_screenshots.py`: hardcodes Windows font `C:/Windows/Fonts/consola.ttf`, local user path `PS C:\Users\admin\...`, and fixed line slices in `evidence_logs.txt` (do not overwrite `image11/12/13` with it unless `evidence_logs.txt` & parser are updated). |

### 3.3. Mã nguồn & Cấu hình (`pki/`, `services/`, `docker/`, `tests/`, `scripts/`)
| Phần đã ổn | Phần cần sửa / bổ sung |
|---|---|
| - `root-ca.cnf` & `intermediate-ca.cnf` enforce 4096/2048-bit RSA, SHA-256, `CA:true`, `pathlen:0`, `unique_subject=no`, CRL `AKI`. All `.sh/.cnf/.conf/.py/.yml/.html` are LF; `bash -n` 10/10 & `py_compile` 2/2 pass.<br>- `01_setup_ca.sh` & `05_reissue_user.sh` build chains cleanly & archive revoked user certs idempotently.<br>- `secure.conf` & `api.conf` serve `*.fullchain.crt`; `api.conf` properly sets `ssl_verify_depth 2`, `ssl_crl ca-chain.crl.pem`, `error_log ... info`.<br>- `docker-compose.yml` isolates `./pki` away from `web`. | - **CA/OpenSSL configs:** `root-ca.cnf:19` `crl = root-ca.crl` mismatches scripts (`root.crl.pem`); `policy_strict` (`30-36`) omits `localityName` (drops `L=Ho Chi Minh City` from `inter-ca.crt`); hardcoded `/workspace`; dead `[ server_cert ]`/`[ usr_cert ]`/`server-ext.cnf`/`client-ext.cnf` (missing `subjectAltName`, `crlDistributionPoints`); obsolete `RANDFILE`/`nsCertType`.<br>- **PKI scripts:** `02_issue_certs.sh` copies `.key` to `artifacts/certs/` without `-p` or `chmod 600`; `03_revoke_crl.sh:44-48` & `04_renew_cert.sh:76` skip regenerating `root.crl.pem` (breaks Nginx mTLS after 30d CRL expiry); `04_renew_cert.sh` hides errors via `>/dev/null` + `|| true` and fails to save `api_old.key`; `/tmp` files (including `/tmp/rogue-ca.key` without `600`) lack `trap` cleanup; `awk` on `index.txt` lacks `-F'\t'`; `01_setup_ca.sh` checks `.key`/`.crt` independently; `init_all_pki.sh` doesn't normalize `*.conf` or warn to reload `web`.<br>- **Nginx/Docker:** `expired.conf:5` & `revoked.conf:5` serve leaf-only instead of `fullchain` (Root-only clients hit `num=20` before `10`/`23`); `ssl_ciphers HIGH:!aNULL:!MD5;` allows legacy TLS 1.2 ciphers; raw `$ssl_client_s_dn` in JSON (`api.conf:26`); dead `html/index.html`; `docker-compose.yml` lacks `healthcheck` & cert-ready guard for `web` and exposes test `.key` files via `artifacts/certs` mount. |

### 3.4. Kiểm thử & Môi trường (`tests/*.sh` & Live Docker Stack)
| Phần đã ổn | Phần cần sửa / bổ sung |
|---|---|
| - Docker Desktop `29.9.2` / WSL2 running; `pki-web` & `pki-client` healthy.<br>- `nginx -t` exit `0`; `.key` files in `artifacts/certs/` all `600`; CRLs valid until `Dec 16 2026 GMT`.<br>- Live runs in `pki-client` ALL exited `0` (`2026-11-16`): `run_all_tests.sh` (`TC01` OK, `TC02` TLS 1.3 2-cert chain `Verify return code: 0`, `TC03` 400 vs 200 `1007`, `TC04` `num=10`, `TC05` `num=20`, `TC06` `num=23`), `run_extended_tests.sh` (`TC08` `1001` revoked vs `1006` OK, `TC07` Bob `400` vs Alice `200`, `TC09` profiles), `eval_rubric.sh` **10/10.0**, `demo_report.sh all` exit `0` (including `tc07b` + `docker logs pki-web` showing `error 23` for Bob `1005` & old Alice `1002`). | - **Test suite false-positives:** `run_all_tests.sh` puts `\|\| true` on every check (always exits `0`), TC01 omits `api`/`alice`, TC06 uses `inter.crl.pem` + `-crl_check` instead of `ca-chain.crl.pem` + `-crl_check_all`.<br>- `eval_rubric.sh`: grades stale logs without running tests or checking freshness; CRLF check skips `.cnf/.conf/.yml/.md`; `.key` check ignores `pki/*/private/*.key`, allows `700`, masks `stat` failure; `TC01` `grep "OK"` matches `"NOT OK"`; `TC03` ignores order; skips `curl: (60)`, `TC07`–`TC09`.<br>- `run_extended_tests.sh`: `TC08` tests `api.lab.local` before `nginx -s reload`; `TC07` writes `TC07_post_revocation_check.log` (untracked) instead of `TC07_nginx_mtls_crl.log` and doesn't assert `400`/`200`.<br>- `demo_report.sh`: `set -euo pipefail` aborts if `grep` misses (`tc02/04/05/06`) or `TC08` log absent; `tc05` omits `num=18`; `tc07b` `ls \| head -n1` picks oldest archive.<br>- **Windows Host Loopback Caveat:** Host `curl.exe` exits `60` (`schannel: chain incomplete`) and host OpenSSL on `127.0.0.1:8443` receives a single cert from `CN=Avast Web/Mail Shield Untrusted Root` (`Verify return code: 21`) due to **Avast Web/Mail Shield TLS interception** on Windows loopback; inside Docker (`pki-client` -> `pki-web`), Nginx serves the real 2-cert `fullchain`. |

### 3.5. Yêu cầu & Sản phẩm Đề tài 14 (PDF p.2 & p.8)
| Hạng mục Yêu cầu | Trạng thái | Chi tiết thiếu / cần xử lý |
|---|---|---|
| Nhóm 3 SV & 3 vai trò | **ỔN** | Đã điền bìa (`KHOA CÔNG NGHỆ SỐ`, `012012303804`) và bảng phân công 3 vai trò trong `generate_docx.py` & `README.md`. |
| (a) Báo cáo | **ỔN** | Đã đồng bộ PR #1, bổ sung Mật mã bất đối xứng, Giới hạn thực nghiệm, `TABLE III` (`bob`/`untrusted`), refs `[1]`–`[3]` theo đề cương UTH. |
| (b) Sơ đồ kiến trúc | **ỔN** | Đã tạo `arch_diagram.png` & `lifecycle_diagram.png` (`scripts/generate_diagrams.py`), nhúng vào báo cáo; đã đóng Mermaid fence ở `AGENTS.md`. |
| (c) Mã nguồn / cấu hình | **ỔN (đã vá P1)** | Đã vá `root-ca.cnf`, `02_issue_certs.sh` (`chmod 600` + `trap`), `03_revoke_crl.sh` / `04_renew_cert.sh` (tái xuất `root.crl.pem`), `eval_rubric.sh`, `run_extended_tests.sh`, `demo_report.sh`. *(Còn P2/P0 clean-clone `*.fullchain.crt` chưa commit).* |
| (d) Dataset / Evidence logs | **CẦN ĐỒNG BỘ** | `TC01–09` & `TC07_nginx_mtls_crl.log` đã đồng bộ `16/11`; riêng `evidence_logs.txt` vẫn là snapshot cũ `14/11`. |
| (e) Kịch bản Demo | **CHƯA ĐỦ** | `demo_report.sh` đã vá lỗi `grep` & `ls -t`; vẫn thiếu tài liệu runbook trình diễn trực tiếp đầy đủ (host commands, browser, 3 vai trò, sự cố). |
| (f) Video dự phòng | **THIẾU HOÀN TOÀN** | 0 file video (`.mp4/.mkv/.webm`) hoặc liên kết video dự phòng trong repo/báo cáo. |
| Quan sát vs Kết luận vs Giới hạn & Metrics | **ỔN (còn metric)** | Đã thêm mục `IV.C. Giới hạn Thực nghiệm` và chú thích so sánh lý thuyết `TABLE II`; `TABLE IV` chưa thêm `TC07` (Bob)/`TC08`/`TC09` và số đo latency/bytes. |
| Lý thuyết & Tham khảo Đề tài 14 | **ỔN** | Đã thêm mục nền tảng Mật mã bất đối xứng/khóa công khai-riêng; giữ đúng `[1]`–`[3]` theo đề cương UTH (`2021`, `5th ed. 2023`, `Khoa Công nghệ Số 2026`). |

---

## 4. Prioritized Actionable Fix Checklist

### P0 — Blockers (Course Deliverables, Clean-Clone Boot, Hard Contradictions)
- [x] **Fill team metadata & 3-role assignment** (`scripts/generate_docx.py`, `README.md`): Filled `KHOA CÔNG NGHỆ SỐ`, class `012012303804`, Nhóm 14 members/MSSV, and added the 3-role breakdown table.
- [x] **Create & embed Architecture + Lifecycle Diagrams** (`scripts/generate_diagrams.py`, `docs/report/images/{arch_diagram,lifecycle_diagram}.png`, `scripts/generate_docx.py`): Generated both diagrams and embedded as `Sơ đồ 1` and `Sơ đồ 2` in `BaoCao_DeTai14_PKI_UTH.docx`.
- [ ] **Deliver full Live Demo Runbook & Backup Video** (`DEMO_SCRIPT.md` or `README.md` + video file/link): Document end-to-end presenter sequence (`docker compose up` -> `init_all_pki.sh` -> `nginx -s reload` -> `demo_report.sh` -> `04_renew`/`05_reissue` -> browser `localhost:8443` accounting for Avast shield -> speaker split) and record backup video.
- [ ] **Fix clean-clone Nginx crash-loop & working tree drift** (`3b82eb1`): Ensure `artifacts/certs/{secure,api}.fullchain.crt` are tracked or auto-generated before `web` starts (`docker-compose.yml` / `README.md`), and reconcile uncommitted changes into a clean commit state.
- [x] **Eliminate report vs screenshot/state contradictions** (`scripts/generate_docx.py` & `docs/report/images/`): Synced `generate_docx.py` snippets (`*.fullchain.crt`), `alice` Serial (`1007` + `alice_1002_revoked`), `.key` count (`19`), CRL numbers (`4102/4097`), SHA-256 (`eed5c499...`), `s_client` log (`2888 bytes`), `05_reissue_user.sh` + `tc07b`, and regenerated `.docx` files.

### P1 — High (Theory, References, Stale Images, Script & Test Bugs)
- [x] **Update references to `[1]–[3]` per UTH PDF** (`scripts/generate_docx.py`): Updated `[1]` Stallings (**2021**), `[2]` Stallings & Brown (**5th ed., 2023**), `[3]` TS. Lê Quốc Tuấn (**Khoa Công nghệ Số**, 2026), kept strictly `[1]–[3]` without external `[4]–[6]`, and fixed `[3, tr. 56, 99]` for SAN. *(Note: `missing_sections.md` remains an unedited draft).*
- [x] **Complete required theory, Limitations, Diagrams, and Table III** (`scripts/generate_docx.py`): Added Asymmetric Cryptography & Public/Private Keys subsection in `II.A`, `Sơ đồ 1` & `Sơ đồ 2`, theoretical comparison note in `TABLE II`, `bob` & `untrusted` in `TABLE III`, `III.A.1` CRL commands, `Fig. X.` period punctuation, and dedicated `IV.C. Giới hạn Thực nghiệm`. *(Optional remaining: add `TC07` Bob / `TC08` / `TC09` + quantitative latency/size metrics to `TABLE IV`).*
- [x] **Regenerate stale/cropped screenshots (`image4`, `image9`, `image11`, `image12`, `image13`)** (`docs/report/images/`): Updated `image4.png`, `image9.png`, `image11.png`, `image12.png`, `image13.png`, and embedded into all `.docx`. *(Optional extra screenshots remaining: `api.crt`, `alice.crt`, `tc07`, `tc08`; optional tighter crop on `image10` & `image9` sidebar).*
- [x] **Fix PKI script security & CRL expiry bugs:**
  - `pki/scripts/02_issue_certs.sh`: added `trap` cleanup for `/tmp/*`, `chmod 600` on `/tmp/rogue-ca.key` and after every `cp` to `artifacts/certs/*.key`.
  - `pki/scripts/03_revoke_crl.sh` & `04_renew_cert.sh`: always regenerate `root.crl.pem` & copy to `artifacts/certs/` before `ca-chain.crl.pem`.
  - *(Remaining optional item: `services/nginx/conf.d/expired.conf:5` & `revoked.conf:5` still serve leaf cert instead of `*.fullchain.crt`).*
- [x] **Fix P1 test & config bugs (`tests/*.sh`, `root-ca.cnf`):**
  - `tests/eval_rubric.sh`: added `.cnf`/`.conf` to CRLF check, checked `600/400` strictly across `pki/root/private/*.key`, `pki/intermediate/private/*.key`, `artifacts/certs/*.key`, and anchored `TC01` (`: OK$`). *(Passed `10 / 10.0`).*
  - `tests/run_extended_tests.sh`: synced `TC07_post_revocation_check.log` -> `TC07_nginx_mtls_crl.log`.
  - `tests/demo_report.sh`: added `|| true` to `grep` pipes (`tc02/04/05/06`), matched `num=(18|20)` (`tc05`), used `ls -t` (`tc07b`).
  - `pki/config/root-ca.cnf`: fixed `crl = $dir/crl/root.crl.pem` and added `localityName = optional` in `policy_strict`.
  - *(Remaining optional test hardening: `tests/run_all_tests.sh` `|| true` & `-crl_check_all` in `TC06`, `eval_rubric.sh` live freshness / `TC03` order / `TC07`–`TC09`).*

### P2 — Medium (Config/Script Hardening, Supporting Docs Sync)
- [ ] **Clean up remaining OpenSSL configs (`pki/config/*.cnf`):** Remove or wire dead `server-ext.cnf`/`client-ext.cnf`/`[ server_cert ]`/`[ usr_cert ]`, remove legacy `RANDFILE`/`nsCertType`, consider `crlDistributionPoints`, avoid hardcoded `/workspace`.
- [ ] **Harden PKI & Python scripts:** Check `.key`+`.crt` atomically (`01_setup_ca.sh:39-76`); stop swallowing `04_renew_cert.sh` errors & save `api_old.key`; copy archive from `${CRT}` & parameterize `OU` (`05:33,52`); fix `init_all_pki.sh` to cover `*.conf` & remind Nginx reload; refactor `scripts/generate_evidence_screenshots.py`. *(Done: `awk -F'\t'` applied in `03_revoke_crl.sh` and `05_reissue_user.sh`).*
- [ ] **Harden Nginx & Docker (`services/nginx/`, `docker-compose.yml`):** Enforce TLS 1.2 AEAD/PFS `ssl_ciphers` (`secure.conf:15-16`, `api.conf:16`), sanitize `$ssl_client_s_dn` in JSON (`api.conf:26`), remove or serve unused `services/nginx/html/index.html`, add `healthcheck:` & cert-ready guard for `web`, and avoid mounting private keys into `web`.
- [ ] **Sync remaining Markdown/Log docs:**
  - `README.md`: **(Done)** added Nhóm 14 3-member table (`KHOA CÔNG NGHỆ SỐ`, `012012303804`). *(Remaining: mention `Bob`, update directory tree, document `8443:443` & Avast loopback caveat).*
  - `evidence_logs.txt`: regenerate verbatim from post-PR#1 commands and strip internal `Worker 1 / Worker 2` comments (`7-8`).

### P3 — Cleanup & Repo Hygiene
- [x] **Remove Antigravity skill/agent scaffolding:** Removed `.agent/`, `.agents/`, `skills/`, `verify-and-eval.md`, `AGENTS.md`, `feature-map.md`, `MEMORY.md`, and `missing_sections.md`.
- [ ] **Tighten `.gitignore` & Python hygiene:** Add `*.old` (OpenSSL backup files) and decide `.vscode/` policy; remove unused `import os` in `scripts/generate_docx.py:1`; optionally deduplicate root `*.docx` vs `docs/report/*.docx`.

---

## 5. Quick Commands & Entry Points

> Run from `c:\Users\admin\Downloads\STUDY\ANM\ANM_DeTai14_PKI` (Docker Desktop + WSL2 running).

### 5.1. Docker Stack & Nginx
```powershell
docker compose up -d client
docker compose exec client bash /workspace/pki/scripts/init_all_pki.sh
docker compose up -d web
docker compose exec web nginx -t
docker compose exec web nginx -s reload
docker compose logs --tail 40 web
```

### 5.2. PKI Lifecycle & OpenSSL Verification (inside `pki-client`)
```bash
docker compose exec client bash /workspace/pki/scripts/04_renew_cert.sh
docker compose exec client bash /workspace/pki/scripts/05_reissue_user.sh alice Alice alice@lab.local
docker compose exec client openssl verify -crl_check_all -CAfile /workspace/artifacts/certs/ca-chain.crt -CRLfile /workspace/artifacts/certs/ca-chain.crl.pem /workspace/artifacts/certs/secure.crt /workspace/artifacts/certs/api.crt /workspace/artifacts/certs/alice.crt
docker compose exec client openssl crl -in /workspace/artifacts/certs/inter.crl.pem -noout -text
```

### 5.3. Test Suites & Demo Menu (inside `pki-client`)
```bash
docker compose exec client bash /workspace/tests/run_all_tests.sh
docker compose exec client bash /workspace/tests/run_extended_tests.sh
docker compose exec web nginx -s reload
docker compose exec client bash /workspace/tests/eval_rubric.sh
docker compose exec client bash /workspace/tests/demo_report.sh all   # or tc01..tc08|tc07b|cert
```

### 5.4. Report & Screenshot Generation (Windows Host Python)
```powershell
python -m py_compile scripts/generate_docx.py scripts/generate_evidence_screenshots.py
python scripts/generate_docx.py
# (Only after updating evidence_logs.txt & fixing hardcoded paths/slices):
python scripts/generate_evidence_screenshots.py
```

### 5.5. Hygiene & Static Checks
```powershell
git status -s
docker compose exec client bash -n /workspace/pki/scripts/*.sh /workspace/tests/*.sh
docker compose exec client grep -l -U $'\r' /workspace/pki/scripts/*.sh /workspace/tests/*.sh /workspace/pki/config/*.cnf /workspace/services/nginx/conf.d/*.conf
python -c "import pathlib; print([p.as_posix() for p in pathlib.Path('.').rglob('*.md') if b'\r\n' in p.read_bytes()])"
docker compose exec client stat -c "%a %n" /workspace/pki/root/private/*.key /workspace/pki/intermediate/private/*.key /workspace/artifacts/certs/*.key
```
