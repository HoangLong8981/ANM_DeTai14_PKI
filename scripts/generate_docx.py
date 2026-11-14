import os
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

BASE_DIR = Path(__file__).resolve().parent.parent
IMG_DIR = BASE_DIR / "docs" / "report" / "images"

COLOR_PRIMARY = RGBColor(0x00, 0x2B, 0x5C)
COLOR_SECONDARY = RGBColor(0x11, 0x4B, 0x7A)
COLOR_SUBTEXT = RGBColor(0x44, 0x44, 0x44)
COLOR_BODY = RGBColor(0x22, 0x22, 0x22)
COLOR_PASS = RGBColor(0x00, 0x70, 0x20)
COLOR_MUTED = RGBColor(0x55, 0x55, 0x55)

FIGURES = [
    (
        1,
        "image7.png",
        "Trích xuất đặc tả chứng thư X.509v3 secure.crt có phần mở rộng SAN tường minh",
        "Xác nhận chứng thư máy chủ secure.crt được cấp bởi UTH Intermediate CA và khai báo đầy đủ SAN gồm DNS:secure.lab.local, DNS:localhost, IP Address:127.0.0.1.",
    ),
    (
        2,
        "image11.png",
        "Kiểm kê cơ sở dữ liệu CA (index.txt cho 2 dịch vụ + 1 người dùng) và quyền khóa riêng chmod 600",
        "Xác nhận index.txt ghi nhận đầy đủ chứng thư đã cấp cho secure.lab.local (Serial 1000), api.lab.local (Serial 1006 sau gia hạn) và Alice (Serial 1002), kèm kiểm tra stat trả về mode 600 trên toàn bộ 17 tệp .key.",
    ),
    (
        3,
        "image5.png",
        "Kết quả xác minh chuỗi tin cậy phân tầng (TC01 — openssl verify)",
        "Chứng minh lệnh openssl verify -CAfile ca-chain.crt secure.crt trả về trạng thái OK qua chuỗi tin cậy hai cấp.",
    ),
    (
        4,
        "image6.png",
        "Kết quả truy vấn HTTPS hợp lệ qua cURL trong container (TC02)",
        "Xác nhận kết nối HTTPS tới secure.lab.local sử dụng ca-chain.crt nhận phản hồi HTTP/1.1 200 OK từ máy chủ nginx/1.27.5.",
    ),
    (
        5,
        "image12.png",
        "Kết quả bắt tay TLS 1.3 và Verify return code: 0 (ok) qua openssl s_client -tls1_3 (TC02 bổ sung)",
        "Chứng minh kết nối tới secure.lab.local thiết lập giao thức TLSv1.3 với cipher TLS_AES_256_GCM_SHA384, khóa tạm thời X25519 (253 bits), chữ ký RSA-PSS trên SHA256 và Verify return code: 0 (ok).",
    ),
    (
        6,
        "image9.png",
        "Giao diện trình duyệt trên Windows tại https://localhost:8443 (cảnh báo chưa import Root CA)",
        "Dịch vụ web vẫn phản hồi 200 OK - Secure Web Service nhưng trình duyệt Windows hiển thị 'Không bảo mật' do Trust Store của Windows chưa import root-ca.crt và URL dùng localhost:8443 thay vì tên miền đầy đủ.",
    ),
    (
        7,
        "image8.png",
        "Thông tin chứng thư số máy chủ cấp bởi UTH Intermediate CA trên trình xem chứng chỉ",
        "Hiển thị thông tin phát hành CN=secure.lab.local bởi UTH Intermediate CA, thời hạn hiệu lực 05/11/2026–05/11/2027 và dấu vân tay SHA-256.",
    ),
    (
        8,
        "image10.png",
        "Kết quả xác thực hai chiều mTLS tại api.lab.local/mtls (TC03 — trước khi thu hồi alice.crt)",
        "Chứng minh Nginx từ chối kết nối thiếu chứng chỉ khách bằng HTTP/1.1 400 Bad Request và cho phép HTTP/1.1 200 OK kèm Client DN khi cung cấp alice.crt hợp lệ (Serial 1002).",
    ),
    (
        9,
        "image13.png",
        "Kết quả Nginx từ chối chứng chỉ alice.crt đã thu hồi qua ssl_crl (HTTP 400 + error 23)",
        "Chứng minh sau khi thu hồi alice.crt (Serial 1002, keyCompromise), yêu cầu mTLS tới api.lab.local/mtls bị Nginx trả về HTTP/1.1 400 Bad Request, log pki-web ghi nhận error (23:certificate revoked) và openssl verify -crl_check báo error 23.",
    ),
    (
        10,
        "image1.png",
        "Phát hiện và từ chối chứng thư hết hạn hiệu lực (TC04 — expired.lab.local)",
        "Chứng minh OpenSSL s_client bắt đúng lỗi verify error:num=10:certificate has expired (notAfter=Jan 2 00:00:00 2020 GMT) và cURL ngắt kết nối với mã lỗi (60).",
    ),
    (
        11,
        "image2.png",
        "Từ chối chứng thư không tin cậy cấp bởi Rogue CA (TC05 — untrusted.lab.local)",
        "Xác nhận chứng thư tự ký bởi Rogue CA độc lập không nằm trong ca-chain.crt bị chặn ngay với lỗi verify error:num=20:unable to get local issuer certificate và curl: (60).",
    ),
    (
        12,
        "image4.png",
        "Kiểm tra thu hồi chứng thư máy chủ qua danh sách CRL (TC06 — revoked.lab.local)",
        "Chứng minh cả openssl verify, openssl s_client kèm CRL và cURL --crlfile đều phát hiện revoked.crt đã bị thu hồi và trả về verify error:num=23:certificate revoked.",
    ),
    (
        13,
        "image3.png",
        "Kết quả thực thi bộ kiểm thử tự động do nhóm xây dựng (eval_rubric.sh) đạt 10.0 / 10.0",
        "Xác nhận toàn bộ tệp script dùng chuẩn xuống dòng LF, quyền khóa riêng hợp lệ (600/400) và cả 6 kịch bản TC01–TC06 đạt trạng thái PASS với tổng điểm 10.0 / 10.0.",
    ),
]


def set_cell_background(cell, fill_hex):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tc_pr.append(shd)


def set_cell_margins(cell, top=80, bottom=80, left=120, right=120):
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_mar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tc_pr.append(tc_mar)


def set_table_borders(table, color="CBD5E1", sz="4"):
    tbl_pr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:bottom w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:left w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:right w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:insideH w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:insideV w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'</w:tblBorders>'
    )
    tbl_pr.append(borders)


def set_row_cant_split(row):
    tr_pr = row._tr.get_or_add_trPr()
    tr_pr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))


def set_repeat_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    tr_pr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))


def add_page_number_field(run):
    fld_char_begin = parse_xml(f'<w:fldChar {nsdecls("w")} w:fldCharType="begin"/>')
    instr_text = parse_xml(f'<w:instrText {nsdecls("w")} xml:space="preserve"> PAGE </w:instrText>')
    fld_char_sep = parse_xml(f'<w:fldChar {nsdecls("w")} w:fldCharType="separate"/>')
    fld_char_end = parse_xml(f'<w:fldChar {nsdecls("w")} w:fldCharType="end"/>')
    run._r.append(fld_char_begin)
    run._r.append(instr_text)
    run._r.append(fld_char_sep)
    run._r.append(fld_char_end)


def configure_base_document():
    doc = Document()
    for s in doc.sections:
        s.top_margin = Inches(0.85)
        s.bottom_margin = Inches(0.85)
        s.left_margin = Inches(0.95)
        s.right_margin = Inches(0.95)
        s.different_first_page_header_footer = True

        hdr = s.header
        hp = hdr.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hr = hp.add_run("UTH — Đề tài 14: Xây dựng PKI thu nhỏ và quản lý vòng đời chứng thư số")
        hr.font.name = "Times New Roman"
        hr.font.size = Pt(9)
        hr.font.italic = True
        hr.font.color.rgb = COLOR_MUTED

        ftr = s.footer
        fp = ftr.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        fr_prefix = fp.add_run("Trang ")
        fr_prefix.font.name = "Times New Roman"
        fr_prefix.font.size = Pt(9.5)
        fr_prefix.font.color.rgb = COLOR_MUTED
        fr_num = fp.add_run()
        fr_num.font.name = "Times New Roman"
        fr_num.font.size = Pt(9.5)
        fr_num.font.color.rgb = COLOR_MUTED
        add_page_number_field(fr_num)

    style_normal = doc.styles["Normal"]
    font = style_normal.font
    font.name = "Times New Roman"
    font.size = Pt(11.5)
    font.color.rgb = COLOR_BODY
    r_pr = style_normal.element.get_or_add_rPr()
    r_fonts = r_pr.find(qn("w:rFonts"))
    if r_fonts is None:
        r_fonts = OxmlElement("w:rFonts")
        r_pr.insert(0, r_fonts)
    r_fonts.set(qn("w:ascii"), "Times New Roman")
    r_fonts.set(qn("w:hAnsi"), "Times New Roman")
    r_fonts.set(qn("w:cs"), "Times New Roman")

    style_normal.paragraph_format.line_spacing = 1.2
    style_normal.paragraph_format.space_after = Pt(5)
    return doc


def make_helpers(doc):
    def add_h1(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text)
        r.font.size = Pt(13)
        r.bold = True
        r.font.color.rgb = COLOR_PRIMARY
        return p

    def add_h2(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text)
        r.font.size = Pt(12)
        r.bold = True
        r.font.color.rgb = COLOR_SECONDARY
        return p

    def add_h3(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text)
        r.font.size = Pt(11.5)
        r.bold = True
        r.font.color.rgb = COLOR_BODY
        return p

    def add_p(text, bold_prefix=None, space_after=5, indent_inches=0.0):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_after = Pt(space_after)
        if indent_inches:
            p.paragraph_format.left_indent = Inches(indent_inches)
        if bold_prefix:
            rb = p.add_run(bold_prefix)
            rb.bold = True
        p.add_run(text)
        return p

    def add_bullet(bold_prefix, text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.left_indent = Inches(0.28)
        p.paragraph_format.first_line_indent = Inches(-0.14)
        p.paragraph_format.space_after = Pt(4)
        p.add_run("• ")
        if bold_prefix:
            rb = p.add_run(bold_prefix)
            rb.bold = True
        p.add_run(text)
        return p

    def add_callout(title, body):
        tbl = doc.add_table(rows=1, cols=1)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        cell = tbl.cell(0, 0)
        cell.width = Inches(6.6)
        set_cell_background(cell, "EEF4FA")
        set_cell_margins(cell, top=100, bottom=100, left=160, right=160)
        set_table_borders(tbl, color="8AB4D8", sz="6")
        set_row_cant_split(tbl.rows[0])
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_after = Pt(0)
        rt = p.add_run(title + ": ")
        rt.bold = True
        rt.font.size = Pt(10.5)
        rt.font.color.rgb = COLOR_PRIMARY
        rb = p.add_run(body)
        rb.font.size = Pt(10.5)
        spacer = doc.add_paragraph()
        spacer.paragraph_format.space_after = Pt(4)

    def add_code(text, label=None):
        if label:
            pl = doc.add_paragraph()
            pl.paragraph_format.space_before = Pt(4)
            pl.paragraph_format.space_after = Pt(2)
            pl.paragraph_format.keep_with_next = True
            rl = pl.add_run(label)
            rl.font.size = Pt(10)
            rl.bold = True
            rl.font.color.rgb = COLOR_SUBTEXT
        tbl = doc.add_table(rows=1, cols=1)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        cell = tbl.cell(0, 0)
        cell.width = Inches(6.6)
        set_cell_background(cell, "F4F6F9")
        set_cell_margins(cell, top=100, bottom=100, left=150, right=150)
        set_table_borders(tbl, color="D6DEE8", sz="4")
        set_row_cant_split(tbl.rows[0])
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.05
        r = p.add_run(text)
        r.font.name = "Consolas"
        r.font.size = Pt(8.8)
        r.font.color.rgb = COLOR_BODY
        spacer = doc.add_paragraph()
        spacer.paragraph_format.space_after = Pt(4)

    def add_styled_table(caption, headers, rows, col_widths, center_cols=None, pass_col=None):
        if caption:
            pt = doc.add_paragraph()
            pt.paragraph_format.space_before = Pt(8)
            pt.paragraph_format.space_after = Pt(3)
            pt.paragraph_format.keep_with_next = True
            rt = pt.add_run(caption)
            rt.font.size = Pt(10)
            rt.bold = True
            rt.font.color.rgb = COLOR_PRIMARY

        tbl = doc.add_table(rows=len(rows) + 1, cols=len(headers))
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        tbl.autofit = False
        set_table_borders(tbl, color="B8C7D9", sz="4")

        set_repeat_header(tbl.rows[0])
        set_row_cant_split(tbl.rows[0])
        for c_idx, h in enumerate(headers):
            cell = tbl.cell(0, c_idx)
            cell.width = Inches(col_widths[c_idx])
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            set_cell_background(cell, "003366")
            set_cell_margins(cell, 80, 80, 90, 90)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(h)
            r.bold = True
            r.font.size = Pt(9.2)
            r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

        center_cols = set(center_cols or [])
        for r_idx, row_vals in enumerate(rows, start=1):
            set_row_cant_split(tbl.rows[r_idx])
            bg = "F7FAFC" if r_idx % 2 == 1 else "FFFFFF"
            for c_idx, val in enumerate(row_vals):
                cell = tbl.cell(r_idx, c_idx)
                cell.width = Inches(col_widths[c_idx])
                cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
                set_cell_background(cell, bg)
                set_cell_margins(cell, 65, 65, 85, 85)
                p = cell.paragraphs[0]
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_idx in center_cols else WD_ALIGN_PARAGRAPH.LEFT
                p.paragraph_format.space_after = Pt(0)
                r = p.add_run(val)
                r.font.size = Pt(8.8)
                if c_idx == 0:
                    r.bold = True
                if pass_col is not None and c_idx == pass_col:
                    r.bold = True
                    r.font.color.rgb = COLOR_PASS

        spacer = doc.add_paragraph()
        spacer.paragraph_format.space_after = Pt(5)
        return tbl

    def add_fig(fig_num, img_name, title, desc=None):
        img_path = IMG_DIR / img_name
        if not img_path.exists():
            raise FileNotFoundError(f"Missing screenshot image: {img_path}")
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(6)
        p_img.paragraph_format.space_after = Pt(3)
        p_img.paragraph_format.keep_with_next = True
        run_img = p_img.add_run()
        run_img.add_picture(str(img_path), width=Inches(5.8))

        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_after = Pt(2 if desc else 10)
        if desc:
            p_cap.paragraph_format.keep_with_next = True
        r_cap = p_cap.add_run(f"Fig. {fig_num}: {title}")
        r_cap.font.size = Pt(10)
        r_cap.bold = True
        r_cap.font.color.rgb = COLOR_PRIMARY

        if desc:
            p_desc = doc.add_paragraph()
            p_desc.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_desc.paragraph_format.space_after = Pt(10)
            r_desc = p_desc.add_run(desc)
            r_desc.font.size = Pt(9.5)
            r_desc.italic = True
            r_desc.font.color.rgb = COLOR_SUBTEXT

    return {
        "h1": add_h1,
        "h2": add_h2,
        "h3": add_h3,
        "p": add_p,
        "bullet": add_bullet,
        "callout": add_callout,
        "code": add_code,
        "table": add_styled_table,
        "fig": add_fig,
    }


def add_cover_header(doc, subtitle_text, doc_type_banner):
    p_uni = doc.add_paragraph()
    p_uni.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_uni.paragraph_format.space_after = Pt(4)
    r_uni = p_uni.add_run(
        "TRƯỜNG ĐẠI HỌC GIAO THÔNG VẬN TẢI TP. HỒ CHÍ MINH (UTH)\n"
        "KHOA CÔNG NGHỆ THÔNG TIN — BỘ MÔN AN NINH MẠNG"
    )
    r_uni.font.size = Pt(12)
    r_uni.bold = True
    r_uni.font.color.rgb = COLOR_PRIMARY

    p_course = doc.add_paragraph()
    p_course.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_course.paragraph_format.space_before = Pt(12)
    p_course.paragraph_format.space_after = Pt(24)
    r_course = p_course.add_run(
        f"{doc_type_banner}\n"
        "MÔN HỌC: AN NINH MẠNG (3 TÍN CHỈ) — GIẢNG VIÊN HƯỚNG DẪN: TS. LÊ QUỐC TUẤN"
    )
    r_course.font.size = Pt(11.5)
    r_course.bold = True
    r_course.font.color.rgb = COLOR_SUBTEXT

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(12)
    p_title.paragraph_format.space_after = Pt(10)
    r_title = p_title.add_run(
        "ĐỀ TÀI 14:\n"
        "XÂY DỰNG HẠ TẦNG KHÓA CÔNG KHAI (PKI) THU NHỎ\n"
        "VÀ QUẢN LÝ VÒNG ĐỜI CHỨNG THƯ SỐ"
    )
    r_title.font.size = Pt(16.5)
    r_title.bold = True
    r_title.font.color.rgb = COLOR_PRIMARY

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(24)
    r_sub = p_sub.add_run(subtitle_text)
    r_sub.font.size = Pt(11.5)
    r_sub.italic = True
    r_sub.font.color.rgb = COLOR_MUTED

    # Cover Metadata Box / Table
    meta_rows = [
        ("Nhóm thực hiện:", "[Tên / Mã nhóm thực hiện — Đề tài 14]"),
        ("Thành viên / MSSV:", "[Họ và tên 1 - MSSV], [Họ và tên 2 - MSSV], [Họ và tên 3 - MSSV]"),
        ("Lớp:", "[Mã lớp học phần]"),
        ("Giảng viên hướng dẫn:", "TS. Lê Quốc Tuấn"),
        ("Môi trường thực nghiệm:", "Docker Compose (các container Linux Alpine) chạy trên nền hệ điều hành Windows"),
        ("Thời gian hoàn thành:", "TP. Hồ Chí Minh, tháng 11/2026"),
    ]
    tbl = doc.add_table(rows=len(meta_rows), cols=2)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    set_table_borders(tbl, color="8AB4D8", sz="6")
    for idx, (k, v) in enumerate(meta_rows):
        set_row_cant_split(tbl.rows[idx])
        bg = "F4F8FC" if idx % 2 == 0 else "FFFFFF"
        c0 = tbl.cell(idx, 0)
        c1 = tbl.cell(idx, 1)
        c0.width = Inches(2.2)
        c1.width = Inches(4.4)
        set_cell_background(c0, "E8F0F8")
        set_cell_background(c1, bg)
        set_cell_margins(c0, 85, 85, 120, 120)
        set_cell_margins(c1, 85, 85, 120, 120)
        p0 = c0.paragraphs[0]
        p0.paragraph_format.space_after = Pt(0)
        rk = p0.add_run(k)
        rk.bold = True
        rk.font.size = Pt(10.5)
        rk.font.color.rgb = COLOR_PRIMARY
        p1 = c1.paragraphs[0]
        p1.paragraph_format.space_after = Pt(0)
        rv = p1.add_run(v)
        rv.font.size = Pt(10.5)


def create_report():
    doc = configure_base_document()
    h = make_helpers(doc)

    # -------------------------------------------------------------
    # PAGE 1: COVER PAGE
    # -------------------------------------------------------------
    add_cover_header(
        doc,
        "Mô hình PKI phân tầng hai cấp (Root CA & Intermediate CA), triển khai HTTPS/mTLS trên Nginx "
        "và kiểm chứng thu hồi CRL bằng OpenSSL trên Docker Compose",
        "BÁO CÁO ĐỒ ÁN MÔN HỌC",
    )
    doc.add_page_break()

    # -------------------------------------------------------------
    # PAGE 2: TABLE OF CONTENTS (MỤC LỤC)
    # -------------------------------------------------------------
    p_toc_hdr = doc.add_paragraph()
    p_toc_hdr.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_toc_hdr.paragraph_format.space_before = Pt(4)
    p_toc_hdr.paragraph_format.space_after = Pt(12)
    r_toc = p_toc_hdr.add_run("MỤC LỤC (TABLE OF CONTENTS)")
    r_toc.font.size = Pt(14)
    r_toc.bold = True
    r_toc.font.color.rgb = COLOR_PRIMARY

    toc_entries = [
        ("Tóm tắt (Abstract) & Từ khóa", True),
        ("I. GIỚI THIỆU (INTRODUCTION)", True),
        ("    A. Bối cảnh An ninh Mạng và Vai trò của Hạ tầng Khóa công khai", False),
        ("    B. Vấn đề Nghiên cứu và Thách thức Thực tiễn", False),
        ("    C. Mục tiêu và Đóng góp Chính của Đề tài", False),
        ("    D. Cấu trúc của Báo cáo", False),
        ("II. CƠ SỞ LÝ THUYẾT VÀ KIẾN TRÚC HỆ THỐNG (THEORY & ARCHITECTURE)", True),
        ("    A. Mô hình Cơ quan Chứng thực Phân tầng Hai cấp và Công thức Chuỗi tin cậy", False),
        ("    B. Đặc tả Kỹ thuật Chứng thư X.509v3, SAN và Khóa Mật mã", False),
        ("    C. Vai trò Registration Authority (RA), Cơ chế CSR và Vòng đời Chứng thư", False),
        ("    D. So sánh Cơ chế Kiểm tra Thu hồi CRL và OCSP", False),
        ("    E. Phân tích Rủi ro Lộ Khóa riêng theo 3 Cấp độ và Biện pháp Giảm thiểu", False),
        ("    F. Liên hệ Hạ tầng PKI với Quy trình Bắt tay TLS 1.3", False),
        ("    G. Kiến trúc Mạng Docker Cô lập (pki-net) trên Nền Windows", False),
        ("III. TRIỂN KHAI VÀ KẾT QUẢ THỰC NGHIỆM (IMPLEMENTATION & RESULTS)", True),
        ("    A. Quy trình Lệnh OpenSSL Thực tế qua các Pha Vòng đời và Kiểm kê Chứng thư", False),
        ("    B. Cấu hình Máy chủ Dịch vụ Mạng Nginx (Virtual Hosts & CRL)", False),
        ("    C. Phân tích Sáu Kịch bản Kiểm thử (TC01–TC06) và Thực nghiệm Từ chối mTLS qua CRL", False),
        ("    D. Tổng hợp Kết quả Kiểm thử và Đánh giá Tự động", False),
        ("IV. KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN (CONCLUSION & FUTURE WORK)", True),
        ("    A. Kết luận", False),
        ("    B. Bài học Kinh nghiệm", False),
        ("    C. Hướng phát triển", False),
        ("DANH MỤC BẢNG BIỂU (TABLE I – TABLE IV)", True),
        ("    TABLE I. So sánh đặc tính kỹ thuật các cấp chứng thư trong hệ thống PKI", False),
        ("    TABLE II. So sánh cơ chế kiểm tra thu hồi CRL và OCSP", False),
        ("    TABLE III. Kiểm kê chứng thư phát hành (2 dịch vụ, 1 người dùng) và chứng thư kiểm thử", False),
        ("    TABLE IV. Ma trận đối chiếu kết quả kiểm thử thực nghiệm (TC01–TC06 và mTLS CRL)", False),
        ("DANH MỤC HÌNH ẢNH MINH CHỨNG (Fig. 1 – Fig. 13)", True),
        ("TÀI LIỆU THAM KHẢO (REFERENCES)", True),
    ]

    toc_tbl = doc.add_table(rows=len(toc_entries), cols=1)
    toc_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    toc_tbl.autofit = False
    set_table_borders(toc_tbl, color="DCE6F2", sz="4")
    for idx, (label, is_major) in enumerate(toc_entries):
        set_row_cant_split(toc_tbl.rows[idx])
        cell = toc_tbl.cell(idx, 0)
        cell.width = Inches(6.6)
        set_cell_background(cell, "EFF5FB" if is_major else "FFFFFF")
        set_cell_margins(cell, 45, 45, 110, 110)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(label)
        r.font.size = Pt(10.2 if is_major else 9.8)
        r.bold = is_major
        if is_major:
            r.font.color.rgb = COLOR_PRIMARY

    doc.add_page_break()

    # -------------------------------------------------------------
    # ABSTRACT & KEYWORDS
    # -------------------------------------------------------------
    p_abs = doc.add_paragraph()
    p_abs.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_abs.paragraph_format.space_after = Pt(6)
    r_at = p_abs.add_run("Tóm tắt (Abstract)— ")
    r_at.bold = True
    r_at.font.size = Pt(11)
    r_ab = p_abs.add_run(
        "Hạ tầng khóa công khai (Public Key Infrastructure — PKI) đóng vai trò nền tảng trong việc duy trì lòng tin số, "
        "bảo đảm các thuộc tính bảo mật, toàn vẹn dữ liệu và xác thực định danh trên các hệ thống mạng hiện đại. Tuy nhiên, "
        "việc thiết kế kiến trúc phân tầng và kiểm soát chặt chẽ vòng đời chứng thư số X.509—từ khởi tạo khóa, phê duyệt CSR, "
        "xác minh chuỗi tin cậy, gia hạn đến thu hồi khẩn cấp khi lộ khóa—đòi hỏi tuân thủ nghiêm ngặt các chuẩn giao thức và "
        "cấu hình dịch vụ. Báo cáo này trình bày quá trình xây dựng và kiểm chứng một mô hình PKI thu nhỏ phân tầng hai cấp "
        "(gồm Root CA RSA 4096-bit tự ký và Intermediate CA RSA 2048-bit ký phát hành) triển khai bằng Docker Compose (các "
        "container Linux Alpine) chạy trên nền hệ điều hành Windows. Hệ thống cấp phát chứng thư số X.509v3 khai báo Subject "
        "Alternative Name (SAN) tường minh cho hai dịch vụ mạng (secure.lab.local và api.lab.local) cùng một người dùng cuối "
        "(alice) phục vụ xác thực hai chiều (Mutual TLS — mTLS) trên Nginx, đồng thời thiết lập cơ chế thu hồi thông qua Danh "
        "sách thu hồi chứng thư (CRL). Kết quả kiểm chứng trên sáu kịch bản độc lập (TC01–TC06) cùng phép thử thu hồi chứng thư "
        "mTLS trên api.lab.local xác nhận hệ thống thiết lập kênh truyền TLS 1.3 hợp lệ (Verify return code: 0), thực thi kiểm "
        "soát truy cập mTLS và phát hiện chính xác các trạng thái hết hạn (num=10), không tin cậy (num=20) và bị thu hồi (num=23)."
    )
    r_ab.font.size = Pt(11)
    r_ab.italic = True

    p_kw = doc.add_paragraph()
    p_kw.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_kw.paragraph_format.space_after = Pt(12)
    r_kt = p_kw.add_run("Từ khóa (Keywords)— ")
    r_kt.bold = True
    r_kt.font.size = Pt(11)
    r_kb = p_kw.add_run(
        "Hạ tầng khóa công khai (PKI), Chứng thư số X.509v3, Subject Alternative Name (SAN), Xác thực hai chiều (mTLS), "
        "Danh sách thu hồi chứng thư (CRL), TLS 1.3, Chuỗi tin cậy (Chain of Trust)."
    )
    r_kb.font.size = Pt(11)
    r_kb.italic = True

    # -------------------------------------------------------------
    # SECTION I. GIỚI THIỆU (INTRODUCTION)
    # -------------------------------------------------------------
    h["h1"]("I. GIỚI THIỆU (INTRODUCTION)")

    h["h2"]("A. Bối cảnh An ninh Mạng và Vai trò của Hạ tầng Khóa công khai")
    h["p"](
        "Trong bối cảnh các hệ thống dịch vụ web và API phân tán vận hành trên hạ tầng mạng phức tạp, bảo mật kênh truyền và "
        "xác thực định danh thực thể là yêu cầu kỹ thuật bắt buộc [1], [2]. Mật mã bất đối xứng (Asymmetric Cryptography) cung cấp "
        "cơ sở toán học cho bài toán trao đổi khóa và chữ ký số [1], [3, Mục 3.3.1–3.3.2]. Tuy nhiên, mã hóa đường truyền đơn "
        "thuần không tự bảo đảm bên nhận là thực thể hợp lệ nếu thiếu cơ chế ràng buộc khóa công khai với danh tính tin cậy [1], "
        "[3, Mục 3.3.1–3.3.5]. Khi không có bên thứ ba đáng tin cậy chứng thực khóa công khai, hệ thống đối mặt trực tiếp với "
        "nguy cơ tấn công xen giữa (Man-in-the-Middle — MitM), trong đó kẻ tấn công chèn khóa giả mạo để nghe lén hoặc chỉnh "
        "sửa lưu lượng [2], [3, Mục 3.3.1]."
    )
    h["p"](
        "Để giảm thiểu nguy cơ mạo danh, Hạ tầng Khóa công khai (Public Key Infrastructure — PKI) thiết lập khung quản trị lòng "
        "tin số dựa trên chuẩn chứng thư X.509 [1, Mục 4.5], [2, Mục 23.2], [3, Mục 3.3.2]. Thông qua Tổ chức chứng thực "
        "(Certification Authority — CA) ký số gắn kết khóa công khai với thông tin định danh của thực thể cuối (End-Entity), các "
        "giao thức như TLS 1.3 và cơ chế xác thực hai chiều (Mutual TLS — mTLS) có thể kiểm định danh tính đối tác trước khi trao "
        "đổi dữ liệu ứng dụng [1, Mục 6.2–6.3], [3, tr. 52–53]."
    )

    h["h2"]("B. Vấn đề Nghiên cứu và Thách thức Thực tiễn")
    h["p"](
        "Việc triển khai và vận hành một hạ tầng PKI đáp ứng yêu cầu an ninh thực tế thường gặp bốn thách thức kỹ thuật cốt lõi:"
    )
    h["p"](
        "1) Rủi ro của mô hình CA đơn tầng: Sử dụng trực tiếp một Root CA tự ký để cấp phát toàn bộ chứng thư máy chủ và người "
        "dùng làm tăng bề mặt tấn công đối với điểm neo tin cậy. Nếu khóa riêng của Root CA bị lộ, toàn bộ hạ tầng mất khả năng "
        "tin cậy và việc thu hồi thủ công trên mọi Trust Store rất tốn kém [1], [3, Mục 3.3.3]. Mô hình CA phân tầng hai cấp "
        "(Root CA kết hợp Intermediate CA) tách biệt gốc tin cậy ngoại tuyến khỏi tác vụ cấp phát trực tuyến [1], [2].",
        space_after=4,
    )
    h["p"](
        "2) Ràng buộc phần mở rộng X.509v3 và SAN: Các trình duyệt hiện đại và ứng dụng HTTPS/TLS đã loại bỏ việc đối chiếu tên "
        "miền chỉ qua trường Common Name (CN), bắt buộc chứng thư máy chủ phải khai báo phần mở rộng Subject Alternative Name "
        "(SAN) cùng các ràng buộc sử dụng khóa phù hợp [1, Mục 4.5], [3, tr. 53, 99].",
        space_after=4,
    )
    h["p"](
        "3) Kiểm soát thu hồi chứng thư trước hạn: Khi khóa riêng nghi ngờ bị rò rỉ hoặc nhân sự/dịch vụ ngừng hoạt động, chứng "
        "thư phải bị vô hiệu hóa ngay qua Danh sách thu hồi chứng thư (CRL) hoặc giao thức kiểm tra trực tuyến OCSP [1, Mục 4.5], "
        "[2, Mục 23.2], [3, Mục 3.3.4], đồng thời đồng bộ kịp thời tới máy chủ dịch vụ (như chỉ thị ssl_crl trên Nginx trong lab).",
        space_after=4,
    )
    h["p"](
        "4) Xác thực hai chiều (mTLS) ở tầng ứng dụng: Máy chủ xác thực ngược danh tính máy khách qua Client Certificate đòi hỏi "
        "phân tách mục đích sử dụng khóa xác thực khách, kiểm tra chuỗi tin cậy và tra cứu tình trạng thu hồi đầy đủ cho cả tầng "
        "CA trung gian lẫn chứng thư người dùng [1, Mục 4.5–4.6], [3, Mục 3.3.5].",
        space_after=6,
    )

    h["h2"]("C. Mục tiêu và Đóng góp Chính của Đề tài")
    h["p"](
        "Bám sát mục tiêu đề cương môn học An ninh Mạng (Đề tài 14: Xây dựng PKI thu nhỏ và quản lý vòng đời chứng thư), đồ án "
        "đã xây dựng và kiểm chứng hoàn chỉnh các hạng mục sau:"
    )
    h["bullet"](
        "Kiến trúc PKI phân tầng hai cấp: ",
        "Thiết lập Root CA (RSA 4096-bit tự ký) và Intermediate CA (RSA 2048-bit ký phát hành với pathlen:0), sử dụng hàm "
        "băm SHA-256 trên nền OpenSSL 3.3.7.",
    )
    h["bullet"](
        "Phát hành chứng thư X.509v3 cho 2 dịch vụ và 1 người dùng: ",
        "Cấp phát chứng thư có SAN tường minh cho secure.lab.local (Serial 1000) và api.lab.local (Serial 1001, sau gia hạn "
        "thành Serial 1006), cùng chứng thư người dùng cho Alice (Serial 1002, EKU clientAuth).",
    )
    h["bullet"](
        "Triển khai HTTPS (TLS 1.3) và xác thực hai chiều mTLS trên Nginx: ",
        "Cấu hình dịch vụ Web HTTPS và API mTLS (nginx:1.27-alpine), chứng minh cơ chế chặn truy cập thiếu chứng chỉ (HTTP 400), "
        "cho phép truy cập khi có chứng chỉ hợp lệ (HTTP 200) và từ chối chứng chỉ đã thu hồi qua ssl_crl.",
    )
    h["bullet"](
        "Thực nghiệm đầy đủ 4 trạng thái vòng đời và thu hồi CRL: ",
        "Trình diễn các trạng thái Hợp lệ, Hết hạn (num=10), Không tin cậy từ Rogue CA (num=20) và Thu hồi qua CRL (num=23) "
        "cho cả chứng thư máy chủ (revoked.lab.local) lẫn chứng thư người dùng (alice.crt trên api.lab.local/mtls).",
    )
    h["bullet"](
        "Đóng gói cô lập và kiểm thử tự động: ",
        "Triển khai toàn bộ trong Docker Compose (các container Linux Alpine) chạy trên nền hệ điều hành Windows; bộ kiểm thử "
        "tự động do nhóm xây dựng (eval_rubric.sh) đạt 10.0 / 10.0 điểm trên 6 kịch bản TC01–TC06 và các tiêu chí kiểm tra định dạng, quyền tệp khóa.",
    )

    h["h2"]("D. Cấu trúc của Báo cáo")
    h["p"](
        "Phần tiếp theo của báo cáo được bố cục như sau: Phần II trình bày cơ sở lý thuyết PKI, mô hình hai cấp, vai trò RA/CSR, "
        "so sánh CRL và OCSP, phân tích rủi ro lộ khóa riêng, liên hệ TLS 1.3 và kiến trúc mạng Docker; Phần III trình bày quy "
        "trình lệnh OpenSSL đầy đủ qua các pha vòng đời, cấu hình Nginx thực tế, phân tích 6 ca kiểm thử kèm bằng chứng từ nhật ký "
        "kiểm chứng; Phần IV tổng kết bài học kỹ thuật và đề xuất hướng phát triển."
    )

    # -------------------------------------------------------------
    # SECTION II. CƠ SỞ LÝ THUYẾT VÀ KIẾN TRÚC HỆ THỐNG
    # -------------------------------------------------------------
    h["h1"]("II. CƠ SỞ LÝ THUYẾT VÀ KIẾN TRÚC HỆ THỐNG (THEORY & ARCHITECTURE)")

    h["h2"]("A. Mô hình Cơ quan Chứng thực Phân tầng Hai cấp và Công thức Chuỗi tin cậy")
    h["p"](
        "Hệ thống áp dụng kiến trúc CA phân tầng hai cấp gồm Root CA và Intermediate CA nhằm tách biệt gốc tin cậy khỏi tác vụ "
        "cấp phát hàng ngày [1], [3, Mục 3.3.3]:"
    )
    h["p"](
        "1) Root CA (UTH Root CA): Đóng vai trò điểm neo tin cậy (Trust Anchor) [3, Mục 3.3.3], sở hữu cặp khóa RSA 4096-bit và "
        "chứng thư tự ký thời hạn 3650 ngày (10 năm) kèm phần mở rộng ràng buộc chứng nhận CA (basicConstraints = critical, CA:true) "
        "[1, Mục 4.5]. Root CA chỉ hoạt động để ký chứng thư cho Intermediate CA hoặc tái xuất root.crl.pem [1], [2, Mục 23.3].",
        space_after=4,
    )
    h["callout"](
        "Lưu ý kiến trúc (Mô phỏng trong Docker và Thực tế sản xuất)",
        "Trong môi trường Docker Compose của bài lab, việc tách thư mục pki/root/ để giữ Root CA 'ngoại tuyến' chỉ mang tính "
        "mô phỏng về mặt logic và tổ chức thư mục. Trong hạ tầng sản xuất thực tế, khóa riêng Root CA bắt buộc phải lưu trữ "
        "ngoại tuyến tách biệt vật lý khỏi mạng hoặc trong mô-đun bảo mật phần cứng (HSM) [1], [3, Mục 3.3.3].",
    )
    h["p"](
        "2) Intermediate CA (UTH Intermediate CA): Là Issuing CA trực tuyến, sở hữu cặp khóa RSA 2048-bit và được Root CA ký chứng "
        "thư thời hạn 1825 ngày (5 năm) kèm ràng buộc chứng nhận trung gian (basicConstraints = critical, CA:true, pathlen:0 — "
        "chỉ được phép ký phát hành chứng thư thực thể cuối, không thể ủy quyền thêm CA cấp dưới) [1, Mục 4.5], [3, Mục 3.3.3].",
        space_after=4,
    )
    h["p"](
        "Về mặt mật mã học trong chuẩn X.509 [1, Mục 3.6, 4.5], [2, Chương 21, Mục 23.2], [3, Mục 3.3.2, 3.3.5], việc xác lập "
        "Chuỗi tin cậy (Chain of Trust) không thực hiện thao tác 'giải mã' toàn bộ chứng thư để đối chiếu, vì các lược đồ chữ ký "
        "hiện đại vận hành thông qua cặp hàm ký (Sign) và hàm xác minh (Verify) tính trên giá trị băm của khối dữ liệu cần ký "
        "(TBSCertificate — To-Be-Signed Certificate):"
    )
    h["code"](
        "# Giai đoạn ký phát hành (Issuing):\n"
        "S_Inter  = Sign(K_Root_Private,  Hash(TBSCertificate_Inter))        (1)\n"
        "S_Entity = Sign(K_Inter_Private, Hash(TBSCertificate_Entity))       (2)\n\n"
        "# Giai đoạn xác minh Chuỗi tin cậy (Verification):\n"
        "Verify(K_Root_Public,  Hash(TBSCertificate_Inter),  S_Inter)  = True (3)\n"
        "Verify(K_Inter_Public, Hash(TBSCertificate_Entity), S_Entity) = True (4)"
    )
    h["p"](
        "Theo cấu trúc chứng thư X.509 [1, Mục 4.5], trường giá trị chữ ký là đầu ra của quá trình ký số nên không thể tính băm "
        "trên toàn bộ tệp chứng thư đóng gói sẵn. Khối TBSCertificate chứa toàn bộ thông tin định danh và ràng buộc cần bảo vệ "
        "toàn vẹn (phiên bản, số sê-ri, định danh thuật toán ký, Issuer, thời hạn hiệu lực, Subject, khóa công khai của chủ thể "
        "và các phần mở rộng như SAN, KeyUsage, BasicConstraints) [1, Mục 4.5], [3, Mục 3.3.2, 3.3.5]."
    )

    h["h2"]("B. Đặc tả Kỹ thuật Chứng thư X.509v3, SAN và Khóa Mật mã")
    h["p"](
        "Một điểm kỹ thuật quan trọng cần phân biệt rõ là nguồn gốc yêu cầu khai báo Subject Alternative Name (SAN): việc bắt "
        "buộc chứng thư máy chủ phải khai báo tên miền hoặc IP trong phần mở rộng SAN thay vì dựa vào Common Name (CN) "
        "không phải là quy định riêng của giao thức TLS 1.3. Theo chuẩn X.509v3, trường Subject truyền thống không đủ linh hoạt "
        "cho định danh dịch vụ Internet nên phần mở rộng SAN được bổ sung để liệt kê tên miền/IP đích [1, Mục 4.5]; đồng thời các "
        "trình duyệt web và ứng dụng HTTPS hiện đại yêu cầu đối chiếu qua SAN (áp dụng đồng nhất cho cả TLS 1.2 lẫn TLS 1.3) [3, tr. 53, 99]."
    )
    h["p"](
        "Bảng I tổng hợp thông số mật mã, phần mở rộng X.509v3 và định danh thực tế đã kiểm chứng của hệ thống:"
    )

    t1_headers = ["Đặc tính kỹ thuật", "Root CA (Gốc)", "Intermediate CA (Trung gian)", "End-Entity (Server / Client)"]
    t1_rows = [
        ("Cặp khóa mật mã", "RSA 4096-bit", "RSA 2048-bit", "RSA 2048-bit"),
        ("Thuật toán băm chữ ký", "SHA-256 (sha256WithRSAEncryption)", "SHA-256 (sha256WithRSAEncryption)", "SHA-256 (sha256WithRSAEncryption)"),
        (
            "Thời hạn hiệu lực",
            "10 năm (3650 ngày)",
            "5 năm (1825 ngày)",
            "Server: 1 năm (365 ngày) cho secure, 2 năm (730 ngày) sau gia hạn cho api; Client: 1 năm (365 ngày)",
        ),
        ("Thực thể cấp phát", "Tự ký (Self-Signed)", "Ký bởi UTH Root CA", "Ký bởi UTH Intermediate CA"),
        ("Ràng buộc cơ bản (BasicConstraints)", "critical, CA:TRUE", "critical, CA:TRUE, pathlen:0", "CA:FALSE"),
        ("Mục đích dùng khóa (KeyUsage)", "digitalSignature, keyCertSign, cRLSign", "digitalSignature, keyCertSign, cRLSign", "critical, digitalSignature, keyEncipherment"),
        ("Mở rộng dùng khóa (EKU)", "Không áp dụng", "Không áp dụng", "Server: TLS Web Server Auth (serverAuth); Client: TLS Web Client Auth (clientAuth)"),
        (
            "Tên thay thế (SAN)",
            "Không áp dụng",
            "Không áp dụng",
            "Server: DNS:secure.lab.local / DNS:api.lab.local, DNS:localhost, IP:127.0.0.1; Client (Alice): không dùng SAN, định danh qua Subject DN & emailAddress",
        ),
        (
            "Trạng thái vận hành",
            "Ngoại tuyến (Offline — mô phỏng thư mục trong Docker; thực tế tách biệt mạng/HSM)",
            "Trực tuyến (Issuing CA)",
            "Triển khai trên Nginx (pki-web) / Máy khách (pki-client)",
        ),
    ]
    h["table"](
        "TABLE I. SO SÁNH ĐẶC TÍNH KỸ THUẬT CÁC CẤP CHỨNG THƯ TRONG HỆ THỐNG PKI",
        t1_headers,
        t1_rows,
        [1.55, 1.35, 1.55, 2.15],
        center_cols=[1, 2],
    )

    h["h2"]("C. Vai trò Registration Authority (RA), Cơ chế CSR và Vòng đời Chứng thư")
    h["p"](
        "Trong mô hình PKI chuẩn mực [1, Mục 4.6], [2, Mục 23.3], [3, Mục 3.3.1–3.3.5], quy trình phát hành chứng thư tách biệt "
        "hai vai trò chính nhằm kiểm soát thẩm quyền trước khi ký số:"
    )
    h["bullet"](
        "Registration Authority (RA): ",
        "Chịu trách nhiệm tiếp nhận yêu cầu và thực hiện xác minh danh tính (Identity Validation) trước khi chuyển tiếp sang CA "
        "ký duyệt [1, Mục 4.6], [2, Mục 23.3], [3, Mục 3.3.3]. Với chứng thư máy chủ, RA kiểm tra tính hợp lệ của định danh tên "
        "miền trong SAN; với chứng thư người dùng, RA đối chiếu hồ sơ cá nhân, địa chỉ email và mục đích sử dụng khóa [3, Mục 3.3.2–3.3.3]. "
        "Trong phạm vi lab thu nhỏ (ANM_DeTai14_PKI), hệ thống không tách máy chủ RA độc lập trực tuyến mà thực hiện chức năng RA "
        "về mặt logic thông qua kiểm tra cấu hình tệp mở rộng, chính sách trường DN (policy_strict trong root-ca.cnf, policy_loose "
        "trong intermediate-ca.cnf) trước lệnh openssl ca -batch.",
    )
    h["bullet"](
        "Certificate Signing Request (CSR): ",
        "Thực thể tự sinh cặp khóa riêng/công khai cục bộ, đóng gói khóa công khai cùng Subject DN vào tệp CSR và ký bằng chính "
        "khóa riêng của mình để chứng minh quyền sở hữu khóa tương ứng, bảo đảm khóa riêng không bao giờ phải truyền qua mạng tới "
        "CA [1, Mục 4.6], [3, Mục 3.3.1–3.3.2].",
    )
    h["bullet"](
        "Vòng đời chứng thư và khóa mật mã: ",
        "(1) Khởi tạo khóa và CSR; (2) Thẩm định và ký phát hành; (3) Vận hành, giám sát và xoay vòng/gia hạn khóa định kỳ "
        "[1, Mục 4.6], [3, Mục 3.3.1, 3.3.3]; và (4) Thu hồi trước hạn khi hết tin cậy hoặc lộ khóa qua CRL [3, Mục 3.3.4] "
        "(trong lab, kịch bản tự viết 04_renew_cert.sh minh họa gia hạn api.crt từ Serial 1001 lên Serial 1006).",
    )

    h["h2"]("D. So sánh Cơ chế Kiểm tra Thu hồi CRL và OCSP")
    h["p"](
        "Kiểm tra trạng thái thu hồi chứng thư trước mốc thời gian notAfter có thể triển khai thông qua CRL (Certificate Revocation "
        "List) [1, Mục 4.5], [2, Mục 23.2], [3, Mục 3.3.4] hoặc OCSP (Online Certificate Status Protocol) [3, Mục 3.3.4]. Bảng II "
        "đối chiếu năm khía cạnh kỹ thuật giữa hai cơ chế:"
    )

    t2_headers = [
        "Tiêu chí so sánh",
        "CRL (Certificate Revocation List) [1], [2], [3]",
        "OCSP (Online Certificate Status Protocol) [3]",
    ]
    t2_rows = [
        (
            "Cơ chế hoạt động",
            "CA định kỳ ký và xuất toàn bộ danh sách số sê-ri bị thu hồi; phía kiểm chứng tải về và lưu đệm cục bộ (local cache).",
            "Client gửi trực tiếp truy vấn mang số sê-ri tới máy chủ OCSP của CA để nhận phản hồi tức thời (Valid hoặc Revoked).",
        ),
        (
            "Độ trễ cập nhật",
            "Phụ thuộc chu kỳ xuất bản CRL (ví dụ 30 ngày trong lab); có độ trễ cập nhật giữa hai kỳ phát hành nếu bản cache chưa hết hạn.",
            "Thấp (theo thời gian thực), phản ánh ngay trạng thái thu hồi mới ngay khi cơ sở dữ liệu của CA được cập nhật.",
        ),
        (
            "Băng thông & Tải",
            "Kích thước tệp CRL tăng dần theo số lượng chứng thư thu hồi; tốn băng thông tải lại toàn bộ danh sách ở hệ thống lớn.",
            "Gói tin truy vấn/phản hồi rất nhỏ (chỉ cho một số sê-ri), tiết kiệm băng thông đường truyền hơn tải cả danh sách CRL.",
        ),
        (
            "Sẵn sàng & Phụ thuộc hạ tầng",
            "Ít phụ thuộc kết nối trực tuyến tới CA tại từng phiên nếu CRL đã lưu đệm cục bộ hoặc gắn sẵn tại máy chủ (như ssl_crl trên Nginx).",
            "Đòi hỏi máy chủ OCSP của CA phải luôn sẵn sàng trực tuyến; nếu máy chủ OCSP gián đoạn, việc kiểm tra có thể bị ảnh hưởng.",
        ),
        (
            "Quyền riêng tư",
            "Ít lộ hành vi truy cập cụ thể: client tải danh sách chung nên CA không biết người dùng đang kết nối dịch vụ nào tại từng thời điểm.",
            "Phát sinh rủi ro lộ thông tin truy cập: mỗi truy vấn trực tiếp mang số sê-ri gửi về máy chủ OCSP cho thấy thời điểm và dịch vụ client đang xác minh.",
        ),
    ]
    h["table"](
        "TABLE II. SO SÁNH CƠ CHẾ KIỂM TRA THU HỒI CRL VÀ OCSP",
        t2_headers,
        t2_rows,
        [1.3, 2.65, 2.65],
    )
    h["p"](
        "Về lựa chọn kiến trúc, CRL phù hợp với mạng nội bộ, môi trường cô lập và mô hình phòng thí nghiệm Docker của đồ án, nơi "
        "số lượng chứng thư thu hồi nhỏ và tệp ca-chain.crl.pem được nạp trực tiếp qua ssl_crl trên Nginx. Ngược lại, trong các "
        "hệ thống quy mô lớn có danh sách thu hồi biến động nhanh, OCSP giúp khắc phục nhược điểm kích thước tệp lớn và độ trễ cập "
        "nhật của CRL [2, Mục 23.2], [3, Mục 3.3.4]."
    )

    h["h2"]("E. Phân tích Rủi ro Lộ Khóa riêng theo 3 Cấp độ và Biện pháp Giảm thiểu")
    h["p"](
        "Phạm vi ảnh hưởng và quy trình ứng phó khi lộ khóa riêng phụ thuộc trực tiếp vào tầng của cặp khóa trong cây phân cấp tin "
        "cậy hai cấp [1, Mục 4.5–4.6], [3, Mục 3.3.3–3.3.4]:"
    )
    h["bullet"](
        "Cấp độ 1 — Lộ khóa riêng Root CA (root-ca.key): ",
        "Kẻ tấn công có thể tự ký phát hành Intermediate CA giả mạo hoặc chứng thư thực thể cuối bất kỳ khiến toàn bộ hệ thống tin "
        "cậy root-ca.crt bị đe dọa [3, Mục 3.3.3]. Vì Root CA tự ký nên không có CA cấp trên thu hồi qua CRL [1, Mục 4.5]; tổ chức "
        "buộc phải gỡ bỏ root-ca.crt khỏi mọi Trust Store trên hệ điều hành, trình duyệt và container, sau đó thiết lập lại Root "
        "CA và tái cấp toàn bộ hệ thống.",
    )
    h["bullet"](
        "Cấp độ 2 — Lộ khóa riêng Intermediate CA (inter-ca.key): ",
        "Toàn bộ chứng thư lá (secure.crt, api.crt, alice.crt) do Intermediate CA đó cấp phát đều mất độ tin cậy do kẻ tấn công có thể "
        "ký giả mạo chứng thư mới. Nếu root-ca.key vẫn an toàn, Root CA thu hồi inter-ca.crt vào root.crl.pem và khởi tạo Intermediate "
        "CA mới [1, Mục 4.5], [3, Mục 3.3.3]. Điều này lý giải vì sao trong lab thực nghiệm, Nginx khi bật ssl_verify_depth 2 cần "
        "tệp CRL gộp ca-chain.crl.pem (inter.crl.pem + root.crl.pem) nhằm bảo đảm kiểm tra thu hồi trên cả hai tầng của chuỗi chứng thư.",
    )
    h["bullet"](
        "Cấp độ 3 — Lộ khóa riêng End-Entity (Máy chủ hoặc Người dùng): ",
        "Rủi ro giới hạn trong danh tính thực thể bị lộ. Lộ khóa máy chủ (secure.key/api.key) kết hợp giả mạo định tuyến cho phép "
        "tấn công MitM; lộ khóa người dùng (alice.key) cho phép kẻ tấn công vượt qua xác thực mTLS tại api.lab.local/mtls. Quy trình "
        "ứng phó chuẩn 5 bước khi lộ khóa [3, Mục 3.3.4] gồm: (1) ngừng sử dụng khóa ngay không chờ hết hạn; (2) gửi yêu cầu thu hồi "
        "tức thì qua CRL/OCSP; (3) tiêu hủy vật lý mọi bản sao khóa lộ; (4) sinh cặp khóa mới kèm CSR mới để cấp lại chứng thư; "
        "(5) kiểm toán nhật ký thiệt hại. Trong lab thực nghiệm, quản trị viên thu hồi alice.crt (Serial 1002) với lý do keyCompromise, "
        "cập nhật ca-chain.crl.pem và chạy nginx -s reload để chặn ngay mọi kết nối (HTTP 400 kèm lỗi error 23).",
    )
    h["p"](
        "Các biện pháp giảm thiểu thực tiễn gồm: (1) Cô lập Root CA ngoại tuyến thực sự (tách biệt vật lý trong sản xuất, phân biệt "
        "với mô phỏng thư mục trong Docker) [1], [3, Mục 3.3.3]; (2) Lưu trữ khóa trong phần cứng bảo mật chuyên dụng (HSM / TPM) "
        "không cho phép xuất khóa bản rõ [3, Mục 3.3.1]; (3) Xoay vòng khóa định kỳ và giới hạn thời hạn hiệu lực chứng thư [3, Mục 3.3.1]; "
        "và (4) Siết quyền truy cập tệp khóa theo nguyên tắc đặc quyền tối thiểu [3, Mục 3.3.1] (600/400 — trong lab đã kiểm chứng "
        "chmod 600 trên toàn bộ 17/17 tệp .key trong container pki-client)."
    )

    h["h2"]("F. Liên hệ Hạ tầng PKI với Quy trình Bắt tay TLS 1.3")
    h["p"](
        "Giao thức TLS sử dụng mô hình mật mã lai kết hợp trao đổi khóa phiên tạm thời (đảm bảo tính bí mật chuyển tiếp — PFS) với "
        "cơ chế xác thực danh tính dựa trên chứng thư PKI [1, Mục 6.2–6.3], [2, Mục 22.3–22.4], [3, tr. 52–53, 89–91]. Quá trình "
        "này được đối chiếu trực tiếp qua kết quả kiểm thử openssl s_client -tls1_3 trên secure.lab.local và api.lab.local:"
    )
    h["bullet"](
        "1) ClientHello / ServerHello (Thỏa thuận khóa phiên tạm thời): ",
        "Client và Server thỏa thuận tham số mật mã và trao đổi khóa tạm thời để thiết lập khóa phiên truyền thông [1, Mục 6.2], "
        "[2, Mục 22.3], [3, tr. 89–91]. Trong kết quả kiểm thử thực nghiệm của nhóm, phiên TLS 1.3 chọn bộ mã AEAD "
        "TLS_AES_256_GCM_SHA384 cùng Server Temp Key: X25519 (253 bits).",
    )
    h["bullet"](
        "2) Thông điệp Certificate (Xác minh chuỗi, hiệu lực, SAN và CRL): ",
        "Server gửi chuỗi chứng thư (secure.crt + inter-ca.crt) trong thông điệp Certificate [1, Mục 6.2], [2, Mục 22.3]. Máy khách "
        "kiểm tra bốn điều kiện PKI: chuỗi tin cậy về ca-chain.crt, thời hạn hiệu lực, khớp tên miền SAN (DNS:secure.lab.local) "
        "cùng mục đích serverAuth, và trạng thái thu hồi CRL/OCSP [1, Mục 4.5], [2, Mục 23.2], [3, Mục 3.3.2, 3.3.5].",
    )
    h["bullet"](
        "3) Thông điệp CertificateVerify (Chứng minh sở hữu khóa riêng): ",
        "Vì chứng thư là dữ liệu công khai, máy chủ ký giá trị băm của lịch sử bắt tay bằng khóa riêng tương ứng để chứng minh "
        "quyền sở hữu khóa riêng khớp với khóa công khai trong Certificate [1, Mục 6.2], [2, Mục 22.3]. Trong log thực nghiệm "
        "TLS 1.3 (Mục III.C), OpenSSL ghi nhận Peer signing digest: SHA256 và Peer signature type: RSA-PSS.",
    )
    h["bullet"](
        "4) Finished và mở rộng mTLS (CertificateRequest trên api.lab.local): ",
        "Thông điệp Finished xác thực tính toàn vẹn phiên bắt tay; khi kích hoạt xác thực hai chiều (mTLS), server gửi "
        "CertificateRequest yêu cầu client gửi lại cặp Certificate và CertificateVerify ký bằng khóa riêng của client [1, Mục 6.2], "
        "[2, Mục 22.3], [3, tr. 52]. Trong thực nghiệm trên api.lab.local, Nginx liệt kê CA tin cậy (UTH Intermediate CA và UTH "
        "Root CA), đối chiếu alice.crt với ca-chain.crt và tra cứu ca-chain.crl.pem.",
    )

    h["h2"]("G. Kiến trúc Mạng Docker Cô lập (pki-net) trên Nền Windows")
    h["p"](
        "Toàn bộ hạ tầng phòng thí nghiệm được đóng gói và cô lập hoàn toàn trong Docker Compose (các container Linux Alpine) chạy "
        "trên nền hệ điều hành Windows, sử dụng mạng bridge nội bộ mang tên pki-net mà không can thiệp vào tệp hosts hay cấu hình "
        "mạng của máy vật lý:"
    )
    h["bullet"](
        "Container pki-web (nginx:1.27-alpine / nginx/1.27.5): ",
        "Phục vụ năm Virtual Hosts qua SNI trên cổng 443 (ánh xạ 8443:443 ra host Windows để kiểm tra giao diện trình duyệt): "
        "secure.lab.local, api.lab.local, expired.lab.local, untrusted.lab.local và revoked.lab.local.",
    )
    h["bullet"](
        "Container pki-client (Alpine Linux 3.20.10, OpenSSL 3.3.7, cURL 8.14.1): ",
        "Đóng vai trò nút quản trị CA mô phỏng, máy trạm người dùng (alice) và môi trường thực thi bộ kịch bản kiểm thử qua phân giải "
        "DNS nội bộ của Docker.",
    )

    # -------------------------------------------------------------
    # SECTION III. TRIỂN KHAI VÀ KẾT QUẢ THỰC NGHIỆM
    # -------------------------------------------------------------
    h["h1"]("III. TRIỂN KHAI VÀ KẾT QUẢ THỰC NGHIỆM (IMPLEMENTATION & RESULTS)")

    h["h2"]("A. Quy trình Lệnh OpenSSL Thực tế qua các Pha Vòng đời và Kiểm kê Chứng thư")
    h["p"](
        "Các pha khởi tạo, phát hành, gia hạn và thu hồi chứng thư được triển khai qua bộ script tại pki/scripts/ bên trong "
        "container pki-client (thư mục làm việc /workspace):"
    )

    h["h3"]("1) Khởi tạo Root CA (4096-bit) và Intermediate CA (2048-bit, pathlen:0)")
    h["code"](
        "# --- (a) Root CA Setup (01_setup_ca.sh) ---\n"
        "mkdir -p /workspace/pki/root/{certs,private,newcerts,crl} && chmod 700 /workspace/pki/root/private\n"
        "touch /workspace/pki/root/index.txt && echo 1000 > /workspace/pki/root/serial && echo 1000 > /workspace/pki/root/crlnumber\n"
        "openssl genrsa -out /workspace/pki/root/private/root-ca.key 4096\n"
        "chmod 600 /workspace/pki/root/private/root-ca.key\n"
        "openssl req -config /workspace/pki/config/root-ca.cnf -key /workspace/pki/root/private/root-ca.key \\\n"
        "    -new -x509 -days 3650 -sha256 -extensions v3_ca -out /workspace/pki/root/certs/root-ca.crt\n"
        "openssl ca -config /workspace/pki/config/root-ca.cnf -gencrl -out /workspace/pki/root/crl/root.crl.pem\n\n"
        "# --- (b) Intermediate CA Setup ---\n"
        "mkdir -p /workspace/pki/intermediate/{certs,private,newcerts,crl,csr} && chmod 700 /workspace/pki/intermediate/private\n"
        "touch /workspace/pki/intermediate/index.txt && echo 1000 > /workspace/pki/intermediate/serial && echo 1000 > /workspace/pki/intermediate/crlnumber\n"
        "openssl genrsa -out /workspace/pki/intermediate/private/inter-ca.key 2048\n"
        "chmod 600 /workspace/pki/intermediate/private/inter-ca.key\n"
        "openssl req -config /workspace/pki/config/intermediate-ca.cnf -new -sha256 \\\n"
        "    -key /workspace/pki/intermediate/private/inter-ca.key -out /workspace/pki/intermediate/csr/inter-ca.csr\n"
        "openssl ca -config /workspace/pki/config/root-ca.cnf -extensions v3_intermediate_ca -days 1825 -notext -md sha256 -batch \\\n"
        "    -in /workspace/pki/intermediate/csr/inter-ca.csr -out /workspace/pki/intermediate/certs/inter-ca.crt\n"
        "cat /workspace/pki/intermediate/certs/inter-ca.crt /workspace/pki/root/certs/root-ca.crt > /workspace/artifacts/certs/ca-chain.crt",
        label="Lệnh OpenSSL khởi tạo hệ thống CA phân tầng hai cấp:",
    )

    h["h3"]("2) Cấp phát chứng thư cho 2 dịch vụ (secure, api), 1 người dùng (alice) và các mẫu kiểm thử")
    h["p"](
        "Theo yêu cầu đề tài, Intermediate CA phát hành chứng thư cho hai dịch vụ mạng (secure.lab.local Serial 1000 và api.lab.local "
        "Serial khởi đầu 1001) cùng một người dùng cuối (alice.crt Serial 1002). Toàn bộ tệp mở rộng máy chủ khai báo tường minh "
        "tên miền và địa chỉ IP trong SAN (không sử dụng wildcard), trong khi chứng thư Alice sử dụng EKU clientAuth và định danh "
        "trực tiếp trong Subject DN (CN=Alice/emailAddress=alice@lab.local). Đồng thời, script 02_issue_certs.sh tạo thêm expired.crt "
        "(Serial 1003, hiệu lực 2020), untrusted.crt (Rogue CA tự ký), revoked.crt (Serial 1004) và bob.crt (Serial 1005)."
    )
    h["code"](
        "# --- Cấp chứng thư Server (ví dụ secure.lab.local, Serial 1000) ---\n"
        "openssl genrsa -out /workspace/pki/intermediate/private/secure.key 2048\n"
        "chmod 600 /workspace/pki/intermediate/private/secure.key\n"
        "# Tệp /tmp/secure_ext.cnf chứa: basicConstraints=CA:FALSE, keyUsage=critical,digitalSignature,keyEncipherment,\n"
        "# extendedKeyUsage=serverAuth, subjectAltName=DNS:secure.lab.local, DNS:localhost, IP:127.0.0.1\n"
        "openssl req -new -sha256 -key /workspace/pki/intermediate/private/secure.key \\\n"
        "    -subj \"/C=VN/ST=Ho Chi Minh/L=Ho Chi Minh City/O=UTH PKI Lab/OU=Server/CN=secure.lab.local\" \\\n"
        "    -out /workspace/pki/intermediate/csr/secure.csr\n"
        "openssl ca -config /workspace/pki/config/intermediate-ca.cnf -extfile /tmp/secure_ext.cnf \\\n"
        "    -days 365 -notext -md sha256 -batch -in /workspace/pki/intermediate/csr/secure.csr -out /workspace/pki/intermediate/certs/secure.crt\n\n"
        "# --- Cấp chứng thư User Alice (Serial 1002, EKU clientAuth, không dùng SAN) ---\n"
        "openssl genrsa -out /workspace/pki/intermediate/private/alice.key 2048\n"
        "chmod 600 /workspace/pki/intermediate/private/alice.key\n"
        "# Tệp /tmp/alice_ext.cnf chứa: basicConstraints=CA:FALSE, nsCertType=client,email,\n"
        "# keyUsage=critical,digitalSignature,keyEncipherment, extendedKeyUsage=clientAuth\n"
        "openssl req -new -sha256 -key /workspace/pki/intermediate/private/alice.key \\\n"
        "    -subj \"/C=VN/ST=Ho Chi Minh/L=Ho Chi Minh City/O=UTH PKI Lab/OU=Engineering/CN=Alice/emailAddress=alice@lab.local\" \\\n"
        "    -out /workspace/pki/intermediate/csr/alice.csr\n"
        "openssl ca -config /workspace/pki/config/intermediate-ca.cnf -extfile /tmp/alice_ext.cnf \\\n"
        "    -days 365 -notext -md sha256 -batch -in /workspace/pki/intermediate/csr/alice.csr -out /workspace/pki/intermediate/certs/alice.crt",
        label="Lệnh tạo khóa, CSR và ký cấp phát End-Entity (02_issue_certs.sh):",
    )

    h["h3"]("3) Gia hạn chứng thư (04_renew_cert.sh) và Thu hồi qua CRL (03_revoke_crl.sh)")
    h["p"](
        "Trong pha gia hạn cho dịch vụ api.lab.local (04_renew_cert.sh), hệ thống sinh cặp khóa mới api_renew.key thay vì tái sử "
        "dụng khóa cũ, phát hành chứng thư mới Serial 1006 thời hạn 730 ngày (Nov 14 06:20:19 2026 GMT đến Nov 13 06:20:19 2028 GMT) "
        "và thu hồi chứng thư cũ Serial 1001 với mã lý do superseded. Tiếp theo, ở pha thu hồi (03_revoke_crl.sh và quy trình kiểm "
        "chứng thu hồi khóa Alice), các chứng thư revoked.crt (1004), bob.crt (1005) và alice.crt (1002) được thu hồi với lý do "
        "keyCompromise; tệp inter.crl.pem được tái xuất bản (CRL Number 4100), ghép với root.crl.pem (CRL Number 4096) thành "
        "ca-chain.crl.pem và nạp lại cấu hình Nginx:"
    )
    h["code"](
        "# --- (d) Gia hạn api.lab.local (1001 superseded -> 1006 valid 730 ngày) ---\n"
        "openssl genrsa -out /workspace/pki/intermediate/private/api_renew.key 2048 && chmod 600 /workspace/pki/intermediate/private/api_renew.key\n"
        "openssl req -new -sha256 -key /workspace/pki/intermediate/private/api_renew.key \\\n"
        "    -subj \"/C=VN/ST=Ho Chi Minh/L=Ho Chi Minh City/O=UTH PKI Lab/OU=Server/CN=api.lab.local\" -out /workspace/pki/intermediate/csr/api_renew.csr\n"
        "openssl ca -config /workspace/pki/config/intermediate-ca.cnf -extfile /tmp/api_renew_ext.cnf -days 730 -notext -md sha256 -batch \\\n"
        "    -in /workspace/pki/intermediate/csr/api_renew.csr -out /workspace/pki/intermediate/certs/api_renew.crt\n"
        "openssl ca -config /workspace/pki/config/intermediate-ca.cnf -revoke /workspace/pki/intermediate/certs/api_old.crt -crl_reason superseded -batch\n\n"
        "# --- (e) Thu hồi alice.crt (1002) / revoked.crt (1004) & Tái tạo CRL Chain ---\n"
        "openssl ca -config /workspace/pki/config/intermediate-ca.cnf -revoke /workspace/pki/intermediate/certs/alice.crt -crl_reason keyCompromise -batch\n"
        "openssl ca -config /workspace/pki/config/intermediate-ca.cnf -gencrl -out /workspace/pki/intermediate/crl/inter.crl.pem -batch\n"
        "cp /workspace/pki/intermediate/crl/inter.crl.pem /workspace/artifacts/certs/inter.crl.pem\n"
        "cat /workspace/artifacts/certs/inter.crl.pem /workspace/artifacts/certs/root.crl.pem > /workspace/artifacts/certs/ca-chain.crl.pem\n"
        "docker compose exec -T web nginx -t && docker compose exec -T web nginx -s reload",
        label="Lệnh gia hạn chứng thư api.crt và thu hồi alice.crt qua CRL:",
    )

    h["h3"]("4) Bằng chứng Kiểm kê Chứng thư (2 dịch vụ + 1 người dùng) và Phân quyền Khóa riêng")
    h["p"](
        "Kết quả trích xuất trực tiếp từ tệp kiểm chứng thực nghiệm (evidence_logs.txt, Phần 2 và Phần 5) xác nhận sự tồn tại "
        "và các thuộc tính X.509v3 thực tế của 2 chứng thư dịch vụ (secure.crt, api.crt), 1 chứng thư người dùng (alice.crt) "
        "cùng cơ sở dữ liệu index.txt và quyền truy cập tệp khóa 600/400 (cụ thể chmod 600 xác minh trên 17/17 tệp .key trong container):"
    )
    h["code"](
        "# Trích xuất pki/intermediate/index.txt sau khi gia hạn api.crt (1006) và thu hồi alice.crt (1002):\n"
        "V\t271105015938Z\t\t1000\tunknown\t/C=VN/ST=Ho Chi Minh/L=Ho Chi Minh City/O=UTH PKI Lab/OU=Server/CN=secure.lab.local\n"
        "R\t271105015938Z\t261114062019Z,superseded\t1001\tunknown\t.../CN=api.lab.local\n"
        "R\t271105015938Z\t261114063506Z,keyCompromise\t1002\tunknown\t.../CN=Alice/emailAddress=alice@lab.local\n"
        "V\t200102000000Z\t\t1003\tunknown\t.../CN=expired.lab.local\n"
        "R\t271105015939Z\t261105015939Z,keyCompromise\t1004\tunknown\t.../CN=revoked.lab.local\n"
        "R\t271114061502Z\t261114061536Z,keyCompromise\t1005\tunknown\t.../CN=Bob/emailAddress=bob@lab.local\n"
        "V\t281113062019Z\t\t1006\tunknown\t.../CN=api.lab.local\n\n"
        "# Kết quả kiểm tra chuỗi + CRL 2 tầng cho 2 dịch vụ hợp lệ:\n"
        "$ openssl verify -crl_check_all -CAfile /workspace/artifacts/certs/ca-chain.crt \\\n"
        "    -CRLfile /workspace/artifacts/certs/ca-chain.crl.pem /workspace/artifacts/certs/secure.crt /workspace/artifacts/certs/api.crt\n"
        "/workspace/artifacts/certs/secure.crt: OK\n"
        "/workspace/artifacts/certs/api.crt: OK\n\n"
        "# Kiểm tra quyền khóa riêng (17/17 tệp .key đều trả về mode 600):\n"
        "$ stat -c '%a %n' /workspace/pki/root/private/*.key /workspace/pki/intermediate/private/*.key /workspace/artifacts/certs/*.key\n"
        "600 /workspace/pki/root/private/root-ca.key  (+ 9 tệp ở intermediate/private/*.key và 7 tệp ở artifacts/certs/*.key -> 600)",
        label="Trích xuất nhật ký kiểm kê chứng thư và phân quyền khóa riêng từ evidence_logs.txt:",
    )

    t3_headers = ["Tệp chứng thư", "Vai trò / Đối tượng", "Serial", "Trạng thái & Hiệu lực", "SAN / Định danh X.509v3 thực tế"]
    t3_rows = [
        (
            "secure.crt",
            "Dịch vụ 1 (Web HTTPS)",
            "1000",
            "V — 365 ngày (05/11/2026–05/11/2027)",
            "EKU: serverAuth; SAN: DNS:secure.lab.local, DNS:localhost, IP Address:127.0.0.1",
        ),
        (
            "api.crt",
            "Dịch vụ 2 (API mTLS)",
            "1006 (gia hạn từ 1001)",
            "V — 730 ngày (14/11/2026–13/11/2028)",
            "EKU: serverAuth; SAN: DNS:api.lab.local, DNS:localhost, IP Address:127.0.0.1",
        ),
        (
            "alice.crt",
            "Người dùng 1 (mTLS Client)",
            "1002",
            "V khi chạy TC03; R (keyCompromise) khi kiểm chứng Nginx CRL",
            "EKU: clientAuth; không gắn SAN; định danh qua Subject DN (CN=Alice, emailAddress=alice@lab.local)",
        ),
        (
            "expired.crt",
            "Dịch vụ kiểm thử TC04",
            "1003",
            "V (quá hạn 02/01/2020 GMT)",
            "SAN: DNS:expired.lab.local, DNS:localhost, IP:127.0.0.1",
        ),
        (
            "revoked.crt",
            "Dịch vụ kiểm thử TC06",
            "1004",
            "R (keyCompromise)",
            "SAN: DNS:revoked.lab.local, DNS:localhost, IP:127.0.0.1",
        ),
    ]
    h["table"](
        "TABLE III. KIỂM KÊ CHỨNG THƯ PHÁT HÀNH (2 DỊCH VỤ, 1 NGƯỜI DÙNG) VÀ CHỨNG THƯ KIỂM THỬ",
        t3_headers,
        t3_rows,
        [1.05, 1.3, 1.0, 1.45, 1.8],
        center_cols=[2],
    )

    h["p"](
        "Hình minh chứng thực tế dưới đây xác nhận phần mở rộng X.509v3 SAN của secure.crt (Fig. 1), cơ sở dữ liệu index.txt "
        "với đầy đủ 2 dịch vụ (secure.lab.local, api.lab.local) cùng 1 người dùng (Alice) và quyền 600 trên toàn bộ 17 tệp khóa "
        "riêng .key trong container pki-client (Fig. 2):",
        space_after=4,
    )
    h["fig"](1, "image7.png", FIGURES[0][2], FIGURES[0][3])
    h["fig"](2, "image11.png", FIGURES[1][2], FIGURES[1][3])

    h["h2"]("B. Cấu hình Máy chủ Dịch vụ Mạng Nginx (Virtual Hosts & CRL)")
    h["p"](
        "Các Virtual Hosts thực tế được nạp trong container pki-web tại /etc/nginx/conf.d/. Sau khi hiệu chỉnh và rà soát, "
        "lệnh docker compose exec -T web nginx -t xác nhận syntax is ok và test is successful; tệp ca-chain.crl.pem nạp vào "
        "Nginx chứa 2 khối CRL (Intermediate CRL Number 4100 và Root CRL Number 4096) với mã băm SHA-256 daf93b27... giống hệt "
        "nhau trên cả pki-web và pki-client."
    )

    h["code"](
        "server {\n"
        "    listen 80;\n"
        "    server_name secure.lab.local localhost 127.0.0.1;\n"
        "    return 301 https://$host$request_uri;\n"
        "}\n\n"
        "server {\n"
        "    listen 443 ssl default_server;\n"
        "    server_name secure.lab.local localhost 127.0.0.1;\n"
        "    ssl_certificate /etc/nginx/certs/secure.crt;\n"
        "    ssl_certificate_key /etc/nginx/certs/secure.key;\n"
        "    ssl_protocols TLSv1.2 TLSv1.3;\n"
        "    ssl_prefer_server_ciphers on;\n"
        "    ssl_ciphers HIGH:!aNULL:!MD5;\n"
        "    location / {\n"
        "        default_type text/html;\n"
        "        return 200 \"<html><body><h1>200 OK - Secure Web Service</h1><p>HTTPS connection established successfully with valid PKI Certificate.</p></body></html>\\n\";\n"
        "    }\n"
        "}",
        label="1) Cấu hình Dịch vụ Web HTTPS Chuẩn (services/nginx/conf.d/secure.conf):",
    )

    h["code"](
        "server {\n"
        "    listen 80;\n"
        "    server_name api.lab.local;\n"
        "    return 301 https://$host$request_uri;\n"
        "}\n\n"
        "server {\n"
        "    listen 443 ssl;\n"
        "    server_name api.lab.local;\n"
        "    error_log /var/log/nginx/error.log info;\n\n"
        "    ssl_certificate /etc/nginx/certs/api.crt;\n"
        "    ssl_certificate_key /etc/nginx/certs/api.key;\n"
        "    ssl_protocols TLSv1.2 TLSv1.3;\n"
        "    ssl_prefer_server_ciphers on;\n\n"
        "    # Mutual TLS (mTLS) Authentication + Server-side Client CRL Enforcement\n"
        "    ssl_client_certificate /etc/nginx/certs/ca-chain.crt;\n"
        "    ssl_verify_client on;\n"
        "    ssl_verify_depth 2;\n"
        "    ssl_crl /etc/nginx/certs/ca-chain.crl.pem;\n\n"
        "    location /mtls {\n"
        "        default_type application/json;\n"
        "        return 200 '{\"status\": 200, \"message\": \"200 OK - mTLS Authenticated\", \"auth\": \"mTLS Authenticated\", \"client_dn\": \"$ssl_client_s_dn\", \"serial\": \"$ssl_client_serial\"}\\n';\n"
        "    }\n\n"
        "    location / {\n"
        "        default_type application/json;\n"
        "        return 200 '{\"status\": 200, \"service\": \"api.lab.local\", \"mtls_required\": true}\\n';\n"
        "    }\n"
        "}",
        label="2) Cấu hình Dịch vụ API Xác thực mTLS và Kiểm tra CRL phía Server (services/nginx/conf.d/api.conf):",
    )

    h["code"](
        "server {\n"
        "    listen 443 ssl;\n"
        "    server_name revoked.lab.local;\n\n"
        "    ssl_certificate /etc/nginx/certs/revoked.crt;\n"
        "    ssl_certificate_key /etc/nginx/certs/revoked.key;\n"
        "    ssl_protocols TLSv1.2 TLSv1.3;\n\n"
        "    # Server cert (revoked.crt) is listed in inter.crl.pem;\n"
        "    # revocation check of server certificates is performed by clients (TC06).\n"
        "    location / {\n"
        "        default_type text/plain;\n"
        "        return 200 \"Revoked Certificate Service\\n\";\n"
        "    }\n"
        "}",
        label="3) Cấu hình Máy chủ Kiểm thử Thu hồi Chứng thư Server (services/nginx/conf.d/revoked.conf):",
    )

    h["callout"](
        "Phân biệt rạch ròi cơ chế kiểm tra CRL ở phía Client (TC06) và phía Server Nginx (mTLS)",
        "Chỉ thị ssl_crl trên Nginx chỉ áp dụng cho việc kiểm tra thu hồi chứng thư khách (Client Certificate) khi bật "
        "ssl_verify_client on;, do đó revoked.conf không khai báo dư thừa ssl_crl mà để phía client kiểm tra thu hồi chứng thư "
        "máy chủ revoked.crt (Serial 1004) bằng cờ -crl_check / --crlfile trong TC06. Ngược lại, tại cổng api.lab.local/mtls, "
        "api.conf nạp ssl_crl /etc/nginx/certs/ca-chain.crl.pem; để Nginx trực tiếp kiểm tra thu hồi đối với Client Certificate: "
        "khi alice.crt (Serial 1002) bị thu hồi, Nginx trả về HTTP/1.1 400 Bad Request (400 The SSL certificate error) và ghi log "
        "client SSL certificate verify error: (23:certificate revoked).",
    )

    h["h2"]("C. Phân tích Sáu Kịch bản Kiểm thử (TC01–TC06) và Thực nghiệm Từ chối mTLS qua CRL")
    h["p"](
        "Toàn bộ sáu kịch bản kiểm thử và các phép thử xác minh bổ sung được thực thi từ container pki-client, lưu nhật ký "
        "tại artifacts/logs/ và evidence_logs.txt:"
    )

    h["p"](
        "1) Kịch bản TC01 — Xác minh Chuỗi tin cậy (Chain of Trust): Lệnh openssl verify -CAfile /workspace/artifacts/certs/ca-chain.crt "
        "/workspace/artifacts/certs/secure.crt trả về secure.crt: OK (Fig. 3), xác nhận chuỗi ủy quyền từ UTH Root CA qua UTH Intermediate CA.",
        space_after=4,
    )
    h["fig"](3, "image5.png", FIGURES[2][2], FIGURES[2][3])

    h["p"](
        "2) Kịch bản TC02 — Dịch vụ HTTPS Hợp lệ (secure.lab.local) và Bắt tay TLS 1.3: Kết quả thực thi curl --tlsv1.3 (Fig. 4) "
        "và openssl s_client -tls1_3 (Fig. 5) trong container pki-client chứng minh phiên TLS 1.3 được thiết lập với cipher "
        "TLS_AES_256_GCM_SHA384, trao đổi khóa X25519, chữ ký RSA-PSS trên SHA-256 và Verify return code: 0 (ok):",
        space_after=4,
    )
    h["code"](
        "$ docker compose exec -T client sh -c \"openssl s_client -connect secure.lab.local:443 -CAfile /workspace/artifacts/certs/ca-chain.crt -servername secure.lab.local -tls1_3 </dev/null\"\n"
        "depth=2 C=VN, ST=Ho Chi Minh, L=Ho Chi Minh City, O=UTH PKI Lab, OU=Security Department, CN=UTH Root CA\n"
        "verify return:1\n"
        "depth=1 C=VN, ST=Ho Chi Minh, O=UTH PKI Lab, OU=Issuing CA Department, CN=UTH Intermediate CA\n"
        "verify return:1\n"
        "depth=0 C=VN, ST=Ho Chi Minh, L=Ho Chi Minh City, O=UTH PKI Lab, OU=Server, CN=secure.lab.local\n"
        "verify return:1\n"
        "---\n"
        "Peer signing digest: SHA256\n"
        "Peer signature type: RSA-PSS\n"
        "Server Temp Key: X25519, 253 bits\n"
        "Verification: OK\n"
        "New, TLSv1.3, Cipher is TLS_AES_256_GCM_SHA384\n"
        "Verify return code: 0 (ok)",
        label="Trích xuất bằng chứng bắt tay TLS 1.3 (evidence_logs.txt — Mục 3, Command 3.1):",
    )
    h["fig"](4, "image6.png", FIGURES[3][2], FIGURES[3][3])
    h["fig"](5, "image12.png", FIGURES[4][2], FIGURES[4][3])

    h["p"](
        "Lưu ý quan sát khi truy cập từ trình duyệt trên máy chủ Windows tại https://localhost:8443 (Fig. 6): dù Nginx phục vụ "
        "đúng nội dung 200 OK - Secure Web Service và chứng thư secure.crt có khai báo DNS:localhost trong SAN, thanh địa chỉ "
        "trình duyệt vẫn hiển thị cảnh báo 'Không bảo mật' (chữ https gạch chéo đỏ) do Trust Store của hệ điều hành Windows chưa "
        "import chứng thư gốc root-ca.crt và trình duyệt truy cập qua địa chỉ cổng ánh xạ localhost:8443 thay vì tên miền nội bộ "
        "secure.lab.local (thông tin chứng thư trình bày ở Fig. 7). Ngược lại, mọi kiểm thử trong container pki-client truyền tường "
        "minh --cacert /workspace/artifacts/certs/ca-chain.crt đều xác minh chuỗi tin cậy thành công với Verify return code: 0 (ok).",
        space_after=4,
    )
    h["fig"](6, "image9.png", FIGURES[5][2], FIGURES[5][3])
    h["fig"](7, "image8.png", FIGURES[6][2], FIGURES[6][3])

    h["p"](
        "3) Kịch bản TC03 — Xác thực Hai chiều mTLS (api.lab.local/mtls) và Kiểm chứng Nginx Từ chối Chứng thư Đã Thu hồi: "
        "Khi người dùng Alice chưa bị thu hồi chứng thư (trạng thái V trong index.txt), Fig. 8 minh họa hai trạng thái đối lập: "
        "truy cập không kèm Client Certificate bị Nginx từ chối với HTTP/1.1 400 Bad Request (400 No required SSL certificate was sent); "
        "truy cập cung cấp alice.crt (Serial 1002) và alice.key được xác thực thành công với HTTP/1.1 200 OK.",
        space_after=4,
    )
    h["fig"](8, "image10.png", FIGURES[7][2], FIGURES[7][3])

    h["p"](
        "Sau đó, để kiểm chứng cơ chế CRL phía máy chủ Nginx trên api.lab.local/mtls, hệ thống thu hồi alice.crt (Serial 1002) "
        "với lý do keyCompromise, tái tạo inter.crl.pem (CRL Number 4100), ghép ca-chain.crl.pem và nạp lại Nginx. Kết quả "
        "ghi nhận trong evidence_logs.txt (Mục 4) và minh họa tại Fig. 9 chứng minh Nginx từ chối kết nối mTLS của Alice với "
        "HTTP/1.1 400 Bad Request (400 The SSL certificate error) kèm nhật ký lỗi error 23 trên máy chủ web:",
        space_after=4,
    )
    h["code"](
        "$ docker compose exec -T client curl -i -sS --cacert /workspace/artifacts/certs/ca-chain.crt \\\n"
        "    --cert /workspace/artifacts/certs/alice.crt --key /workspace/artifacts/certs/alice.key https://api.lab.local/mtls\n"
        "HTTP/1.1 400 Bad Request\n"
        "Server: nginx/1.27.5\n"
        "...\n"
        "<head><title>400 The SSL certificate error</title></head>\n\n"
        "$ docker compose logs --tail 40 web\n"
        "pki-web | 172.20.0.2 - - [14/Nov/2026:06:36:38 +0000] \"GET /mtls HTTP/1.1\" 400 215 \"-\" \"curl/8.14.1\" \"-\"\n"
        "pki-web | 2026/11/14 06:36:38 [info] 188#188: *42 client SSL certificate verify error: (23:certificate revoked) while reading client request headers, client: 172.20.0.2, server: api.lab.local, request: \"GET /mtls HTTP/1.1\", host: \"api.lab.local\"\n\n"
        "$ docker compose exec -T client openssl verify -crl_check -CAfile /workspace/artifacts/certs/ca-chain.crt -CRLfile /workspace/artifacts/certs/ca-chain.crl.pem /workspace/artifacts/certs/alice.crt\n"
        "error 23 at 0 depth lookup: certificate revoked",
        label="Trích xuất bằng chứng Nginx mTLS chặn alice.crt đã thu hồi (evidence_logs.txt — Mục 4):",
    )
    h["fig"](9, "image13.png", FIGURES[8][2], FIGURES[8][3])

    h["p"](
        "4) Kịch bản TC04 — Phát hiện Chứng thư Hết hạn (expired.lab.local): Chứng thư expired.crt (Serial 1003, notAfter=Jan 2 00:00:00 "
        "2020 GMT) bị openssl s_client phát hiện với lỗi verify error:num=10:certificate has expired và cURL từ chối kết nối (exit code 60) (Fig. 10).",
        space_after=4,
    )
    h["fig"](10, "image1.png", FIGURES[9][2], FIGURES[9][3])

    h["p"](
        "5) Kịch bản TC05 — Phát hiện Chứng thư Không tin cậy (untrusted.lab.local): Chứng thư untrusted.crt được ký bởi một Rogue Root CA "
        "tự ký độc lập không nằm trong ca-chain.crt bị phát hiện lỗi verify error:num=20:unable to get local issuer certificate và bị cURL chặn (Fig. 11).",
        space_after=4,
    )
    h["fig"](11, "image2.png", FIGURES[10][2], FIGURES[10][3])

    h["p"](
        "6) Kịch bản TC06 — Thu hồi Chứng thư Máy chủ qua CRL (revoked.lab.local): Khi kiểm tra chứng thư máy chủ revoked.crt (Serial 1004, "
        "thu hồi lý do keyCompromise) ở phía client bằng openssl verify -crl_check, openssl s_client -CRLfile và curl --crlfile, cả ba "
        "công cụ đều báo lỗi verify error:num=23:certificate revoked và từ chối thiết lập phiên tin cậy (Fig. 12).",
        space_after=4,
    )
    h["fig"](12, "image4.png", FIGURES[11][2], FIGURES[11][3])

    h["h2"]("D. Tổng hợp Kết quả Kiểm thử và Đánh giá Tự động")
    h["p"](
        "Bảng IV tổng hợp kết quả đối chiếu giữa trạng thái kỳ vọng và kết quả ghi nhận thực tế từ toàn bộ sáu kịch bản TC01–TC06 "
        "cùng phép thử bổ sung kiểm tra thu hồi chứng thư khách hàng mTLS trên Nginx:"
    )

    t4_headers = ["Mã kiểm thử", "Kịch bản", "Công cụ sử dụng", "Kết quả kỳ vọng", "Kết quả ghi nhận từ Log", "Trạng thái"]
    t4_rows = [
        ("TC01", "Chuỗi tin cậy CA 2 tầng", "openssl verify", "secure.crt: OK", "secure.crt: OK", "PASS (1.5đ)"),
        ("TC02", "Dịch vụ HTTPS hợp lệ (TLS 1.3)", "curl, s_client -tls1_3", "HTTP 200 & code: 0 (ok)", "HTTP/1.1 200 OK; TLSv1.3, code: 0 (ok)", "PASS (1.5đ)"),
        ("TC03", "Xác thực hai chiều mTLS (Alice)", "curl (No cert vs Valid cert)", "Chặn 400; Cho phép 200", "400 Bad Request / 200 OK (Serial 1002)", "PASS (1.5đ)"),
        ("TC04", "Chứng thư hết hạn", "s_client, curl", "verify error:num=10", "num=10:certificate has expired; curl (60)", "PASS (1.0đ)"),
        ("TC05", "Chứng thư Rogue CA giả mạo", "s_client, curl", "verify error:num=18/20", "num=20:unable to get local issuer; curl (60)", "PASS (1.0đ)"),
        ("TC06", "Thu hồi cert máy chủ qua CRL", "verify, s_client, curl --crlfile", "verify error:num=23", "num=23:certificate revoked; curl (60)", "PASS (1.5đ)"),
        ("Bổ sung", "Nginx từ chối Alice đã thu hồi", "curl, s_client, docker logs web", "HTTP 400 & log error 23", "400 Bad Request + (23:certificate revoked)", "PASS (Xác minh)"),
    ]
    h["table"](
        "TABLE IV. MA TRẬN ĐỐI CHIẾU KẾT QUẢ KIỂM THỬ THỰC NGHIỆM (TC01–TC06 VÀ mTLS CRL)",
        t4_headers,
        t4_rows,
        [0.75, 1.45, 1.15, 1.1, 1.35, 0.8],
        center_cols=[0, 5],
        pass_col=5,
    )

    h["p"](
        "Bộ kiểm thử tự động do nhóm xây dựng (eval_rubric.sh) xác nhận các tiêu chí kỹ thuật gồm: chuẩn xuống dòng LF trên "
        "toàn bộ script bash (1.0đ), quyền bảo mật tệp khóa riêng 600/400 (1.0đ — cụ thể chmod 600 xác minh trên 17/17 tệp .key "
        "trong container) và sáu kịch bản TC01–TC06 (8.0đ) đều đạt trạng thái PASS với tổng điểm 10.0 / 10.0 (Fig. 13)."
    )
    h["fig"](13, "image3.png", FIGURES[12][2], FIGURES[12][3])

    # -------------------------------------------------------------
    # SECTION IV. KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN
    # -------------------------------------------------------------
    h["h1"]("IV. KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN (CONCLUSION & FUTURE WORK)")

    h["h2"]("A. Kết luận")
    h["p"](
        "Đề tài 14 đã xây dựng và kiểm chứng đầy đủ các yêu cầu đề cương môn học An ninh Mạng thông qua mô hình PKI thu nhỏ trên "
        "môi trường Docker Compose (các container Linux Alpine) chạy trên nền hệ điều hành Windows:"
    )
    h["p"](
        "1) Thiết lập hạ tầng PKI phân tầng hai cấp gồm Root CA (RSA 4096-bit tự ký, mô phỏng cô lập tại thư mục pki/root/) và "
        "Intermediate CA (RSA 2048-bit ký phát hành với pathlen:0), sử dụng hàm băm SHA-256 trên nền OpenSSL 3.3.7.\n"
        "2) Phát hành chứng thư số X.509v3 khai báo SAN tường minh cho 2 dịch vụ (secure.lab.local Serial 1000 và api.lab.local "
        "Serial 1006 sau gia hạn) cùng 1 người dùng (alice.crt Serial 1002), đáp ứng tiêu chuẩn định danh của các trình duyệt "
        "và máy khách TLS hiện đại.\n"
        "3) Triển khai xác thực hai chiều mTLS trên Nginx (api.conf) kết hợp kiểm tra CRL hai tầng (ca-chain.crl.pem qua ssl_crl), "
        "cho phép truy cập khi chứng thư hợp lệ và từ chối tức thì (HTTP 400 kèm lỗi error 23) khi thiếu chứng thư hoặc chứng thư bị thu hồi.\n"
        "4) Trình diễn đầy đủ bốn trạng thái vòng đời chứng thư (Hợp lệ, Hết hạn, Không tin cậy, Thu hồi) qua sáu kịch bản TC01–TC06 "
        "và đạt 10.0 / 10.0 điểm trên bộ kiểm thử tự động do nhóm xây dựng (eval_rubric.sh).",
        space_after=6,
    )

    h["h2"]("B. Bài học Kinh nghiệm")
    h["p"](
        "Quá trình thực nghiệm rút ra bốn lưu ý kỹ thuật quan trọng: (1) Chứng thư máy chủ bắt buộc phải khai báo đầy đủ SAN "
        "thay vì phụ thuộc trường Common Name theo yêu cầu đối chiếu của trình duyệt và ứng dụng HTTPS hiện đại [1, Mục 4.5], "
        "[3, tr. 53, 99]; (2) Với mô hình CA hai tầng, Nginx khi bật ssl_verify_depth 2 cần tệp CRL gộp cả Intermediate CRL và "
        "Root CRL (ca-chain.crl.pem) để kiểm tra thu hồi đầy đủ trên mọi tầng của chuỗi chứng thư; (3) Kiểm soát quyền truy cập "
        "tệp khóa riêng (chmod 600 trên toàn bộ 17 tệp .key) và chuẩn xuống dòng LF là điều kiện tiên quyết khi phát triển trên "
        "Windows và chạy trong container Linux; (4) Cần phân biệt rõ giới hạn mô phỏng thư mục của Root CA trong Docker với yêu "
        "cầu lưu trữ ngoại tuyến tách biệt mạng hoặc HSM ở hạ tầng thực tế [1], [3, Mục 3.3.3]."
    )

    h["h2"]("C. Hướng phát triển")
    h["p"](
        "Để mở rộng mô hình hướng tới quy mô vận hành thực tế, đề tài đề xuất hai hướng phát triển tiếp theo:"
    )
    h["bullet"](
        "Triển khai dịch vụ kiểm tra thu hồi trực tuyến OCSP: ",
        "Bổ sung máy chủ OCSP nhằm giảm độ trễ cập nhật trạng thái thu hồi theo thời gian thực và tiết kiệm băng thông so với "
        "việc tải toàn bộ tệp CRL khi quy mô chứng thư tăng cao [2, Mục 23.2], [3, Mục 3.3.4].",
    )
    h["bullet"](
        "Tự động hóa xoay vòng khóa và gia hạn chứng thư: ",
        "Xây dựng cơ chế tự động hóa quy trình gia hạn và xoay vòng khóa định kỳ (Key Rotation) cho chứng thư có thời hạn ngắn, "
        "giảm thiểu rủi ro sai sót thao tác thủ công và thu hẹp cửa sổ thời gian phơi nhiễm nếu xảy ra lộ khóa [3, Mục 3.3.1].",
    )

    # -------------------------------------------------------------
    # REFERENCES
    # -------------------------------------------------------------
    h["h1"]("TÀI LIỆU THAM KHẢO (REFERENCES)")
    refs = [
        "[1] W. Stallings, Network Security Essentials: Applications and Standards, 6th ed. Harlow, England: Pearson Education, 2017.",
        "[2] W. Stallings and L. Brown, Computer Security: Principles and Practice, 2nd ed. Boston, MA, USA: Pearson Education, 2012.",
        "[3] Lê Quốc Tuấn, \"Bài giảng An ninh Mạng — Chương 3: Bảo mật hệ thống mạng và Dữ liệu (Mục 3.3.1–3.3.5),\" Khoa Công nghệ Thông tin, Trường Đại học Giao thông vận tải TP. Hồ Chí Minh (UTH), 2026.",
    ]
    for r_text in refs:
        p_ref = doc.add_paragraph()
        p_ref.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p_ref.paragraph_format.left_indent = Inches(0.38)
        p_ref.paragraph_format.first_line_indent = Inches(-0.38)
        p_ref.paragraph_format.space_after = Pt(4)
        rr = p_ref.add_run(r_text)
        rr.font.size = Pt(10)

    out_root = BASE_DIR / "BaoCao_DeTai14_PKI_UTH.docx"
    out_docs = BASE_DIR / "docs" / "report" / "BaoCao_DeTai14_PKI_UTH.docx"
    out_docs.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out_root))
    doc.save(str(out_docs))
    print(f"Generated Main Report: {out_root} and {out_docs}")


def create_image_appendix():
    doc = configure_base_document()
    h = make_helpers(doc)

    # Cover / Header Page for Image Appendix
    add_cover_header(
        doc,
        "Tập hợp 13 ảnh chụp minh chứng thực nghiệm (Fig. 1 – Fig. 13) đồng bộ với báo cáo chính "
        "BaoCao_DeTai14_PKI_UTH.docx trên môi trường Docker Compose (các container Linux Alpine) chạy trên nền hệ điều hành Windows",
        "PHỤ LỤC HÌNH ẢNH MINH CHỨNG THỰC NGHIỆM (PROJECT_ANM)",
    )
    doc.add_page_break()

    # Index Table of Figures
    h["h1"]("DANH MỤC HÌNH ẢNH MINH CHỨNG (LIST OF FIGURES)")
    idx_headers = ["Ký hiệu", "Tệp ảnh nguồn", "Tiêu đề minh chứng"]
    idx_rows = [(f"Fig. {num}", fname, title) for num, fname, title, _ in FIGURES]
    h["table"](
        "BẢNG TRA CỨU ĐỒNG BỘ HÌNH ẢNH MINH CHỨNG (Fig. 1 – Fig. 13)",
        idx_headers,
        idx_rows,
        [0.85, 1.35, 4.4],
        center_cols=[0, 1],
    )

    h["h1"]("CHI TIẾT HÌNH ẢNH MINH CHỨNG THỰC NGHIỆM (Fig. 1 – Fig. 13)")
    for fig_num, img_name, title, desc in FIGURES:
        h["fig"](fig_num, img_name, title, desc)

    out_root = BASE_DIR / "PROJECT_ANM.docx"
    out_docs = BASE_DIR / "docs" / "report" / "PROJECT_ANM.docx"
    out_docs.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out_root))
    doc.save(str(out_docs))
    print(f"Generated Image Appendix: {out_root} and {out_docs}")


if __name__ == "__main__":
    create_report()
    create_image_appendix()
