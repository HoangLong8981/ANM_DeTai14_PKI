# TÀI LIỆU BỔ SUNG LÝ THUYẾT & QUY TRÌNH OPENSSL (ĐỀ TÀI 14: PKI)

> **Ghi chú biên tập**: Tài liệu này được soạn thảo theo văn phong kỹ thuật chuẩn IEEE bằng tiếng Việt học thuật, đồng bộ hoàn toàn với cấu hình PKI trong `pki/scripts/`, `pki/config/` và bằng chứng kiểm thử thực tế tại `evidence_logs.txt` (môi trường Docker Compose gồm hai container Linux Alpine `pki-client` và `pki-web` chạy trên nền hệ điều hành Windows).

---

## 1. Vòng đời PKI, vai trò RA/CSR và quy trình lệnh OpenSSL thực tế

### 1.1. Vai trò của Registration Authority (RA) và cơ chế CSR

Trong kiến trúc hạ tầng khóa công khai (PKI) theo chuẩn X.509 [1, Mục 4.6], [3, Mục 3.3.1–3.3.5], chức năng cấp phát chứng thư được tách biệt nhằm hạn chế rủi ro tập trung quyền lực tại một điểm duy nhất:

- **Registration Authority (RA)**: Đảm nhiệm vai trò tiếp nhận yêu cầu cấp chứng thư từ thực thể đầu cuối và thực hiện quy trình **xác minh danh tính (Identity Validation)** trước khi chuyển yêu cầu sang Certificate Authority (CA) phê duyệt ký [1, Mục 4.6], [2, Mục 23.3], [3, Mục 3.3.3]. Đối với chứng thư máy chủ (Server Certificate), RA kiểm tra tính hợp lệ của thông tin định danh dịch vụ và tên miền gắn trong trường Subject Alternative Name (SAN); đối với chứng thư người dùng (Client Certificate), RA đối chiếu hồ sơ cá nhân, địa chỉ thư điện tử (`emailAddress`), phạm vi sử dụng khóa (`KeyUsage`, `ExtendedKeyUsage`) và thẩm quyền truy cập hệ thống [3, Mục 3.3.2–3.3.3].
- **Certificate Signing Request (CSR)**: Sau khi thực thể tự sinh cặp khóa trên thiết bị của mình, thực thể đóng gói khóa công khai (Public Key), thông tin định danh (`Subject DN`) và các thuộc tính yêu cầu thành một tệp CSR để gửi tới RA/CA. Tệp CSR được chính thực thể tự ký bằng khóa riêng (Private Key) tương ứng để chứng minh quyền sở hữu khóa hợp lệ, bảo đảm khóa riêng không bao giờ rời khỏi thực thể xin cấp phát [1, Mục 4.6], [3, Mục 3.3.1–3.3.2].
- **Áp dụng trong mô hình triển khai nhỏ / Lab thực nghiệm**: Trong phạm vi triển khai thực nghiệm của đồ án (`ANM_DeTai14_PKI`), hệ thống không tách riêng một máy chủ RA độc lập qua giao thức đăng ký trực tuyến. Thay vào đó, chức năng RA được thực hiện về mặt logic bởi quản trị viên hệ thống thông qua bước rà soát cấu hình định danh, chính sách trường thuộc tính (`policy_strict` trong `root-ca.cnf`, `policy_loose` trong `intermediate-ca.cnf`) và nội dung tệp mở rộng X.509v3 trước khi phê duyệt ký bằng lệnh `openssl ca` ở chế độ không tương tác (`-batch`).

### 1.2. Bộ lệnh OpenSSL đầy đủ qua các pha vòng đời trong Lab

Toàn bộ các thao tác mật mã trong bài thực nghiệm được thực thi bên trong container `pki-client` trên thư mục làm việc `/workspace`.

#### (a) Khởi tạo Root CA (Root CA Setup)

Cấu trúc cơ sở dữ liệu tối thiểu của Root CA được thiết lập tại `/workspace/pki/root/` với quyền thư mục khóa riêng `700`, tệp chỉ mục `index.txt`, bộ đếm số sê-ri `serial` (khởi tạo `1000`) và bộ đếm `crlnumber` (`1000`). Root CA sử dụng khóa RSA 4096-bit bảo vệ với quyền `600`, chứng thư tự ký có hiệu lực 3650 ngày (10 năm) theo hồ sơ mở rộng `v3_ca` (`basicConstraints = critical, CA:true`; `keyUsage = critical, digitalSignature, cRLSign, keyCertSign`):

```bash
# Chuẩn bị thư mục và cơ sở dữ liệu Root CA
mkdir -p /workspace/pki/root/{certs,private,newcerts,crl}
chmod 700 /workspace/pki/root/private
touch /workspace/pki/root/index.txt
echo 1000 > /workspace/pki/root/serial
echo 1000 > /workspace/pki/root/crlnumber

# 1. Sinh khóa riêng Root CA (RSA 4096-bit) và siết quyền tệp
openssl genrsa -out /workspace/pki/root/private/root-ca.key 4096
chmod 600 /workspace/pki/root/private/root-ca.key

# 2. Tạo chứng thư tự ký cho Root CA (SHA-256, hiệu lực 3650 ngày)
openssl req -config /workspace/pki/config/root-ca.cnf \
    -key /workspace/pki/root/private/root-ca.key \
    -new -x509 -days 3650 -sha256 \
    -extensions v3_ca \
    -out /workspace/pki/root/certs/root-ca.crt

# 3. Xuất danh sách thu hồi chứng thư ban đầu của Root CA (CRL Number: 4096)
openssl ca -config /workspace/pki/config/root-ca.cnf \
    -gencrl -out /workspace/pki/root/crl/root.crl.pem
```

> **Lưu ý kiến trúc (Mô phỏng và Sản xuất)**: Trong môi trường Docker Compose của bài lab, việc cô lập Root CA tại thư mục `pki/root/` chỉ mang tính **mô phỏng về mặt logic và cấu trúc thư mục**. Trong hạ tầng vận hành thực tế (production), khóa riêng Root CA phải được lưu trữ ngoại tuyến tách biệt vật lý khỏi mạng hoặc bên trong mô-đun bảo mật phần cứng (HSM), chỉ kích hoạt khi ký Intermediate CA hoặc phát hành `root.crl.pem` định kỳ [1, Mục 4.5–4.6], [3, Mục 3.3.1, 3.3.3].

#### (b) Khởi tạo Intermediate CA (Issuing CA Setup)

Intermediate CA (`UTH Intermediate CA`) sử dụng khóa RSA 2048-bit, tạo CSR theo cấu hình `intermediate-ca.cnf` và được Root CA ký bằng hồ sơ mở rộng `v3_intermediate_ca` với ràng buộc `basicConstraints = critical, CA:true, pathlen:0` (giới hạn chỉ cấp được chứng thư thực thể cuối, không thể ủy quyền thêm CA con) và thời hạn 1825 ngày (5 năm):

```bash
# Chuẩn bị thư mục và cơ sở dữ liệu Intermediate CA
mkdir -p /workspace/pki/intermediate/{certs,private,newcerts,crl,csr}
chmod 700 /workspace/pki/intermediate/private
touch /workspace/pki/intermediate/index.txt
echo 1000 > /workspace/pki/intermediate/serial
echo 1000 > /workspace/pki/intermediate/crlnumber

# 1. Sinh khóa riêng Intermediate CA (RSA 2048-bit)
openssl genrsa -out /workspace/pki/intermediate/private/inter-ca.key 2048
chmod 600 /workspace/pki/intermediate/private/inter-ca.key

# 2. Tạo CSR cho Intermediate CA
openssl req -config /workspace/pki/config/intermediate-ca.cnf \
    -new -sha256 \
    -key /workspace/pki/intermediate/private/inter-ca.key \
    -out /workspace/pki/intermediate/csr/inter-ca.csr

# 3. Root CA phê duyệt và ký chứng thư Intermediate CA
openssl ca -config /workspace/pki/config/root-ca.cnf \
    -extensions v3_intermediate_ca \
    -days 1825 -notext -md sha256 -batch \
    -in /workspace/pki/intermediate/csr/inter-ca.csr \
    -out /workspace/pki/intermediate/certs/inter-ca.crt

# 4. Xuất CRL ban đầu của Intermediate CA và gộp chuỗi tin cậy (ca-chain)
openssl ca -config /workspace/pki/config/intermediate-ca.cnf \
    -gencrl -out /workspace/pki/intermediate/crl/inter.crl.pem

cat /workspace/pki/intermediate/certs/inter-ca.crt /workspace/pki/root/certs/root-ca.crt \
    > /workspace/artifacts/certs/ca-chain.crt
cat /workspace/pki/intermediate/crl/inter.crl.pem /workspace/pki/root/crl/root.crl.pem \
    > /workspace/artifacts/certs/ca-chain.crl.pem
```

#### (c) Sinh khóa, tạo CSR và phát hành chứng thư End-Entity (2 dịch vụ + 1 người dùng)

Theo yêu cầu đề bài, Intermediate CA phát hành chứng thư cho **2 dịch vụ** (`secure.lab.local` mang Serial `1000` và `api.lab.local` mang Serial khởi đầu `1001`) cùng **1 người dùng** (`alice.crt` mang Serial `1002`). Toàn bộ các tệp khóa riêng `.key` đều được áp dụng quyền `chmod 600` (đã kiểm chứng thực tế bằng `stat -c '%a %n'` trên cả 17/17 tệp `.key` trong container `pki-client` đều trả về mode `600`).

Đối với **Dịch vụ 1 (`secure.lab.local`)** và **Dịch vụ 2 (`api.lab.local`)**, chứng thư máy chủ không sử dụng tên miền đại diện (wildcard) mà khai báo tường minh từng tên miền và địa chỉ IP trong phần mở rộng `subjectAltName` kèm `extendedKeyUsage = serverAuth`:

```bash
# Ví dụ quy trình phát hành cho dịch vụ secure.lab.local (Serial 1000)
openssl genrsa -out /workspace/pki/intermediate/private/secure.key 2048
chmod 600 /workspace/pki/intermediate/private/secure.key

cat > /tmp/secure_ext.cnf <<EOF
basicConstraints = CA:FALSE
nsCertType = server
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = DNS:secure.lab.local, DNS:localhost, IP:127.0.0.1
EOF

openssl req -new -sha256 \
    -key /workspace/pki/intermediate/private/secure.key \
    -subj "/C=VN/ST=Ho Chi Minh/L=Ho Chi Minh City/O=UTH PKI Lab/OU=Server/CN=secure.lab.local" \
    -out /workspace/pki/intermediate/csr/secure.csr

openssl ca -config /workspace/pki/config/intermediate-ca.cnf \
    -extfile /tmp/secure_ext.cnf -days 365 -notext -md sha256 -batch \
    -in /workspace/pki/intermediate/csr/secure.csr \
    -out /workspace/pki/intermediate/certs/secure.crt
```

Tương tự, `api.lab.local` sử dụng tệp mở rộng `/tmp/api_ext.cnf` với `subjectAltName = DNS:api.lab.local, DNS:localhost, IP:127.0.0.1`. Đối với **Người dùng 1 (`alice.crt`, Serial `1002`)** phục vụ xác thực mTLS, chứng thư mang `extendedKeyUsage = clientAuth`, không gắn phần mở rộng SAN mà định danh qua Subject DN (`CN=Alice/emailAddress=alice@lab.local`):

```bash
# Quy trình phát hành chứng thư người dùng cho Alice (Serial 1002)
openssl genrsa -out /workspace/pki/intermediate/private/alice.key 2048
chmod 600 /workspace/pki/intermediate/private/alice.key

cat > /tmp/alice_ext.cnf <<EOF
basicConstraints = CA:FALSE
nsCertType = client, email
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = clientAuth
EOF

openssl req -new -sha256 \
    -key /workspace/pki/intermediate/private/alice.key \
    -subj "/C=VN/ST=Ho Chi Minh/L=Ho Chi Minh City/O=UTH PKI Lab/OU=Engineering/CN=Alice/emailAddress=alice@lab.local" \
    -out /workspace/pki/intermediate/csr/alice.csr

openssl ca -config /workspace/pki/config/intermediate-ca.cnf \
    -extfile /tmp/alice_ext.cnf -days 365 -notext -md sha256 -batch \
    -in /workspace/pki/intermediate/csr/alice.csr \
    -out /workspace/pki/intermediate/certs/alice.crt
```

Bên cạnh 3 thực thể chính nêu trên, script `02_issue_certs.sh` đồng thời tạo các chứng thư phục vụ kiểm thử trạng thái bất thường gồm: `expired.crt` (Serial `1003`, dùng `-startdate 20200101000000Z -enddate 20200102000000Z`), `untrusted.crt` (ký bởi một Rogue Root CA tự ký độc lập), `revoked.crt` (Serial `1004`), và `bob.crt` (Serial `1005`).

#### (d) Gia hạn chứng thư (Certificate Renewal — `04_renew_cert.sh`)

Quy trình gia hạn cho `api.lab.local` thực hiện xoay vòng khóa (sinh khóa riêng mới `api_renew.key` thay vì tái sử dụng khóa cũ), tạo CSR mới, ký cấp chứng thư mới với thời hạn mở rộng `730` ngày (Serial **`1006`**, hiệu lực từ `Nov 14 06:20:19 2026 GMT` đến `Nov 13 06:20:19 2028 GMT`), và thu hồi chứng thư cũ (`api_old.crt`, Serial **`1001`**) với mã lý do `superseded`:

```bash
# 1. Lưu bản sao chứng thư cũ (Serial 1001) và sinh khóa + CSR mới
cp /workspace/pki/intermediate/certs/api.crt /workspace/pki/intermediate/certs/api_old.crt
openssl genrsa -out /workspace/pki/intermediate/private/api_renew.key 2048
chmod 600 /workspace/pki/intermediate/private/api_renew.key

openssl req -new -sha256 \
    -key /workspace/pki/intermediate/private/api_renew.key \
    -subj "/C=VN/ST=Ho Chi Minh/L=Ho Chi Minh City/O=UTH PKI Lab/OU=Server/CN=api.lab.local" \
    -out /workspace/pki/intermediate/csr/api_renew.csr

# 2. Cấp chứng thư gia hạn thời hạn 730 ngày (Serial 1006)
openssl ca -config /workspace/pki/config/intermediate-ca.cnf \
    -extfile /tmp/api_renew_ext.cnf -days 730 -notext -md sha256 -batch \
    -in /workspace/pki/intermediate/csr/api_renew.csr \
    -out /workspace/pki/intermediate/certs/api_renew.crt

# 3. Thu hồi chứng thư cũ (Serial 1001) với lý do superseded và cập nhật CRL
openssl ca -config /workspace/pki/config/intermediate-ca.cnf \
    -revoke /workspace/pki/intermediate/certs/api_old.crt \
    -crl_reason superseded -batch
openssl ca -config /workspace/pki/config/intermediate-ca.cnf \
    -gencrl -out /workspace/pki/intermediate/crl/inter.crl.pem

# 4. Thay thế chứng thư/khóa mới cho dịch vụ và cập nhật chuỗi CRL
cp /workspace/pki/intermediate/certs/api_renew.crt /workspace/artifacts/certs/api.crt
cp /workspace/pki/intermediate/private/api_renew.key /workspace/artifacts/certs/api.key
chmod 600 /workspace/artifacts/certs/api.key
cat /workspace/pki/intermediate/crl/inter.crl.pem /workspace/pki/root/crl/root.crl.pem \
    > /workspace/artifacts/certs/ca-chain.crl.pem
```

#### (e) Thu hồi chứng thư và cập nhật CRL (Certificate Revocation & CRL Update)

Khi chứng thư hết tin cậy trước hạn (như `revoked.crt` Serial `1004`, `bob.crt` Serial `1005`, hoặc tình huống khóa `alice.key` bị nghi ngờ rò rỉ đối với `alice.crt` Serial `1002`), quản trị viên thu hồi bằng lệnh `openssl ca -revoke` kèm lý do `keyCompromise`, tái tạo `inter.crl.pem` (nâng `X509v3 CRL Number` lên **`4100`** như ghi nhận trong `evidence_logs.txt`), cập nhật chuỗi `ca-chain.crl.pem` và tải lại cấu hình Nginx:

```bash
# 1. Thu hồi chứng thư người dùng alice.crt (Serial 1002) trong database index.txt
openssl ca -config /workspace/pki/config/intermediate-ca.cnf \
    -revoke /workspace/pki/intermediate/certs/alice.crt \
    -crl_reason keyCompromise -batch

# 2. Tái xuất bản Intermediate CRL (CRL Number: 4100) và ghép chuỗi ca-chain.crl.pem
openssl ca -config /workspace/pki/config/intermediate-ca.cnf \
    -gencrl -out /workspace/pki/intermediate/crl/inter.crl.pem -batch
cat /workspace/pki/intermediate/crl/inter.crl.pem /workspace/pki/root/crl/root.crl.pem \
    > /workspace/artifacts/certs/ca-chain.crl.pem

# 3. Kiểm tra cú pháp, nạp lại Nginx và xác minh lại trạng thái thu hồi bằng OpenSSL
docker compose exec -T web nginx -t
docker compose exec -T web nginx -s reload
openssl verify -crl_check -CAfile /workspace/artifacts/certs/ca-chain.crt \
    -CRLfile /workspace/artifacts/certs/ca-chain.crl.pem \
    /workspace/artifacts/certs/alice.crt
```

Sau thao tác trên, `pki/intermediate/index.txt` chuyển trạng thái của Serial `1002` từ `V` sang `R` (`261114063506Z,keyCompromise`), và Nginx lập tức từ chối mọi yêu cầu mTLS dùng `alice.crt` với mã `HTTP/1.1 400 Bad Request` kèm nhật ký lỗi `client SSL certificate verify error: (23:certificate revoked)`.

---

## 2. So sánh cơ chế kiểm tra thu hồi CRL và OCSP

Trong vận hành PKI, việc công bố và kiểm tra trạng thái thu hồi chứng thư trước thời điểm hết hạn (`notAfter`) được triển khai chủ yếu qua hai cơ chế chuẩn là **CRL (Certificate Revocation List)** [1, Mục 4.5], [2, Mục 23.2], [3, Mục 3.3.4] và **OCSP (Online Certificate Status Protocol)** [3, Mục 3.3.4]. Bảng dưới đây tổng hợp các đặc tính kỹ thuật cốt lõi giữa hai cơ chế:

| Tiêu chí so sánh | CRL (Certificate Revocation List) [1], [2], [3] | OCSP (Online Certificate Status Protocol) [3] |
|---|---|---|
| **Cơ chế hoạt động** | CA định kỳ phát hành danh sách chứa toàn bộ số sê-ri chứng thư bị thu hồi kèm chữ ký số của CA; phía kiểm chứng tải về và lưu đệm cục bộ (*local cache*). | Client gửi trực tiếp truy vấn mang số sê-ri của chứng thư cần kiểm tra tới máy chủ OCSP của CA và nhận phản hồi trạng thái tức thời (`Valid` hoặc `Revoked`). |
| **Độ trễ cập nhật** | Phụ thuộc chu kỳ xuất bản CRL và thời gian lưu đệm tại client; tồn tại độ trễ cập nhật nếu chứng thư bị thu hồi ngay sau khi bản CRL hiện tại vừa được phát hành. | Cập nhật gần như theo thời gian thực (*real-time*), phản ánh tức thì trạng thái mới ngay khi cơ sở dữ liệu thu hồi của CA được cập nhật. |
| **Chi phí băng thông & tải** | Kích thước tệp CRL tăng dần theo số lượng chứng thư bị thu hồi; phía kiểm chứng phải tải toàn bộ danh sách gây tốn băng thông khi hệ thống lớn. | Kích thước gói tin truy vấn và phản hồi rất nhỏ (chỉ chứa thông tin của một số sê-ri), tiết kiệm băng thông đường truyền hơn so với tải cả tệp CRL. |
| **Tính sẵn sàng & phụ thuộc hạ tầng** | Không phụ thuộc kết nối trực tuyến tới CA tại từng phiên bắt tay nếu CRL đã được lưu đệm cục bộ hoặc nạp sẵn tại máy chủ (như chỉ thị `ssl_crl` trên Nginx). | Đòi hỏi máy chủ OCSP của CA phải luôn sẵn sàng trực tuyến; nếu máy chủ OCSP gặp sự cố hoặc nghẽn mạng, quá trình xác minh có thể bị gián đoạn hoặc giảm độ an toàn. |
| **Quyền riêng tư (Privacy)** | Ít làm lộ hành vi truy cập cụ thể của từng phiên: client tải tệp danh sách chung nên CA không biết chính xác client đang kết nối tới dịch vụ nào tại từng thời điểm. | Phát sinh rủi ro lộ thông tin truy cập: mỗi truy vấn trực tiếp mang số sê-ri chứng thư gửi về máy chủ OCSP của CA cho thấy thời điểm và dịch vụ mà client đang xác minh. |

Về mặt lựa chọn kiến trúc, **CRL** là giải pháp phù hợp cho các hệ thống nội bộ, môi trường mạng cô lập và mô hình phòng thí nghiệm Docker của đồ án, nơi số lượng chứng thư thu hồi nhỏ và quản trị viên kiểm soát trực tiếp việc gắn `ca-chain.crl.pem` vào cấu hình `ssl_crl` của Nginx. Ngược lại, trong các hệ thống quy mô lớn có số lượng chứng thư thu hồi nhiều và đòi hỏi độ tươi dữ liệu tức thời, **OCSP** giúp khắc phục nhược điểm kích thước tệp lớn và độ trễ cập nhật của CRL [2, Mục 23.2], [3, Mục 3.3.4].

---

## 3. Phân tích rủi ro lộ khóa riêng (Private Key Compromise) theo 3 cấp độ

Mức độ nghiêm trọng và quy trình ứng phó sự cố khi lộ khóa riêng phụ thuộc trực tiếp vào vị trí của cặp khóa đó trong cây phân cấp tin cậy hai tầng [1, Mục 4.5–4.6], [3, Mục 3.3.3–3.3.4]:

### 3.1. Cấp độ 1: Lộ khóa riêng Root CA (`root-ca.key`)

- **Phạm vi ảnh hưởng**: Đây là kịch bản sự cố nghiêm trọng nhất vì Root CA đóng vai trò là **Gốc tin cậy (Trust Anchor)** của toàn hệ thống [3, Mục 3.3.3]. Khi khóa `root-ca.key` bị chiếm đoạt, kẻ tấn công có khả năng tự ký phát hành bất kỳ Intermediate CA giả mạo hoặc chứng thư thực thể cuối hợp lệ nào về mặt mật mã cho mọi tên miền hay tài khoản người dùng; toàn bộ các hệ thống đã tin cậy `root-ca.crt` đều có nguy cơ chấp nhận chuỗi chứng thư giả mạo này.
- **Quy trình ứng phó**: Do Root CA tự ký nên không tồn tại CA cấp trên để thu hồi nó thông qua cơ chế CRL thông thường [1, Mục 4.5]. Tổ chức bắt buộc phải gỡ bỏ chứng thư `root-ca.crt` khỏi toàn bộ **Trust Store** trên hệ điều hành, trình duyệt, container và thiết bị đầu cuối trong toàn hệ thống, sau đó thiết lập lại một Root CA hoàn toàn mới, tái cấp Intermediate CA và toàn bộ chứng thư thực thể cuối.

### 3.2. Cấp độ 2: Lộ khóa riêng Intermediate CA (`inter-ca.key`)

- **Phạm vi ảnh hưởng**: Toàn bộ chứng thư lá (`secure.crt`, `api.crt`, `alice.crt`) do Intermediate CA đó cấp phát đều mất độ tin cậy vì kẻ tấn công có thể dùng `inter-ca.key` để giả mạo chứng thư máy chủ hoặc khách hàng mới trong phạm vi ràng buộc của CA này. Tuy nhiên, nếu khóa `root-ca.key` vẫn được bảo vệ an toàn, gốc tin cậy của hệ thống vẫn giữ nguyên giá trị.
- **Quy trình ứng phó**: Root CA phải thực hiện thu hồi chứng thư `inter-ca.crt` (ghi nhận vào `root.crl.pem` của Root CA) và khởi tạo một Intermediate CA mới với cặp khóa mới để thay thế [1, Mục 4.5], [3, Mục 3.3.3]. Đây cũng là cơ sở kỹ thuật giải thích lý do trong lab thực nghiệm, Nginx khi bật xác thực chuỗi hai tầng (`ssl_verify_depth 2`) nạp tệp CRL gộp `ca-chain.crl.pem` (`inter.crl.pem` nối tiếp `root.crl.pem`) nhằm bảo đảm cả trường hợp chứng thư Intermediate CA bị Root CA thu hồi cũng bị phát hiện và chặn lại.

### 3.3. Cấp độ 3: Lộ khóa riêng End-Entity (Máy chủ hoặc Người dùng)

- **Phạm vi ảnh hưởng**: Thiệt hại bị khoanh vùng trong phạm vi danh tính của thực thể sở hữu khóa bị lộ.
  - Nếu rò rỉ khóa máy chủ (`secure.key` hoặc `api.key`), kẻ tấn công kết hợp với kỹ thuật giả mạo định tuyến (DNS spoofing / ARP poisoning) có thể mạo danh máy chủ hợp pháp để thực hiện tấn công xen giữa (Man-in-the-Middle — MitM) và giải mã hoặc can thiệp lưu lượng HTTPS.
  - Nếu rò rỉ khóa người dùng (`alice.key`), kẻ tấn công có thể mạo danh người dùng `Alice` vượt qua lớp xác thực hai chiều mTLS để truy cập trái phép các điểm cuối API nhạy cảm (như `/mtls` trên `api.lab.local`).
- **Quy trình ứng phó 5 bước khi lộ khóa riêng** [3, Mục 3.3.4]: (1) **Hành động khẩn cấp** — ngừng sử dụng ngay lập tức cặp khóa bị nghi ngờ mà không chờ hết hạn; (2) **Yêu cầu thu hồi tức thì** — đưa số sê-ri chứng thư vào danh sách thu hồi CRL/OCSP tại Intermediate CA (như đã thực nghiệm thu hồi `alice.crt` Serial `1002` trong `evidence_logs.txt` với lý do `keyCompromise`, tái xuất `inter.crl.pem`, gộp `ca-chain.crl.pem` và thực thi `nginx -s reload` khiến mọi nỗ lực tái sử dụng `alice.key` bị Nginx chặn với mã `HTTP/1.1 400 Bad Request` và thông báo `error 23: certificate revoked`); (3) **Tiêu hủy vật lý** — xóa an toàn mọi bản sao khóa bị lộ trên thiết bị và bản sao lưu; (4) **Tái tạo khóa và cấp mới** — sinh cặp khóa hoàn toàn mới kèm CSR mới gửi CA cấp chứng thư thay thế; (5) **Kiểm toán thiệt hại** — rà soát nhật ký hệ thống trong khoảng thời gian khóa có nguy cơ rò rỉ để phát hiện phiên truy cập hoặc chữ ký giả mạo.

### 3.4. Các biện pháp giảm thiểu thực tiễn

Để thu hẹp khả năng rò rỉ và giới hạn phạm vi thiệt hại, hạ tầng PKI cần kết hợp đồng thời nhiều lớp phòng vệ trong suốt vòng đời khóa [1, Mục 4.5–4.6], [3, Mục 3.3.1, 3.3.3–3.3.4]:
1. **Cô lập Root CA ngoại tuyến (Offline Root CA)**: Giữ khóa `root-ca.key` tách biệt vật lý khỏi mạng trong vận hành thực tế (khác với mô hình mô phỏng qua cấu trúc thư mục Docker trong bài lab).
2. **Sử dụng Mô-đun bảo mật phần cứng (HSM / TPM)**: Khóa riêng của CA và máy chủ trọng yếu được sinh và lưu trữ trong phần cứng bảo mật chuyên dụng (HSM hoặc TPM), không cho phép xuất khóa riêng ra ngoài dưới dạng bản rõ [3, Mục 3.3.1].
3. **Xoay vòng khóa và giới hạn thời hạn chứng thư**: Áp dụng cơ chế xoay vòng khóa (Key Rotation) và giảm thời hạn hiệu lực của chứng thư thực thể cuối nhằm thu hẹp cửa sổ thời gian kẻ tấn công có thể lợi dụng khóa bị lộ [3, Mục 3.3.1].
4. **Kiểm soát quyền truy cập và quy trình thu hồi nhanh**: Áp dụng nguyên tắc đặc quyền tối thiểu (*Least Privilege*) trên tệp khóa (`chmod 600` cho tệp `.key`, `chmod 700` cho thư mục `private/`, đã kiểm chứng đạt mode `600` trên toàn bộ 17 tệp khóa của lab) [3, Mục 3.3.1], kết hợp tái xuất bản CRL và nạp lại dịch vụ (`nginx -s reload`) ngay sau khi ghi nhận sự cố.

---

## 4. Liên hệ hạ tầng PKI với quy trình bắt tay TLS 1.3

Giao thức TLS/HTTPS sử dụng mô hình **mật mã lai (Hybrid Cryptosystem)** kết hợp trao đổi khóa phiên tạm thời để bảo đảm **tính bí mật chuyển tiếp (Perfect Forward Secrecy — PFS)** với cơ chế xác thực danh tính dựa trên chứng thư số PKI [1, Mục 6.2–6.3], [2, Mục 22.3–22.4], [3, tr. 52–53, 89–91]. Quá trình tích hợp PKI trong một phiên bắt tay TLS 1.3 điển hình (đã kiểm chứng trên `secure.lab.local` và `api.lab.local` trong `evidence_logs.txt`) diễn ra qua các bước sau:

1. **Thỏa thuận tham số và thiết lập khóa phiên (`ClientHello` / `ServerHello`)**:
   Client gửi `ClientHello` mang danh sách thuật toán mật mã hỗ trợ và tham số trao đổi khóa phiên tạm thời; máy chủ phản hồi `ServerHello` để chốt tham số thuật toán và dẫn xuất khóa phiên dùng cho phiên truyền thông [1, Mục 6.2], [2, Mục 22.3], [3, tr. 89–91]. Trong kết quả kiểm thử `evidence_logs.txt` với `openssl s_client -tls1_3`, phiên thiết lập bộ mã đối xứng xác thực `TLS_AES_256_GCM_SHA384` cùng tham số trao đổi khóa tạm thời `Server Temp Key: X25519, 253 bits`.

2. **Chuyển giao chuỗi tin cậy qua thông điệp `Certificate`**:
   Server gửi thông điệp `Certificate` mang chứng thư thực thể cuối (`secure.crt`) kèm chứng thư trung gian (`inter-ca.crt`) [1, Mục 6.2], [2, Mục 22.3]. Tại phía client, trình xác minh thực hiện đồng thời bốn kiểm tra PKI [1, Mục 4.5], [2, Mục 23.2], [3, Mục 3.3.2, 3.3.5]:
   - Xác minh chuỗi tin cậy hướng về gốc tin cậy (`ca-chain.crt` chứa `UTH Root CA`);
   - Kiểm tra khoảng thời gian hiệu lực (`notBefore ≤ hiện tại ≤ notAfter`);
   - Đối chiếu tên miền đích với phần mở rộng SAN (`DNS:secure.lab.local`) và kiểm tra mục đích sử dụng khóa (`serverAuth`);
   - Kiểm tra trạng thái thu hồi qua CRL hoặc OCSP.

3. **Chứng minh quyền sở hữu khóa riêng qua thông điệp `CertificateVerify`**:
   Do chứng thư `secure.crt` là dữ liệu công khai, việc chỉ gửi `Certificate` không chứng minh được máy chủ đang nắm giữ khóa riêng tương ứng. Do đó, server tạo một chữ ký số đặt trong thông điệp `CertificateVerify`, tính trên giá trị băm của lịch sử các thông điệp bắt tay trước đó bằng khóa riêng của máy chủ (`secure.key`) [1, Mục 6.2], [2, Mục 22.3].
   Trong bằng chứng thực nghiệm ở `evidence_logs.txt` (Section 3, Command 3.1) khi kiểm thử `secure.lab.local` qua `openssl s_client -tls1_3`, các tham số quan sát trực tiếp gồm:
   - `New, TLSv1.3, Cipher is TLS_AES_256_GCM_SHA384` (bộ mã hóa đối xứng xác thực AEAD);
   - `Server Temp Key: X25519, 253 bits` (trao đổi khóa tạm thời giúp đạt tính bí mật chuyển tiếp PFS);
   - `Peer signing digest: SHA256` và `Peer signature type: RSA-PSS` (hàm băm SHA-256 kết hợp lược đồ chữ ký số RSA-PSS dùng trong thông điệp `CertificateVerify`);
   - `Verification: OK` và `Verify return code: 0 (ok)`.
   Client sử dụng khóa công khai trích xuất từ `secure.crt` (đã xác minh chuỗi tin cậy ở bước 2) để kiểm định chữ ký trong `CertificateVerify`, qua đó xác nhận bên gửi thực sự sở hữu `secure.key` [1, Mục 6.2].

4. **Hoàn tất tính toàn vẹn (`Finished`) và mở rộng cho mTLS (`api.lab.local`)**:
   Thông điệp `Finished` chứa mã xác thực thông điệp phủ lên toàn bộ quá trình bắt tay để chống sửa đổi trái phép [1, Mục 6.2]. Khi yêu cầu xác thực hai chiều (mTLS), server gửi thêm `CertificateRequest` yêu cầu client cung cấp chứng thư thuộc danh sách CA tin cậy; client phản hồi cặp thông điệp `Certificate` và `CertificateVerify` ký bằng khóa riêng của mình [1, Mục 6.2], [2, Mục 22.3], [3, tr. 52]. Trong bài lab thực nghiệm trên `api.lab.local` (bật `ssl_verify_client on;`), `evidence_logs.txt` (Section 4, Command 4.2) ghi nhận server gửi `Acceptable client certificate CA names` gồm `UTH Intermediate CA` và `UTH Root CA`; Nginx xác minh `alice.crt` đối chiếu `ca-chain.crt` (`ssl_verify_depth 2`) và tra cứu `ca-chain.crl.pem` (`ssl_crl`), lập tức trả về `HTTP/1.1 400 Bad Request` (`client SSL certificate verify error: (23:certificate revoked)`) khi phát hiện Serial `1002` đã bị thu hồi.

---

## 5. Đính chính thuật ngữ và cơ sở mật mã chuẩn xác

### 5.1. Yêu cầu Subject Alternative Name (SAN) so với Common Name (CN)

Trong tài liệu kỹ thuật PKI, cần phân biệt chính xác nguồn gốc quy chuẩn: việc bắt buộc máy chủ Web/API phải khai báo tên miền hoặc địa chỉ IP trong phần mở rộng **Subject Alternative Name (SAN)** thay vì chỉ dựa vào trường `Common Name (CN)` của Subject DN **không phải là quy định riêng của giao thức TLS 1.3**.

Theo chuẩn chứng thư số X.509, trường `Subject` truyền thống không đủ linh hoạt để biểu diễn đầy đủ các định danh dịch vụ Internet như địa chỉ email, URL hay tên miền máy chủ, nên phần mở rộng X.509v3 `Subject Alternative Name (SAN)` được bổ sung nhằm liệt kê một hoặc nhiều định danh gắn với thực thể sở hữu khóa công khai [1, Mục 4.5], [3, Mục 3.3.2]. Đặc biệt đối với máy chủ HTTPS, các trình duyệt web và máy khách TLS hiện đại yêu cầu đối chiếu tên miền truy cập với trường SAN (thay thế cách đối chiếu theo trường CN truyền thống), áp dụng đồng nhất cho cả TLS 1.2 lẫn TLS 1.3 [1, Mục 4.5], [3, tr. 53, 99]. Do đó, mọi chứng thư máy chủ trong đồ án (`secure.crt`, `api.crt`) đều cấu hình đầy đủ SAN (chẳng hạn `DNS:secure.lab.local, DNS:localhost, IP Address:127.0.0.1`).

### 5.2. Công thức mật mã Chuỗi tin cậy (Chain of Trust) và cấu trúc `TBSCertificate`

Cách diễn đạt thông thường *"dùng khóa công khai của CA để giải mã chữ ký trên chứng thư"* không chính xác về mặt mật mã học đối với các lược đồ chữ ký hiện đại (như RSA-PSS hay ECDSA), vốn hoạt động theo nguyên lý **tạo và xác minh chữ ký trên giá trị băm** chứ không giải mã chữ ký để khôi phục toàn văn chứng thư [1, Mục 3.6, 4.5], [2, Chương 21, Mục 23.2], [3, Mục 3.3.2, 3.3.5]. Theo cấu trúc chứng thư X.509 [1, Mục 4.5], [3, Mục 3.3.2], cơ chế Chuỗi tin cậy được mô tả chuẩn xác bằng hai cặp hàm ký (`Sign`) và xác minh (`Verify`) thực hiện trên giá trị băm của khối dữ liệu **`TBSCertificate`** (*To-Be-Signed Certificate*):

- **Giai đoạn ký phát hành (Issuing)**:
  - Root CA ký phát hành chứng thư Intermediate CA:
    `S_Inter = Sign(K_Root_Private, Hash(TBSCertificate_Inter))`
  - Intermediate CA ký phát hành chứng thư thực thể cuối (Server hoặc Client):
    `S_Entity = Sign(K_Inter_Private, Hash(TBSCertificate_Entity))`

- **Giai đoạn xác minh chuỗi tin cậy (Verification)**:
  - Trình xác minh dùng khóa công khai của Root CA (từ Trust Anchor) kiểm định chữ ký trên chứng thư Intermediate CA:
    `Verify(K_Root_Public, Hash(TBSCertificate_Inter), S_Inter) = True`
  - Sau khi tin cậy khóa công khai trích xuất từ Intermediate CA, trình xác minh kiểm định chữ ký trên chứng thư thực thể cuối:
    `Verify(K_Inter_Public, Hash(TBSCertificate_Entity), S_Entity) = True`

**Lý do chỉ băm và ký trên `TBSCertificate`**: Theo cấu trúc chứng thư X.509 [1, Mục 4.5], trường giá trị chữ ký là đầu ra của thuật toán ký số nên chưa tồn tại tại thời điểm tính `Hash(...)`. Toàn bộ dữ liệu định danh và ràng buộc bảo mật cần bảo vệ toàn vẹn (bao gồm phiên bản chứng thư, số sê-ri `serialNumber`, thuật toán ký, nhà phát hành `Issuer`, thời hạn hiệu lực, chủ thể `Subject`, khóa công khai `SubjectPublicKeyInfo` và toàn bộ phần mở rộng `extensions` như SAN, KeyUsage, BasicConstraints) đều nằm trong khối `TBSCertificate`; chứng thư hoàn chỉnh chỉ ghép thêm định danh thuật toán ký và giá trị chữ ký số thu được [1, Mục 4.5], [3, Mục 3.3.2, 3.3.5].

---

## 6. Quy tắc gắn trích dẫn và Danh mục Tài liệu tham khảo duy nhất

### 6.1. Nguyên tắc gắn thẻ trích dẫn trong báo cáo chính

- **Whitelist nghiêm ngặt (chỉ `[1]`–`[3]`)**: Toàn bộ cơ sở lý thuyết, định nghĩa chuẩn X.509, vòng đời PKI/RA/CA, CRL/OCSP và TLS/HTTPS chỉ được trích dẫn từ đúng **3 tài liệu** trong danh mục bên dưới. Tuyệt đối không đưa thêm nguồn ngoài luồng hoặc liên kết website bên ngoài.
- **Không gắn trích dẫn vào phần thực nghiệm của nhóm**: Không gắn `[1]`, `[2]`, `[3]` vào các đoạn mô tả cấu hình Docker (`docker-compose.yml`), tệp cấu hình Nginx tự viết (`secure.conf`, `api.conf`, `revoked.conf`), kịch bản shell tự xây dựng (`01_setup_ca.sh`–`04_renew_cert.sh`, `eval_rubric.sh`) hoặc kết quả kiểm thử trong `evidence_logs.txt`.
- **Chỉ định chính xác mục tài liệu giảng dạy** khi dùng `[3]` (cụ thể `Chương 3, Mục 3.3.1–3.3.5` cho kiến thức về hạ tầng PKI, chứng thư số X.509 và quản lý vòng đời chứng thư).
- **Phân bổ thẻ `[1]`–`[3]` theo nội dung gốc của từng tài liệu**:
  - `[1]`: Khái niệm chữ ký số (Mục 3.6), cấu trúc X.509, chuỗi tin cậy, CRL và mô hình PKIX/RA (Mục 4.5–4.6), bắt tay TLS và HTTPS (Mục 6.2–6.3) trong W. Stallings (2017).
  - `[2]`: Cơ sở mật mã khóa công khai (Chương 21), SSL/TLS và HTTPS (Mục 22.3–22.4), xác thực X.509, bộ đệm CRL cục bộ và mô hình PKI (Mục 23.2–23.3) trong W. Stallings & L. Brown (2nd ed., 2012).
  - `[3]`: Giáo trình/Bài giảng An ninh Mạng — Trường ĐH Giao thông vận tải TP.HCM, `Chương 3 (Mục 3.3.1–3.3.5)`: vòng đời khóa mật mã, cấu trúc X.509/SAN, RA/CA/Trust Anchor, so sánh CRL với OCSP, quy trình ứng phó lộ khóa 5 bước và bảo mật tầng vận chuyển TLS/HTTPS.

### 6.2. Danh mục Tài liệu tham khảo chuẩn (IEEE Style — Whitelist duy nhất)

- `[1]` W. Stallings, *Network Security Essentials: Applications and Standards*, 6th ed. Harlow, England: Pearson Education, 2017.
- `[2]` W. Stallings and L. Brown, *Computer Security: Principles and Practice*, 2nd ed. Boston, MA, USA: Pearson Education, 2012.
- `[3]` Lê Quốc Tuấn, "Bài giảng An ninh Mạng — Chương 3: Bảo mật hệ thống mạng và Dữ liệu (Mục 3.3.1–3.3.5)," Khoa Công nghệ Thông tin, Trường Đại học Giao thông vận tải TP. Hồ Chí Minh (UTH), 2026.
