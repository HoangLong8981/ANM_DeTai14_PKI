from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = BASE_DIR / "docs" / "report" / "images"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_font(size: int, bold: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont:
    if mono:
        candidates = ["C:/Windows/Fonts/consolab.ttf" if bold else "C:/Windows/Fonts/consola.ttf"]
    elif bold:
        candidates = ["C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/segoeuib.ttf"]
    else:
        candidates = ["C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/segoeui.ttf"]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


FONT_TITLE = load_font(28, bold=True)
FONT_SUBTITLE = load_font(17, bold=False)
FONT_H2 = load_font(19, bold=True)
FONT_H3 = load_font(16, bold=True)
FONT_BODY = load_font(15, bold=False)
FONT_SMALL = load_font(13, bold=False)
FONT_MONO = load_font(14, bold=False)
FONT_MONO_B = load_font(14, bold=True)
FONT_BADGE = load_font(14, bold=True)


def draw_round_box(draw, box, fill, outline, radius=14, width=2):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def draw_header_box(draw, box, header_h, fill, header_fill, outline, title, title_color=(255, 255, 255), radius=14):
    x1, y1, x2, y2 = box
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=2)
    draw.rounded_rectangle((x1, y1, x2, y1 + header_h + radius), radius=radius, fill=header_fill, outline=outline, width=2)
    draw.rectangle((x1 + 2, y1 + header_h, x2 - 2, y1 + header_h + radius + 1), fill=fill)
    draw.line((x1, y1 + header_h, x2, y1 + header_h), fill=outline, width=2)
    draw.text((x1 + 16, y1 + (header_h - 20) // 2), title, font=FONT_H2, fill=title_color)


def draw_arrow(draw, p1, p2, color, width=3, head_len=12, head_w=7, dashed=False):
    x1, y1 = p1
    x2, y2 = p2
    if dashed:
        import math
        dist = math.hypot(x2 - x1, y2 - y1)
        steps = max(1, int(dist // 14))
        for i in range(0, steps, 2):
            t0 = i / steps
            t1 = min(1.0, (i + 1) / steps)
            sx = x1 + (x2 - x1) * t0
            sy = y1 + (y2 - y1) * t0
            ex = x1 + (x2 - x1) * t1
            ey = y1 + (y2 - y1) * t1
            draw.line((sx, sy, ex, ey), fill=color, width=width)
    else:
        draw.line((x1, y1, x2, y2), fill=color, width=width)

    import math
    angle = math.atan2(y2 - y1, x2 - x1)
    left = (x2 - head_len * math.cos(angle) + head_w * math.sin(angle),
            y2 - head_len * math.sin(angle) - head_w * math.cos(angle))
    right = (x2 - head_len * math.cos(angle) - head_w * math.sin(angle),
             y2 - head_len * math.sin(angle) + head_w * math.cos(angle))
    draw.polygon([(x2, y2), left, right], fill=color)


def draw_label_pill(draw, cx, cy, text, bg=(255, 255, 255), fg=(20, 40, 80), border=(140, 170, 210)):
    bbox = draw.textbbox((0, 0), text, font=FONT_SMALL)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    pad_x, pad_y = 8, 4
    box = (cx - tw // 2 - pad_x, cy - th // 2 - pad_y, cx + tw // 2 + pad_x, cy + th // 2 + pad_y)
    draw.rounded_rectangle(box, radius=8, fill=bg, outline=border, width=1)
    draw.text((cx - tw // 2, cy - th // 2 - 2), text, font=FONT_SMALL, fill=fg)


def draw_multiline(draw, x, y, lines, font=FONT_BODY, fill=(30, 35, 45), line_gap=6):
    cur_y = y
    for line in lines:
        if isinstance(line, tuple):
            fnt, col, txt = line
        else:
            fnt, col, txt = font, fill, line
        draw.text((x, cur_y), txt, font=fnt, fill=col)
        bbox = draw.textbbox((x, cur_y), txt, font=fnt)
        cur_y = bbox[3] + line_gap
    return cur_y


def build_arch_diagram():
    W, H = 1600, 900
    img = Image.new("RGB", (W, H), (247, 249, 252))
    draw = ImageDraw.Draw(img)

    # Top Banner
    draw.rectangle((0, 0, W, 92), fill=(11, 43, 88))
    draw.text((38, 18), "SƠ ĐỒ 1. KIẾN TRÚC HẠ TẦNG PKI 2 TẦNG VÀ MẠNG DOCKER CÔ LẬP (pki-net)", font=FONT_TITLE, fill=(255, 255, 255))
    draw.text((38, 56), "Đề tài 14 — Nhóm 14 | OpenSSL 3.3.7 + Nginx 1.27.5 (Alpine Linux trên Docker Compose) | Cô lập hoàn toàn khỏi Host Windows", font=FONT_SUBTITLE, fill=(200, 222, 250))

    # Box 1 (Top-Left): PKI Core
    draw_header_box(draw, (40, 118, 760, 468), 46, (255, 255, 255), (21, 76, 138), (21, 76, 138),
                    "1. Hạ tầng CA Phân tầng (./pki/ — chỉ gắn vào pki-client)")

    # Root CA sub-box
    draw_round_box(draw, (64, 184, 376, 362), (240, 246, 255), (43, 99, 168), radius=10, width=2)
    draw_multiline(draw, 80, 198, [
        (FONT_H3, (15, 52, 102), "UTH Root CA (pki/root/)"),
        (FONT_SMALL, (50, 60, 75), "• Khóa: RSA 4096-bit (chmod 600)"),
        (FONT_SMALL, (50, 60, 75), "• Self-signed, 3650 ngày (10 năm)"),
        (FONT_SMALL, (50, 60, 75), "• CA:TRUE | keyCertSign, cRLSign"),
        (FONT_SMALL, (50, 60, 75), "• Cô lập logic (chỉ ký Inter CA & CRL)"),
        (FONT_SMALL, (50, 60, 75), "• CRL: root.crl.pem (CRL #4097)"),
    ], line_gap=5)

    # Inter CA sub-box
    draw_round_box(draw, (426, 184, 742, 362), (239, 250, 245), (26, 122, 74), radius=10, width=2)
    draw_multiline(draw, 438, 198, [
        (FONT_H3, (18, 92, 54), "Intermediate CA (pki/intermediate/)"),
        (FONT_SMALL, (50, 60, 75), "• Khóa: RSA 2048-bit (chmod 600)"),
        (FONT_SMALL, (50, 60, 75), "• Ký bởi Root CA, 1825 ngày (5 năm)"),
        (FONT_SMALL, (50, 60, 75), "• CA:TRUE, pathlen:0 | unique_subject=no"),
        (FONT_SMALL, (50, 60, 75), "• Cấp phát End-Entity (1000..1007)"),
        (FONT_SMALL, (50, 60, 75), "• CRL: inter.crl.pem (CRL #4102)"),
    ], line_gap=5)

    draw_arrow(draw, (376, 273), (426, 273), (21, 76, 138), width=3)
    draw_label_pill(draw, 401, 245, "Ký CA", bg=(232, 242, 255), fg=(15, 52, 102))

    # Artifacts Bundle Bar inside Box 1
    draw_round_box(draw, (64, 382, 738, 448), (255, 248, 232), (186, 124, 24), radius=10, width=2)
    draw_multiline(draw, 80, 392, [
        (FONT_H3, (140, 82, 8), "Gói phân phối chuẩn (./artifacts/certs/) — Mount :ro vào pki-web"),
        (FONT_SMALL, (65, 55, 35), "ca-chain.crt (Inter + Root) | ca-chain.crl.pem (Inter + Root) | secure.fullchain.crt | api.fullchain.crt"),
    ], line_gap=4)

    # Box 2 (Bottom-Left): pki-client
    draw_header_box(draw, (40, 502, 760, 862), 46, (255, 255, 255), (38, 97, 86), (38, 97, 86),
                    "2. Container pki-client (Alpine 3.20 — OpenSSL 3.3.7 & cURL 8.14.1)")
    draw_multiline(draw, 62, 566, [
        (FONT_H3, (22, 74, 64), "Điều phối PKI & Lưu trữ Chứng thư Người dùng (Mount .:/workspace)"),
        (FONT_BODY, (40, 45, 55), "• Scripts vòng đời: init_all_pki.sh, 01_setup_ca.sh → 05_reissue_user.sh"),
        (FONT_BODY, (40, 45, 55), "• Alice (User 1 - Hợp lệ): alice.crt (Serial 1007, EKU clientAuth) → mTLS 200 OK"),
        (FONT_BODY, (40, 45, 55), "• Alice (Cũ - Thu hồi): alice_1002_revoked.crt (Serial 1002, keyCompromise) → 400"),
        (FONT_BODY, (40, 45, 55), "• Bob (User 2 - Thu hồi): bob.crt (Serial 1005, keyCompromise) → 400 (error 23)"),
        (FONT_H3, (22, 74, 64), "Bộ kiểm thử tự động & Minh chứng (./tests/ → ./artifacts/logs/)"),
        (FONT_BODY, (40, 45, 55), "• run_all_tests.sh (TC01–TC06) | run_extended_tests.sh (TC07–TC09)"),
        (FONT_BODY, (40, 45, 55), "• demo_report.sh (tc01..tc08, tc07b) | eval_rubric.sh (Đạt 10.0 / 10.0)"),
    ], line_gap=7)

    # Box 3 (Right): Docker Network + pki-web
    draw_round_box(draw, (818, 118, 1560, 862), (235, 242, 252), (90, 128, 178), radius=16, width=2)
    draw.text((840, 130), "Mạng Bridge cô lập: pki-net (Docker Compose Internal DNS)", font=FONT_H3, fill=(28, 66, 115))

    draw_header_box(draw, (840, 168, 1538, 748), 46, (255, 255, 255), (120, 44, 122), (120, 44, 122),
                    "3. Container pki-web (nginx:1.27-alpine — Cổng 443, Ánh xạ 8443:443)")

    draw_round_box(draw, (862, 228, 1516, 266), (253, 240, 240), (176, 48, 48), radius=8, width=1)
    draw.text((878, 238), "Bảo mật: Chỉ mount ./artifacts/certs:ro (/etc/nginx/certs) — KHÔNG mount ./pki (tách biệt khóa CA)", font=FONT_SMALL, fill=(145, 28, 28))

    vhosts = [
        ("secure.conf  |  https://secure.lab.local",
         "• Cert: secure.fullchain.crt (Serial 1000, TLSv1.2/1.3, SAN: DNS:secure.lab.local, localhost, 127.0.0.1)\n• Kết quả: HTTPS hợp lệ HTTP 200 OK, Verify return code: 0 (ok) [TC01, TC02]",
         (238, 249, 241), (36, 130, 74)),
        ("api.conf  |  https://api.lab.local/mtls",
         "• Cert: api.fullchain.crt (Serial 1006, gia hạn 730 ngày từ 1001) + ssl_verify_client on (depth 2)\n• Kiểm soát thu hồi: ssl_crl ca-chain.crl.pem → Alice (1007): 200 OK | Bob (1005), Alice cũ (1002): 400",
         (236, 245, 255), (29, 92, 164)),
        ("expired.conf  |  https://expired.lab.local",
         "• Cert: expired.crt (Serial 1003, hiệu lực 01/01/2020–02/01/2020 GMT)\n• Kết quả: Client bắt lỗi verify error:num=10:certificate has expired, curl: (60) [TC04]",
         (255, 247, 234), (186, 114, 16)),
        ("untrusted.conf  |  https://untrusted.lab.local",
         "• Cert: untrusted.crt (ký bởi Rogue Root CA độc lập, không nằm trong ca-chain.crt)\n• Kết quả: Client bắt lỗi verify error:num=20:unable to get local issuer certificate [TC05]",
         (253, 241, 242), (176, 45, 56)),
        ("revoked.conf  |  https://revoked.lab.local",
         "• Cert: revoked.crt (Serial 1004, đã thu hồi keyCompromise trong inter.crl.pem)\n• Kết quả: Client kiểm tra CRL (-CRL / --crlfile) bắt lỗi verify error:num=23:certificate revoked [TC06]",
         (248, 242, 253), (122, 52, 160)),
    ]

    vy = 282
    for title_v, body_v, bg_v, bd_v in vhosts:
        draw_round_box(draw, (862, vy, 1516, vy + 82), bg_v, bd_v, radius=10, width=2)
        draw.text((878, vy + 10), title_v, font=FONT_H3, fill=bd_v)
        lines = body_v.split("\n")
        draw.text((878, vy + 36), lines[0], font=FONT_SMALL, fill=(45, 50, 60))
        draw.text((878, vy + 56), lines[1], font=FONT_SMALL, fill=(45, 50, 60))
        vy += 92

    # Browser Box (Bottom-Right inside pki-net card)
    draw_round_box(draw, (840, 766, 1538, 844), (255, 255, 255), (72, 92, 122), radius=10, width=2)
    draw_multiline(draw, 856, 778, [
        (FONT_H3, (35, 55, 85), "4. Trình duyệt trên Máy chủ Windows Host (Port Forwarding 8443 → 443)"),
        (FONT_SMALL, (50, 55, 65), "Truy cập https://localhost:8443 → 200 OK (hiển thị 'Không bảo mật' do Windows chưa import root-ca.crt)"),
    ], line_gap=7)

    # Arrows connecting Left and Right
    draw_arrow(draw, (760, 415), (840, 320), (186, 124, 24), width=3)
    draw_label_pill(draw, 800, 345, "Mount :ro", bg=(255, 248, 232), fg=(140, 82, 8), border=(186, 124, 24))

    draw_arrow(draw, (760, 620), (840, 420), (38, 97, 86), width=3)
    draw_label_pill(draw, 800, 515, "TLS / mTLS", bg=(235, 250, 245), fg=(22, 74, 64), border=(38, 97, 86))

    draw_arrow(draw, (760, 730), (840, 680), (176, 45, 56), width=3, dashed=True)
    draw_label_pill(draw, 800, 718, "Test lỗi", bg=(253, 241, 242), fg=(145, 28, 28), border=(176, 45, 56))

    draw_arrow(draw, (1190, 766), (1190, 748), (72, 92, 122), width=3)

    out_path = OUT_DIR / "arch_diagram.png"
    img.save(out_path, format="PNG")
    print(f"Saved {out_path} ({img.size})")


def build_lifecycle_diagram():
    W, H = 1600, 780
    img = Image.new("RGB", (W, H), (247, 249, 252))
    draw = ImageDraw.Draw(img)

    # Top Banner
    draw.rectangle((0, 0, W, 92), fill=(11, 43, 88))
    draw.text((38, 18), "SƠ ĐỒ 2. QUY TRÌNH QUẢN LÝ VÒNG ĐỜI CHỨNG THƯ SỐ X.509 TRONG THỰC NGHIỆM", font=FONT_TITLE, fill=(255, 255, 255))
    draw.text((38, 56), "Theo dõi trạng thái trên pki/intermediate/index.txt (Serial 1000 → 1007) qua 5 pha thực thi bằng OpenSSL & Nginx", font=FONT_SUBTITLE, fill=(200, 222, 250))

    phases = [
        ("PHA 1: KHỞI TẠO CA", "01_setup_ca.sh", (21, 76, 138), (240, 246, 255), [
            "• Sinh khóa Root CA 4096-bit",
            "• Sinh khóa Inter CA 2048-bit",
            "• Phân quyền chmod 600/700",
            "• Tạo index.txt, serial=1000",
            "• Xuất root-ca.crt, inter-ca.crt",
            "• Ghép ca-chain.crt & CRL đầu",
        ]),
        ("PHA 2: CSR & CẤP PHÁT", "02_issue_certs.sh", (26, 122, 74), (239, 250, 245), [
            "• Tạo cặp khóa + CSR cục bộ",
            "• Kiểm tra chính sách RA/CNF",
            "• Gắn SAN & EKU chuẩn X.509v3",
            "• Cấp 2 dịch vụ: secure (1000),",
            "  api (1001) & user alice (1002)",
            "• Tạo mẫu test: 1003, 1004, 1005",
        ]),
        ("PHA 3: VẬN HÀNH & KIỂM THỬ", "run_all_tests.sh", (13, 110, 145), (236, 248, 252), [
            "• Nginx nạp *.fullchain.crt",
            "• TC01: Verify chain → OK",
            "• TC02: TLS 1.3 → 200 OK",
            "• TC03: mTLS → 400 vs 200",
            "• TC04: Hết hạn 2020 → num=10",
            "• TC05: Rogue CA → num=20",
        ]),
        ("PHA 4: GIA HẠN (RENEWAL)", "04_renew_cert.sh (TC08)", (176, 106, 14), (255, 248, 234), [
            "• Sinh khóa mới api_renew.key",
            "• Ký cấp api.crt mới (730 ngày):",
            "  Serial 1006 [V]",
            "• Thu hồi api_old.crt (1001):",
            "  lý do superseded [R]",
            "• Cập nhật api.fullchain.crt",
        ]),
        ("PHA 5: THU HỒI & CẤP LẠI", "03_revoke + 05_reissue", (166, 38, 52), (253, 241, 243), [
            "• Thu hồi 1004 (revoked),",
            "  1005 (Bob), 1002 (Alice cũ)",
            "  với lý do keyCompromise [R]",
            "• Tái xuất ca-chain.crl.pem",
            "• Nginx reload → chặn HTTP 400",
            "• Cấp lại alice.crt Serial 1007",
        ]),
    ]

    card_w = 276
    gap = 34
    start_x = 42
    top_y = 128
    card_h = 396

    for idx, (p_title, p_script, hdr_col, bg_col, bullets) in enumerate(phases):
        x1 = start_x + idx * (card_w + gap)
        x2 = x1 + card_w
        y1 = top_y
        y2 = y1 + card_h
        draw_round_box(draw, (x1, y1, x2, y2), bg_col, hdr_col, radius=12, width=2)
        draw.rounded_rectangle((x1, y1, x2, y1 + 64), radius=12, fill=hdr_col, outline=hdr_col, width=2)
        draw.rectangle((x1 + 2, y1 + 48, x2 - 2, y1 + 66), fill=hdr_col)
        draw.text((x1 + 14, y1 + 12), p_title, font=FONT_H3, fill=(255, 255, 255))
        draw.text((x1 + 14, y1 + 36), p_script, font=FONT_SMALL, fill=(235, 242, 255))

        cy = y1 + 84
        for line in bullets:
            draw.text((x1 + 14, cy), line, font=FONT_SMALL, fill=(35, 40, 50))
            cy += 34

        if idx < len(phases) - 1:
            draw_arrow(draw, (x2 + 2, top_y + card_h // 2), (x2 + gap - 4, top_y + card_h // 2), (55, 70, 95), width=3)

    # Bottom Summary Strip: index.txt State Transition Timeline
    draw_round_box(draw, (42, 558, 1558, 742), (255, 255, 255), (60, 82, 118), radius=12, width=2)
    draw.text((64, 574), "Theo dõi Trạng thái Cơ sở dữ liệu CA (pki/intermediate/index.txt — 8 bản ghi kiểm chứng thực tế ngày 16/11/2026):", font=FONT_H3, fill=(21, 76, 138))

    rows = [
        ("Serial 1000 [V]", "secure.lab.local (Hợp lệ 365d)", (232, 246, 236), (22, 115, 58)),
        ("Serial 1001 [R]", "api_old (superseded → 1006)", (255, 244, 224), (168, 96, 12)),
        ("Serial 1002 [R]", "alice_1002_revoked (keyCompromise)", (253, 236, 238), (166, 38, 52)),
        ("Serial 1003 [V*]", "expired.lab.local (Hạn 2020 → num=10)", (255, 244, 224), (168, 96, 12)),
        ("Serial 1004 [R]", "revoked.lab.local (TC06 → num=23)", (253, 236, 238), (166, 38, 52)),
        ("Serial 1005 [R]", "Bob (TC07 mTLS CRL → HTTP 400)", (253, 236, 238), (166, 38, 52)),
        ("Serial 1006 [V]", "api.lab.local (Gia hạn 730d — TC08)", (232, 246, 236), (22, 115, 58)),
        ("Serial 1007 [V]", "Alice mới (Cấp lại — TC03 200 OK)", (232, 246, 236), (22, 115, 58)),
    ]

    bx, by = 64, 616
    bw, bh = 362, 48
    for i, (s_code, s_desc, s_bg, s_fg) in enumerate(rows):
        col = i % 4
        row = i // 4
        rx1 = bx + col * (bw + 16)
        ry1 = by + row * (bh + 14)
        draw_round_box(draw, (rx1, ry1, rx1 + bw, ry1 + bh), s_bg, s_fg, radius=8, width=2)
        draw.text((rx1 + 10, ry1 + 6), s_code, font=FONT_SMALL, fill=s_fg)
        draw.text((rx1 + 10, ry1 + 24), s_desc, font=FONT_SMALL, fill=(40, 45, 55))

    out_path = OUT_DIR / "lifecycle_diagram.png"
    img.save(out_path, format="PNG")
    print(f"Saved {out_path} ({img.size})")


if __name__ == "__main__":
    build_arch_diagram()
    build_lifecycle_diagram()
