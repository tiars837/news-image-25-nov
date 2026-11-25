#!/usr/bin/env python3
"""The World in One Day — Wednesday, 25 November 2026.

Draws a one-page newspaper poster summing up 25 November 2026 world news
and writes it to /output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png).

Python 3.13 standard library only. No network. Fully deterministic:
the same bytes are written on every run.
"""

import os
import struct
import sys
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- colours
PAPER = (250, 247, 240)
INK = (20, 20, 20)
RED = (166, 30, 34)
NAVY = (29, 53, 87)
BLUE_PANEL = (232, 236, 241)
GREY = (90, 90, 90)
WHITE = (255, 255, 255)
GOLD = (214, 164, 32)

# ---------------------------------------------------------------- 5x7 font
# Each glyph is 7 rows; each row is a 5-bit value, bit 4 = leftmost pixel.
FONT = {
    "A": (0b01110, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001),
    "B": (0b11110, 0b10001, 0b10001, 0b11110, 0b10001, 0b10001, 0b11110),
    "C": (0b01110, 0b10001, 0b10000, 0b10000, 0b10000, 0b10001, 0b01110),
    "D": (0b11110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b11110),
    "E": (0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b11111),
    "F": (0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b10000),
    "G": (0b01110, 0b10001, 0b10000, 0b10111, 0b10001, 0b10001, 0b01111),
    "H": (0b10001, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001),
    "I": (0b01110, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110),
    "J": (0b00111, 0b00010, 0b00010, 0b00010, 0b00010, 0b10010, 0b01100),
    "K": (0b10001, 0b10010, 0b10100, 0b11000, 0b10100, 0b10010, 0b10001),
    "L": (0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b11111),
    "M": (0b10001, 0b11011, 0b10101, 0b10101, 0b10001, 0b10001, 0b10001),
    "N": (0b10001, 0b11001, 0b10101, 0b10011, 0b10001, 0b10001, 0b10001),
    "O": (0b01110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110),
    "P": (0b11110, 0b10001, 0b10001, 0b11110, 0b10000, 0b10000, 0b10000),
    "Q": (0b01110, 0b10001, 0b10001, 0b10001, 0b10101, 0b10010, 0b01101),
    "R": (0b11110, 0b10001, 0b10001, 0b11110, 0b10100, 0b10010, 0b10001),
    "S": (0b01111, 0b10000, 0b10000, 0b01110, 0b00001, 0b00001, 0b11110),
    "T": (0b11111, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100),
    "U": (0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110),
    "V": (0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01010, 0b00100),
    "W": (0b10001, 0b10001, 0b10001, 0b10101, 0b10101, 0b10101, 0b01010),
    "X": (0b10001, 0b10001, 0b01010, 0b00100, 0b01010, 0b10001, 0b10001),
    "Y": (0b10001, 0b10001, 0b01010, 0b00100, 0b00100, 0b00100, 0b00100),
    "Z": (0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b10000, 0b11111),
    "0": (0b01110, 0b10001, 0b10011, 0b10101, 0b11001, 0b10001, 0b01110),
    "1": (0b00100, 0b01100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110),
    "2": (0b01110, 0b10001, 0b00001, 0b00110, 0b01000, 0b10000, 0b11111),
    "3": (0b11111, 0b00010, 0b00100, 0b00010, 0b00001, 0b10001, 0b01110),
    "4": (0b00010, 0b00110, 0b01010, 0b10010, 0b11111, 0b00010, 0b00010),
    "5": (0b11111, 0b10000, 0b11110, 0b00001, 0b00001, 0b10001, 0b01110),
    "6": (0b00110, 0b01000, 0b10000, 0b11110, 0b10001, 0b10001, 0b01110),
    "7": (0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b01000, 0b01000),
    "8": (0b01110, 0b10001, 0b10001, 0b01110, 0b10001, 0b10001, 0b01110),
    "9": (0b01110, 0b10001, 0b10001, 0b01111, 0b00001, 0b00010, 0b01100),
    " ": (0, 0, 0, 0, 0, 0, 0),
    ".": (0, 0, 0, 0, 0, 0b01100, 0b01100),
    ",": (0, 0, 0, 0, 0b01100, 0b00100, 0b01000),
    "-": (0, 0, 0, 0b01110, 0, 0, 0),
    "\u2014": (0, 0, 0, 0b11111, 0, 0, 0),
    "'": (0b00100, 0b00100, 0b01000, 0, 0, 0, 0),
    "!": (0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0, 0b00100),
    "?": (0b01110, 0b10001, 0b00001, 0b00110, 0b00100, 0, 0b00100),
    ":": (0, 0b01100, 0b01100, 0, 0b01100, 0b01100, 0),
    ";": (0, 0b01100, 0b01100, 0, 0b01100, 0b00100, 0b01000),
    "/": (0b00001, 0b00010, 0b00010, 0b00100, 0b01000, 0b01000, 0b10000),
    "(": (0b00010, 0b00100, 0b01000, 0b01000, 0b01000, 0b00100, 0b00010),
    ")": (0b01000, 0b00100, 0b00010, 0b00010, 0b00010, 0b00100, 0b01000),
    "%": (0b11001, 0b11010, 0b00010, 0b00100, 0b01000, 0b01011, 0b10011),
    "&": (0b01100, 0b10010, 0b10100, 0b01000, 0b10101, 0b10010, 0b01101),
    "+": (0, 0b00100, 0b00100, 0b11111, 0b00100, 0b00100, 0),
    "=": (0, 0, 0b11111, 0, 0b11111, 0, 0),
    '"': (0b01010, 0b01010, 0, 0, 0, 0, 0),
    "*": (0, 0b10101, 0b01110, 0b11111, 0b01110, 0b10101, 0),
    "$": (0b00100, 0b01111, 0b10100, 0b01110, 0b00101, 0b11110, 0b00100),
    "#": (0b01010, 0b01010, 0b11111, 0b01010, 0b11111, 0b01010, 0b01010),
    "@": (0b01110, 0b10001, 0b10111, 0b10101, 0b10110, 0b10000, 0b01110),
    "[": (0b01110, 0b01000, 0b01000, 0b01000, 0b01000, 0b01000, 0b01110),
    "]": (0b01110, 0b00010, 0b00010, 0b00010, 0b00010, 0b00010, 0b01110),
    "_": (0, 0, 0, 0, 0, 0, 0b11111),
    "~": (0, 0, 0b01101, 0b10110, 0, 0, 0),
    "<": (0b00010, 0b00100, 0b01000, 0b10000, 0b01000, 0b00100, 0b00010),
    ">": (0b01000, 0b00100, 0b00010, 0b00001, 0b00010, 0b00100, 0b01000),
    "|": (0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100),
    "\\": (0b10000, 0b01000, 0b01000, 0b00100, 0b00010, 0b00010, 0b00001),
    "^": (0b00100, 0b01010, 0b10001, 0, 0, 0, 0),
    "`": (0b01000, 0b00100, 0, 0, 0, 0, 0),
    "{": (0b00110, 0b01000, 0b01000, 0b11100, 0b01000, 0b01000, 0b00110),
    "}": (0b01100, 0b00010, 0b00010, 0b00111, 0b00010, 0b00010, 0b01100),
    "\u2022": (0, 0, 0b00100, 0b01110, 0b01110, 0b00100, 0),
}

CHAR_W = 6  # 5 pixels + 1 pixel gap, before scaling


def text_width(text, scale):
    return len(text) * CHAR_W * scale - scale


def wrap_text(text, max_w, scale):
    """Greedy word wrap; returns a list of lines fitting max_w pixels."""
    lines, cur = [], ""
    for word in text.split(" "):
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ------------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(w * h * 3)
        self.fill(0, 0, w, h, bg)

    def _set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = color

    def fill(self, x, y, w, h, color):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i], self.px[i + 1], self.px[i + 2] = color

    def hline(self, x, y, w, color, thick=1):
        self.fill(x, y, w, thick, color)

    def vline(self, x, y, h, color, thick=1):
        self.fill(x, y, thick, h, color)

    def rect(self, x, y, w, h, color, thick=1):
        self.hline(x, y, w, color, thick)
        self.hline(x, y + h - thick, w, color, thick)
        self.vline(x, y, h, color, thick)
        self.vline(x + w - thick, y, h, color, thick)

    def line(self, x0, y0, x1, y1, color):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err, x, y = dx - dy, x0, y0
        while True:
            self._set(x, y, color)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    def circle(self, cx, cy, r, color, fill=False):
        import math

        for dy in range(-r, r + 1):
            dx = int(math.sqrt(r * r - dy * dy))
            if fill:
                self.fill(cx - dx, cy + dy, dx * 2 + 1, 1, color)
            else:
                self._set(cx - dx, cy + dy, color)
                self._set(cx + dx, cy + dy, color)

    def text(self, x, y, s, scale, color):
        cx = x
        for ch in s:
            glyph = FONT.get(ch.upper(), FONT[" "])
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits & (1 << (4 - col)):
                        self.fill(cx + col * scale, y + row * scale,
                                  scale, scale, color)
            cx += CHAR_W * scale
        return cx

    def text_center(self, y, s, scale, color):
        w = text_width(s, scale)
        return self.text((self.w - w) // 2, y, s, scale, color)


# ---------------------------------------------------------------- PNG encode
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(canvas, path):
    raw = bytearray()
    stride = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)
        raw += canvas.px[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


# ------------------------------------------------------------------- poster
LEAD_HEAD = "CIA AND SPY CHIEF'S OFFICE HACKED"
LEAD_BODY = (
    "An apparent hack hit unclassified systems used for open-source "
    "intelligence at the CIA and the spy chief's office. No classified "
    "data was touched, officials said; early signs point to China. "
    "The breach is unrelated to the FBI database hack reported last week."
)
LEAD_TAIL = "Latest in a string of U.S. government cyber incidents."

STORIES = [
    ("MARKETS",
     "ASIAN MARKETS SLIDE AS AI RALLY FADES",
     "Stocks tumbled across Asia as fresh U.S. tariff threats hit "
     "sentiment: Seoul fell 5.3%, Taiwan 5.1% and Tokyo 2.9%. Nvidia "
     "gave back 5.9% a day after its 31.5% surge."),
    ("SPACE",
     "PAKISTAN'S FIRST ASTRONAUT REACHES ORBIT",
     "Shenzhou-24 blasted off from Jiuquan carrying Muhammad Zeeshan "
     "Ali, the first Pakistani in orbit and the first foreign astronaut "
     "aboard China's Tiangong station."),
    ("COLOMBIA",
     "30 HOSTAGES SEIZED IN CARTAGENA SUPERMARKET",
     "Gunmen fled into an Exito store after a botched armoured-truck "
     "robbery. Ten elderly women were freed; about 20 people were "
     "still held as troops ringed the shop."),
    ("AFRICA",
     "WHO PULLS EBOLA STAFF OUT OF CONGO HOSPITAL",
     "Health workers were evacuated from a hospital in Akwe, Ituri, "
     "after three days sheltering from fighting. The Ebola outbreak "
     "has killed 5,775 of 11,762 cases."),
    ("WAR",
     "RUSSIA CALLS UKRAINE DRONE STRIKES 'TERRORISM'",
     "Moscow accused Kyiv after drones hit a Russian cargo ship in the "
     "Gulf of Finland and a warship off Libya, and warned of severe "
     "consequences."),
]

ALSO_TODAY = [
    "NATO vows space defence \u2022 Huawei guilty on 10 of 12 counts",
    "Giuliani gets Medal of Freedom \u2022 N. Korea threatens Swiss office",
]


def draw_lead_art(c):
    """Shield-and-keyhole illustration in the navy panel."""
    x0, y0, x1, y1 = 692, 132, 992, 420
    c.fill(x0, y0, x1 - x0, y1 - y0, NAVY)
    cx, cy = 842, 262
    # ring
    for r in range(96, 88, -1):
        c.circle(cx, cy, r, WHITE)
    # keyhole: circle + stem
    c.circle(cx, cy - 18, 30, WHITE, fill=True)
    c.fill(cx - 13, cy + 2, 26, 58, WHITE)
    # network nodes at the four diagonals
    for nx, ny in ((742, 178), (942, 178), (742, 346), (942, 346)):
        c.fill(nx - 7, ny - 7, 14, 14, RED)
        c.line(cx, cy, nx, ny, WHITE)
    # small caption bar at the panel bottom
    c.fill(x0, y1 - 26, x1 - x0, 26, (16, 30, 52))
    c.text_center(y1 - 19, "UNCLASSIFIED SYSTEMS HIT", 1, (200, 210, 225))


def draw_icon(c, kind, x, y):
    """72x72 icon box glyphs, drawn with plain shapes."""
    c.fill(x, y, 72, 72, BLUE_PANEL)
    c.rect(x, y, 72, 72, INK, 2)
    if kind == "MARKETS":
        # falling bars, red
        c.fill(x + 12, y + 22, 12, 38, RED)
        c.fill(x + 30, y + 32, 12, 28, RED)
        c.fill(x + 48, y + 44, 12, 16, RED)
        c.hline(x + 8, y + 62, 56, INK, 2)
    elif kind == "SPACE":
        # rocket: body, nose, fins, flame
        c.fill(x + 30, y + 16, 12, 30, NAVY)
        c.fill(x + 27, y + 10, 18, 8, NAVY)
        c.fill(x + 24, y + 38, 6, 10, NAVY)
        c.fill(x + 42, y + 38, 6, 10, NAVY)
        c.fill(x + 32, y + 48, 8, 12, GOLD)
        c.circle(x + 36, y + 26, 5, WHITE, fill=True)
    elif kind == "COLOMBIA":
        # shopfront with striped awning
        for i in range(4):
            c.fill(x + 10 + i * 14, y + 12, 12, 10,
                   RED if i % 2 == 0 else WHITE)
        c.rect(x + 10, y + 22, 52, 38, INK, 2)
        c.fill(x + 30, y + 38, 12, 22, NAVY)
        c.fill(x + 14, y + 28, 12, 8, NAVY)
        c.fill(x + 46, y + 28, 12, 8, NAVY)
    elif kind == "AFRICA":
        # red disc with a white medical cross
        c.circle(x + 36, y + 36, 26, RED, fill=True)
        c.fill(x + 32, y + 18, 8, 36, WHITE)
        c.fill(x + 18, y + 32, 36, 8, WHITE)
    elif kind == "WAR":
        # quadcopter drone
        c.fill(x + 28, y + 30, 16, 12, NAVY)
        for rx, ry in ((16, 16), (56, 16), (16, 56), (56, 56)):
            c.line(x + 36, y + 36, x + rx, y + ry, INK)
            c.circle(x + rx, y + ry, 7, INK)
            c.circle(x + rx, y + ry, 3, WHITE, fill=True)


def draw_poster():
    c = Canvas(W, H, PAPER)
    # masthead
    c.fill(0, 0, W, 8, RED)
    c.text_center(28, "THE WORLD IN ONE DAY", 4, INK)
    c.text_center(74, "WEDNESDAY, 25 NOVEMBER 2026", 2, GREY)
    c.hline(32, 106, 960, INK, 4)
    c.hline(32, 114, 960, INK, 2)
    # lead
    c.text(32, 134, "LEAD  \u2022  CYBERATTACK ON U.S. SPY AGENCIES", 2, RED)
    y = 162
    for line in wrap_text(LEAD_HEAD, 628, 3):
        c.text(32, y, line, 3, INK)
        y += 27
    y += 6
    for line in wrap_text(LEAD_BODY, 628, 2):
        c.text(32, y, line, 2, INK)
        y += 18
    y += 8
    c.text(32, y, LEAD_TAIL, 2, GREY)
    draw_lead_art(c)
    # divider
    c.hline(32, 436, 960, INK, 3)
    # five stories
    y0 = 452
    for i, (kind, head, body) in enumerate(STORIES):
        ry = y0 + i * 88
        draw_icon(c, kind, 32, ry)
        c.text(124, ry + 2, head, 2, INK)
        by = ry + 28
        for line in wrap_text(body, 868, 2):
            c.text(124, by, line, 2, INK)
            by += 18
    # also today
    c.hline(32, 892, 960, INK, 2)
    c.text(32, 908, "ALSO TODAY", 2, RED)
    c.text(32, 932, ALSO_TODAY[0], 2, INK)
    c.text(32, 952, ALSO_TODAY[1], 2, INK)
    # footer
    c.text_center(988, "SOURCES: REUTERS \u2022 CNN \u2022 AP \u2022 XINHUA  "
                  "\u2014  WEDNESDAY, 25 NOVEMBER 2026", 1, GREY)
    return c


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    # Clear only the contents of the output directory, never the dir itself.
    for name in os.listdir(out_dir):
        path = os.path.join(out_dir, name)
        if os.path.isdir(path):
            import shutil
            shutil.rmtree(path)
        else:
            os.unlink(path)
    canvas = draw_poster()
    out_path = os.path.join(out_dir, "entry.png")
    size = write_png(canvas, out_path)
    print("wrote %s (%d bytes)" % (out_path, size))
    return 0


if __name__ == "__main__":
    sys.exit(main())
