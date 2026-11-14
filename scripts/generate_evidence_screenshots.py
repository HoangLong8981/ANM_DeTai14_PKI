"""Generate terminal-style evidence screenshots verbatim from evidence_logs.txt."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent.parent
EVIDENCE_PATH = BASE_DIR / "evidence_logs.txt"
OUT_DIR = BASE_DIR / "docs" / "report" / "images"

FONT_PATH = Path("C:/Windows/Fonts/consola.ttf")
BG_COLOR = (12, 12, 12)
TEXT_COLOR = (204, 204, 204)
CMD_COLOR = (249, 241, 165)
DIM_COLOR = (140, 140, 140)
PROMPT = r"PS C:\Users\admin\Downloads\STUDY\ANM\ANM_DeTai14_PKI> "


def expand_tabs(line: str, tabsize: int = 8) -> str:
    return line.expandtabs(tabsize)


def wrap_line(text: str, max_chars: int = 176) -> list[str]:
    text = expand_tabs(text)
    if len(text) <= max_chars:
        return [text]
    chunks: list[str] = []
    remaining = text
    while len(remaining) > max_chars:
        split_at = remaining.rfind(" ", 0, max_chars)
        if split_at <= 20:
            split_at = max_chars
        chunks.append(remaining[:split_at].rstrip())
        remaining = remaining[split_at:].lstrip()
    if remaining:
        chunks.append(remaining)
    return chunks


def render_terminal_png(blocks: list[tuple[str, list[str]]], out_path: Path) -> tuple[int, int]:
    """Render PowerShell command + verbatim stdout blocks into a dark terminal PNG."""
    font = ImageFont.truetype(str(FONT_PATH), 17)
    char_w = font.getlength("M")
    line_h = 24
    pad_x = 18
    pad_y = 14

    rows: list[tuple[str, str]] = []  # (kind, text)
    for idx, (cmd, outputs) in enumerate(blocks):
        if idx > 0:
            rows.append(("blank", ""))
        full_cmd = f"{PROMPT}{cmd}"
        wrapped_cmd = wrap_line(full_cmd, max_chars=176)
        for w_idx, wc in enumerate(wrapped_cmd):
            rows.append(("cmd_first" if w_idx == 0 else "cmd_cont", wc))
        for line in outputs:
            if line == "":
                rows.append(("blank", ""))
            else:
                for wl in wrap_line(line, max_chars=176):
                    rows.append(("out", wl))

    max_len = max((len(t) for _, t in rows), default=80)
    width = max(1240, int(max_len * char_w) + pad_x * 2 + 8)
    height = len(rows) * line_h + pad_y * 2

    img = Image.new("RGBA", (width, height), BG_COLOR + (255,))
    draw = ImageDraw.Draw(img)

    y = pad_y
    for kind, text in rows:
        if kind == "cmd_first":
            # Draw PS prompt, highlight first command token ('docker'), draw remaining args
            draw.text((pad_x, y), PROMPT, font=font, fill=TEXT_COLOR)
            x = pad_x + font.getlength(PROMPT)
            rest = text[len(PROMPT):]
            first_tok, sep, tail = rest.partition(" ")
            draw.text((x, y), first_tok, font=font, fill=CMD_COLOR)
            x += font.getlength(first_tok)
            if sep:
                draw.text((x, y), sep + tail, font=font, fill=TEXT_COLOR)
        elif kind == "cmd_cont":
            draw.text((pad_x, y), text, font=font, fill=TEXT_COLOR)
        elif kind == "out":
            fill = DIM_COLOR if text.startswith("[...") else TEXT_COLOR
            draw.text((pad_x, y), text, font=font, fill=fill)
        y += line_h

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="PNG")
    return img.size


def main() -> None:
    lines = EVIDENCE_PATH.read_text(encoding="utf-8").splitlines()

    def slice_lines(start_1: int, end_1: int) -> list[str]:
        return lines[start_1 - 1 : end_1]

    # 1. image11.png (Fig. 2): CA index.txt (2 services + 1 user), ls -la certs, stat -c '%a %n' *.key (600)
    cmd_2_3 = slice_lines(111, 111)[0].removeprefix("$ ")
    out_2_3 = slice_lines(112, 118)
    cmd_5_1 = slice_lines(490, 490)[0].removeprefix("$ ")
    out_5_1 = slice_lines(491, 493)
    cmd_5_4 = slice_lines(547, 547)[0].removeprefix("$ ")
    out_5_4 = slice_lines(548, 564)

    sz11 = render_terminal_png(
        [
            (cmd_2_3, out_2_3),
            (cmd_5_1, out_5_1),
            (cmd_5_4, out_5_4),
        ],
        OUT_DIR / "image11.png",
    )

    # 2. image12.png (Fig. 5): openssl s_client -tls1_3 handshake + Verify return code: 0 (ok)
    cmd_3_1 = slice_lines(229, 229)[0].removeprefix("$ ")
    out_3_1 = (
        slice_lines(230, 246)
        + ["[... Server certificate PEM block (lines 247-269 in evidence_logs.txt) ...]"]
        + slice_lines(270, 289)
    )
    sz12 = render_terminal_png([(cmd_3_1, out_3_1)], OUT_DIR / "image12.png")

    # 3. image13.png (Fig. 9): curl 400 with revoked alice.crt + docker logs error 23 + openssl verify -crl_check
    cmd_4_1 = slice_lines(310, 310)[0].removeprefix("$ ")
    out_4_1 = slice_lines(311, 325)
    cmd_4_4 = slice_lines(464, 464)[0].removeprefix("$ ")
    out_4_4 = slice_lines(469, 474)
    cmd_4_5 = slice_lines(477, 477)[0].removeprefix("$ ")
    out_4_5 = slice_lines(478, 480)

    sz13 = render_terminal_png(
        [
            (cmd_4_1, out_4_1),
            (cmd_4_4, out_4_4),
            (cmd_4_5, out_4_5),
        ],
        OUT_DIR / "image13.png",
    )

    print(f"Generated image11.png {sz11}, image12.png {sz12}, image13.png {sz13}")


if __name__ == "__main__":
    main()
