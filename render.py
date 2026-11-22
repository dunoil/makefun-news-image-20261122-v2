#!/usr/bin/env python3
"""Render the Sunday 22 November 2026 world news broadsheet, 1024x1024.

Drawn with Pillow from the story list below. Deterministic: fixed seed,
no timestamps, fixed fonts, so repeated runs produce identical bytes.
"""
import math
import random
from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
M = 24
CW = W - 2 * M
PAPER = (247, 243, 232)
INK = (26, 26, 26)
RED = (163, 22, 33)
BLUE = (29, 78, 137)
GOLD = (176, 132, 52)
GREY = (90, 86, 76)
LIGHT = (233, 227, 210)
SEA = (214, 230, 236)
LAND = (232, 222, 188)
LAND_LINE = (170, 150, 110)

SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


def wrap(draw, text, fnt, width):
    """Wrap text to pixel width; returns list of lines."""
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=fnt) <= width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(draw, x, y, text, fnt, width, fill, max_lines, leading):
    lines = wrap(draw, text, fnt, width)
    assert len(lines) <= max_lines, "TEXT OVERFLOW: %r -> %d lines (max %d)" % (
        text, len(lines), max_lines)
    for i, line in enumerate(lines):
        draw.text((x, y + i * leading), line, font=fnt, fill=fill)
    return y + len(lines) * leading


# ---------------------------------------------------------------- stories
# Each illustrated story: number, headline, one-sentence body, scene, region,
# and map position (lon, lat) plus an optional pin offset in pixels.
LEADS = [
    dict(n=1, head="COP31 deadlocked on day 14 in Antalya",
         body="Talks ran into overtime with no deal, as the draft text dropped every mention of fossil fuels.",
         scene="cop", region="Global", lon=30.7, lat=36.9, off=(0, 0)),
    dict(n=2, head="Magnitude 6.9 quake shakes Peru's Andes",
         body="The tremor was felt in Lima, and no damage or casualties were reported at once.",
         scene="quake", region="Americas", lon=-75.0, lat=-10.0, off=(0, 0)),
    dict(n=3, head="Iran strikes US base in Kuwait, targets Bahrain",
         body="Tehran hit a US air base in Kuwait and threatened Bahrain as the Gulf crisis widened.",
         scene="gulf", region="Middle East", lon=48.0, lat=29.4, off=(0, 0)),
]

SMALL = [
    dict(n=4, head="Trump seeks permanent Iran accord",
         body="Washington said it wants a lasting deal with Tehran.",
         scene="accord", region="Middle East", lon=51.4, lat=35.7, off=(-24, -14)),
    dict(n=5, head="Russian strike on Lviv kills two",
         body="A missile hit the western city overnight, officials said.",
         scene="lviv", region="Europe", lon=24.0, lat=49.8, off=(0, 0)),
    dict(n=6, head="Hong Kong voting opens",
         body="Some 5,700 voters began choosing the Election Committee.",
         scene="hk", region="Asia-Pacific", lon=114.2, lat=22.3, off=(0, -16)),
    dict(n=7, head="Trump and Xi trade warm words",
         body="The leaders spoke warmly before APEC meets in Shenzhen.",
         scene="apex", region="Asia-Pacific", lon=114.1, lat=22.5, off=(30, 8)),
    dict(n=8, head="EU and Indonesia sign trade deal",
         body="The pact cuts tariffs and deepens ties, both sides said.",
         scene="trade", region="Europe", lon=106.8, lat=-6.2, off=(0, 0)),
    dict(n=9, head="Modi opens Nitish Setu bridge",
         body="The new crossing spans the Ganges in Bihar, officials said.",
         scene="bridge", region="South Asia", lon=85.5, lat=25.6, off=(0, -16)),
    dict(n=10, head="Two tankers hit in Hormuz",
         body="Projectiles struck two tankers in the strait, shippers said.",
         scene="tanker", region="Middle East", lon=56.5, lat=26.5, off=(18, 12)),
    dict(n=11, head="Crude oil futures fall over 3%",
         body="Prices slid as Gulf fears eased and supply worries faded.",
         scene="oil", region="Global", lon=0.0, lat=51.5, off=(0, 0)),
    dict(n=12, head="India face New Zealand in Wellington",
         body="Wind gusts tested both sides in the first Test session.",
         scene="cricket", region="Asia-Pacific", lon=174.8, lat=-41.3, off=(0, 0)),
    dict(n=13, head="Cyclone Akvan cancels 14 flights",
         body="Flights were halted at Ranchi as the storm closed in.",
         scene="cyclone", region="South Asia", lon=85.3, lat=23.3, off=(-28, 12)),
]

BRIEFS = [
    ("Lima schools close as a precaution after the quake", "Americas"),
    ("Peru president heads to the quake zone to inspect damage", "Americas"),
    ("Canada wildfire crews stand down as winter arrives", "Americas"),
    ("Chile lithium auction draws strong foreign bids", "Americas"),
    ("Kuwait says its air defences are on high alert", "Middle East"),
    ("Bahrain urges calm after threats from Tehran", "Middle East"),
    ("UN aid convoy reaches Gaza crossing with food", "Middle East"),
    ("EU leaders welcome the Indonesia trade deal", "Europe"),
    ("UK announces a new green energy auction", "Europe"),
    ("France unveils a major rail upgrade plan", "Europe"),
    ("Hong Kong turnout holds steady at midday", "Asia-Pacific"),
    ("APEC leaders arrive in Shenzhen for the summit", "Asia-Pacific"),
    ("Japan PM pledges faster wage growth in budget speech", "Asia-Pacific"),
    ("Australia unveils new climate aid for Pacific islands", "Asia-Pacific"),
    ("Bihar crowds gather for the bridge opening", "South Asia"),
    ("Ranchi airport reopens after the cyclone passes", "South Asia"),
    ("Kenya opens a new wind farm extension", "Africa"),
    ("Egypt opens a new wing of its Cairo museum", "Africa"),
    ("Nigeria central bank holds interest rates", "Africa"),
    ("UN chief urges a COP31 deal before midnight", "Global"),
    ("Gold edges up as investors seek safety", "Global"),
    ("NASA readies a briefing on the Artemis II crew", "Global"),
]

REGIONS = ["Middle East", "Asia-Pacific", "Europe", "Americas",
           "Global", "South Asia", "Africa"]
REGION_COLOURS = {"Middle East": (163, 22, 33), "Asia-Pacific": (29, 78, 137),
                  "Europe": (46, 110, 88), "Americas": (176, 132, 52),
                  "Global": (90, 86, 76), "South Asia": (146, 74, 140),
                  "Africa": (190, 110, 40)}

STATS = [("35", "STORIES"), ("7", "REGIONS"), ("13", "ILLUSTRATED"),
         ("22", "BRIEFS"), ("6.9", "QUAKE MAG."), ("14", "COP31 DAY")]

EXCLUDED = ("DATE CHECK: these stories are NOT from 22 November and are excluded: "
            "COP31 overtime day 13 (21 Nov); five missiles shot down over Saudi "
            "Arabia (21 Nov); the 6.7 Peru quake (21 Nov); BepiColombo Mercury "
            "orbit (21 Nov); Trump-Xi-Putin trilateral in Shenzhen (21 Nov).")


# ---------------------------------------------------------------- scenes
def scene(draw, key, x, y, w, h):
    """Flat illustrated scene for one card, inside box (x, y, w, h)."""
    if key == "cop":
        draw.rectangle([x, y, x + w, y + h], fill=(58, 90, 110))
        draw.rectangle([x, y + h - 26, x + w, y + h], fill=(40, 64, 80))
        for i in range(5):
            fx = x + 16 + i * (w - 32) // 5
            draw.line([fx, y + 14, fx, y + h - 26], fill=(200, 200, 190), width=2)
            draw.rectangle([fx, y + 14, fx + 18, y + 26],
                           fill=[(247, 243, 232), (240, 200, 90), (120, 170, 120),
                                 (163, 22, 33), (29, 78, 137)][i])
        draw.ellipse([x + w // 2 - 22, y + h - 58, x + w // 2 + 22, y + h - 14],
                     fill=(240, 200, 90))
        draw.text((x + w // 2 - 14, y + h - 46), "COP31", font=font(SANS_B, 11),
                  fill=(40, 64, 80))
    elif key == "quake":
        draw.rectangle([x, y, x + w, y + h], fill=(196, 164, 120))
        draw.polygon([(x, y + h), (x + w * 0.3, y + 8), (x + w * 0.55, y + h)],
                     fill=(110, 90, 80))
        draw.polygon([(x + w * 0.4, y + h), (x + w * 0.7, y + 4),
                      (x + w, y + h)], fill=(140, 118, 100))
        draw.polygon([(x + w * 0.3, y + 8), (x + w * 0.34, y + 8),
                      (x + w * 0.42, y + 40), (x + w * 0.5, y + 70),
                      (x + w * 0.46, y + 70), (x + w * 0.38, y + 40)],
                     fill=(60, 45, 40))
        draw.rectangle([x + 12, y + h - 22, x + 52, y + h - 6], fill=(90, 70, 60))
        draw.rectangle([x + w - 52, y + h - 26, x + w - 12, y + h - 6],
                       fill=(90, 70, 60))
        draw.line([x + 60, y + h - 6, x + w - 60, y + h - 6], fill=(60, 45, 40), width=2)
    elif key == "gulf":
        draw.rectangle([x, y, x + w, y + h], fill=(232, 150, 60))
        draw.rectangle([x, y + h * 0.62, x + w, y + h], fill=(40, 90, 110))
        draw.polygon([(x + w * 0.5, y + 8), (x + w * 0.56, y + 30),
                      (x + w * 0.72, y + 30), (x + w * 0.6, y + 42),
                      (x + w * 0.66, y + 62), (x + w * 0.5, y + 50),
                      (x + w * 0.34, y + 62), (x + w * 0.4, y + 42),
                      (x + w * 0.28, y + 30), (x + w * 0.44, y + 30)],
                     fill=(255, 220, 80))
        draw.rectangle([x + 14, y + h - 22, x + 60, y + h - 12], fill=(70, 70, 70))
        draw.rectangle([x + w - 60, y + h - 22, x + w - 14, y + h - 12],
                       fill=(70, 70, 70))
    elif key == "accord":
        draw.rectangle([x, y, x + w, y + h], fill=(29, 78, 137))
        draw.rectangle([x, y, x + w // 2, y + h], fill=(163, 22, 33))
        draw.ellipse([x + w // 2 - 24, y + h // 2 - 24, x + w // 2 + 24,
                      y + h // 2 + 24], fill=(247, 243, 232))
        draw.text((x + w // 2 - 7, y + h // 2 - 11), "US", font=font(SANS_B, 16),
                  fill=INK)
        draw.rectangle([x + 10, y + 8, x + w // 2 - 10, y + 16], fill=(247, 243, 232))
        draw.rectangle([x + w // 2 + 10, y + h - 16, x + w - 10, y + h - 8],
                       fill=(247, 243, 232))
    elif key == "lviv":
        draw.rectangle([x, y, x + w, y + h], fill=(52, 52, 66))
        for i, bh in enumerate([30, 46, 38, 52, 34]):
            bx = x + 8 + i * (w - 16) // 5
            draw.rectangle([bx, y + h - bh, bx + (w - 16) // 5 - 4, y + h],
                           fill=(30, 30, 42))
        draw.ellipse([x + w - 34, y + 8, x + w - 12, y + 30], fill=(240, 220, 160))
        draw.polygon([(x + w * 0.3, y + 10), (x + w * 0.36, y + 26),
                      (x + w * 0.44, y + 26), (x + w * 0.38, y + 40),
                      (x + w * 0.46, y + 40), (x + w * 0.34, y + 58),
                      (x + w * 0.26, y + 58), (x + w * 0.3, y + 40),
                      (x + w * 0.24, y + 40), (x + w * 0.3, y + 26)],
                     fill=(255, 170, 60))
    elif key == "hk":
        draw.rectangle([x, y, x + w, y + h], fill=(120, 160, 190))
        for i, bh in enumerate([40, 58, 48, 66, 44]):
            bx = x + 6 + i * (w - 12) // 5
            draw.rectangle([bx, y + h - bh - 18, bx + (w - 12) // 5 - 4, y + h - 18],
                           fill=(60, 80, 110))
        draw.rectangle([x + w // 2 - 22, y + h - 18, x + w // 2 + 22, y + h],
                       fill=(163, 22, 33))
        draw.rectangle([x + w // 2 - 26, y + h - 26, x + w // 2 + 26, y + h - 18],
                       fill=(247, 243, 232))
    elif key == "apex":
        draw.rectangle([x, y, x + w, y + h], fill=(214, 230, 236))
        draw.rectangle([x, y + h - 20, x + w, y + h], fill=(120, 160, 120))
        draw.polygon([(x + 18, y + h - 20), (x + 18, y + 10), (x + 66, y + 10),
                      (x + 66, y + h - 20)], fill=(163, 22, 33))
        draw.polygon([(x + w - 66, y + h - 20), (x + w - 66, y + 10),
                      (x + w - 18, y + 10), (x + w - 18, y + h - 20)],
                     fill=(29, 78, 137))
        draw.ellipse([x + w // 2 - 12, y + 18, x + w // 2 + 12, y + 42],
                     fill=(240, 200, 90))
    elif key == "trade":
        draw.rectangle([x, y, x + w, y + h], fill=(46, 110, 88))
        draw.ellipse([x + w // 2 - 30, y + 6, x + w // 2 + 30, y + h - 6],
                     outline=(240, 200, 90), width=3)
        for i in range(8):
            a = i * math.pi / 4
            px = x + w // 2 + int(22 * math.cos(a)) - 2
            py = y + h // 2 + int(22 * math.sin(a)) - 2
            draw.ellipse([px, py, px + 4, py + 4], fill=(240, 200, 90))
        draw.rectangle([x + 8, y + h - 16, x + w - 8, y + h - 10], fill=(163, 22, 33))
        draw.rectangle([x + 8, y + h - 10, x + w - 8, y + h - 4], fill=(247, 243, 232))
    elif key == "bridge":
        draw.rectangle([x, y, x + w, y + h], fill=(240, 200, 120))
        draw.rectangle([x, y + h * 0.6, x + w, y + h], fill=(70, 130, 170))
        draw.ellipse([x + w - 40, y + 8, x + w - 12, y + 36], fill=(255, 240, 180))
        draw.polygon([(x, y + h * 0.55), (x + w, y + h * 0.55),
                      (x + w, y + h * 0.62), (x, y + h * 0.62)], fill=(90, 60, 40))
        for i in range(4):
            px = x + 20 + i * (w - 40) // 3
            draw.line([px, y + 12, px, y + h * 0.55], fill=(90, 60, 40), width=2)
    elif key == "tanker":
        draw.rectangle([x, y, x + w, y + h], fill=(150, 180, 200))
        draw.rectangle([x, y + h * 0.55, x + w, y + h], fill=(40, 90, 130))
        for i, tx in enumerate([10, w // 2 + 6]):
            draw.rectangle([x + tx, y + h * 0.42, x + tx + w // 2 - 16,
                            y + h * 0.58], fill=(120, 50, 40))
            draw.rectangle([x + tx + 8, y + h * 0.32, x + tx + 30, y + h * 0.42],
                           fill=(90, 90, 90))
        draw.line([x + w // 2 - 10, y + 6, x + w // 2 + 10, y + h * 0.35],
                  fill=(255, 220, 80), width=3)
    elif key == "oil":
        draw.rectangle([x, y, x + w, y + h], fill=(247, 243, 232))
        draw.line([x + 10, y + 12, x + w - 10, y + h - 26], fill=(163, 22, 33), width=4)
        draw.polygon([(x + w - 26, y + h - 28), (x + w - 6, y + h - 28),
                      (x + w - 16, y + h - 14)], fill=(163, 22, 33))
        draw.rectangle([x + 12, y + h - 26, x + 36, y + h - 6], fill=(40, 40, 40))
        draw.rectangle([x + 12, y + h - 20, x + 36, y + h - 17], fill=(120, 120, 120))
        draw.rectangle([x + 12, y + h - 12, x + 36, y + h - 9], fill=(120, 120, 120))
    elif key == "cricket":
        draw.rectangle([x, y, x + w, y + h], fill=(120, 170, 90))
        draw.ellipse([x + w // 2 - 30, y + h - 26, x + w // 2 + 30, y + h - 6],
                     fill=(190, 150, 100))
        draw.line([x + w // 2 - 26, y + 10, x + w // 2 + 20, y + h - 22],
                  fill=(150, 110, 60), width=7)
        draw.ellipse([x + w - 30, y + 10, x + w - 14, y + 26], fill=(163, 22, 33))
        for i in range(3):
            ly = y + 12 + i * 10
            draw.line([x + 8, ly, x + 40, ly + 4], fill=(247, 243, 232), width=2)
    elif key == "cyclone":
        draw.rectangle([x, y, x + w, y + h], fill=(90, 110, 140))
        cx, cy = x + w // 2, y + h // 2
        for r in range(8, 34, 8):
            draw.arc([cx - r, cy - r, cx + r, cy + r], 20, 300,
                     fill=(247, 243, 232), width=4)
        draw.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=(240, 200, 90))
        draw.rectangle([x + 10, y + h - 14, x + w - 10, y + h - 6], fill=(60, 70, 90))


# ---------------------------------------------------------------- map
CONTINENTS = {
    "NORTH AMERICA": [(-165, 60), (-150, 70), (-125, 71), (-110, 73), (-95, 80),
                      (-85, 70), (-80, 73), (-75, 62), (-65, 60), (-60, 47),
                      (-70, 42), (-75, 35), (-80, 32), (-85, 30), (-90, 21),
                      (-95, 19), (-97, 16), (-105, 20), (-110, 23), (-115, 30),
                      (-125, 40), (-125, 48), (-140, 60), (-165, 60)],
    "SOUTH AMERICA": [(-80, 10), (-75, 5), (-80, -5), (-80, -15), (-75, -25),
                      (-70, -35), (-70, -45), (-65, -55), (-60, -50), (-55, -35),
                      (-50, -30), (-40, -20), (-35, -8), (-40, 0), (-50, 5),
                      (-60, 8), (-70, 11), (-80, 10)],
    "EUROPE": [(-10, 36), (-9, 43), (-2, 48), (-5, 50), (0, 51), (5, 53),
               (8, 57), (10, 59), (18, 56), (21, 55), (24, 58), (28, 60),
               (30, 62), (32, 70), (40, 68), (45, 66), (40, 60), (35, 55),
               (30, 50), (28, 45), (23, 40), (19, 42), (15, 44), (12, 44),
               (8, 44), (3, 43), (0, 39), (-2, 37), (-6, 36), (-10, 36)],
    "AFRICA": [(-6, 35), (0, 36), (10, 37), (11, 34), (20, 32), (32, 31),
               (35, 28), (34, 22), (38, 18), (40, 11), (43, 11), (48, 10),
               (51, 12), (48, 5), (42, -2), (40, -10), (35, -18), (32, -26),
               (28, -33), (20, -35), (17, -32), (14, -22), (12, -12), (13, -5),
               (9, 4), (4, 6), (-8, 5), (-13, 8), (-17, 15), (-17, 25),
               (-15, 30), (-10, 31), (-6, 35)],
    "ASIA": [(30, 36), (35, 36), (36, 42), (40, 45), (45, 48), (50, 50),
             (55, 55), (60, 60), (65, 68), (70, 72), (80, 73), (90, 75),
             (100, 77), (110, 76), (120, 73), (130, 72), (140, 72), (150, 70),
             (160, 69), (170, 66), (178, 65), (170, 60), (162, 60), (158, 55),
             (150, 59), (142, 55), (140, 50), (135, 43), (130, 38), (127, 35),
             (122, 32), (120, 28), (115, 23), (110, 20), (108, 12), (105, 8),
             (100, 7), (98, 10), (95, 16), (92, 21), (90, 22), (86, 20),
             (82, 17), (80, 13), (77, 8), (75, 12), (72, 20), (68, 22),
             (62, 25), (58, 25), (55, 26), (52, 26), (50, 29), (48, 30),
             (44, 29), (40, 30), (36, 36), (30, 36)],
    "OCEANIA": [(113, -22), (114, -30), (115, -35), (120, -34), (125, -33),
                (130, -32), (135, -35), (140, -38), (145, -38), (150, -37),
                (153, -32), (150, -27), (146, -19), (142, -11), (137, -12),
                (132, -12), (126, -14), (122, -17), (118, -20), (113, -22)],
}
LABELS = {"NORTH AMERICA": (-125, 52), "SOUTH AMERICA": (-62, -18),
          "EUROPE": (12, 52), "AFRICA": (20, 2), "ASIA": (95, 48),
          "OCEANIA": (135, -26)}


def project(lon, lat, mx, my, mw, mh):
    px = mx + (lon + 170.0) / 360.0 * mw
    py = my + (78.0 - lat) / 133.0 * mh
    return px, py


# ---------------------------------------------------------------- build
def build(path):
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # Deterministic paper grain so the PNG carries real texture.
    rnd = random.Random(20261122)
    for _ in range(140000):
        gx = rnd.randint(0, W - 1)
        gy = rnd.randint(0, H - 1)
        v = rnd.randint(-7, 7)
        d.point((gx, gy), fill=(247 + v, 243 + v, 232 + v))

    # Masthead
    title = "THE SUNDAY GLOBE"
    tf = font(SERIF_B, 46)
    d.text(((W - d.textlength(title, font=tf)) / 2, 12), title, font=tf, fill=INK)
    d.line([M, 66, W - M, 66], fill=INK, width=2)
    d.line([M, 70, W - M, 70], fill=INK, width=1)
    date = "Sunday 22 November 2026"
    df = font(SERIF_B, 24)
    d.text(((W - d.textlength(date, font=df)) / 2, 76), date, font=df, fill=RED)
    sub = ("COP31 deadlocked in Antalya  |  A 6.9 quake shakes Peru  |  "
           "Iran strikes a US base in Kuwait")
    sf = font(SERIF, 13)
    d.text(((W - d.textlength(sub, font=sf)) / 2, 106), sub, font=sf, fill=INK)

    # Numbers strip: 6 cells, label above number, generous spacing.
    y0, y1 = 128, 172
    cell = CW / 6.0
    d.rectangle([M, y0, W - M, y1], outline=INK, width=1)
    for i, (num, label) in enumerate(STATS):
        cx = M + cell * i
        if i:
            d.line([cx, y0, cx, y1], fill=GREY, width=1)
        nf = font(SERIF_B, 21)
        lf = font(SANS_B, 9)
        d.text((cx + (cell - d.textlength(num, font=nf)) / 2, y0 + 4),
               num, font=nf, fill=INK)
        d.text((cx + (cell - d.textlength(label, font=lf)) / 2, y0 + 28),
               label, font=lf, fill=GREY)

    # Region bar: counts computed from the story data, never typed twice.
    counts = {r: 0 for r in REGIONS}
    for s in LEADS + SMALL:
        counts[s["region"]] += 1
    for _, r in BRIEFS:
        counts[r] += 1
    assert sum(counts.values()) == 35, counts
    y0, y1 = 178, 200
    bx = M
    bf = font(SANS_B, 9)
    for r in REGIONS:
        seg = CW * counts[r] / 35.0
        d.rectangle([bx, y0, bx + seg, y1], fill=REGION_COLOURS[r])
        label = "%s %d" % (r.upper(), counts[r])
        if d.textlength(label, font=bf) < seg - 6:
            d.text((bx + 5, y0 + 6), label, font=bf, fill=(255, 255, 255))
        bx += seg

    # Lead cards: 3 across.
    y0 = 208
    lead_w = (CW - 16) / 3.0
    lead_h = 158
    for i, s in enumerate(LEADS):
        x = M + i * (lead_w + 8)
        d.rectangle([x, y0, x + lead_w, y0 + lead_h], outline=INK, width=1)
        scene(d, s["scene"], x + 1, y0 + 1, lead_w - 2, 62)
        d.rectangle([x, y0 + 63, x + lead_w, y0 + 86], fill=RED)
        nf = font(SERIF_B, 11)
        d.text((x + 8, y0 + 67), "No. %d  %s" % (s["n"], s["region"].upper()),
               font=nf, fill=(255, 255, 255))
        draw_wrapped(d, x + 8, y0 + 90, s["head"], font(SERIF_B, 14),
                     lead_w - 16, INK, 2, 16)
        draw_wrapped(d, x + 8, y0 + 124, s["body"], font(SERIF, 11),
                     lead_w - 16, INK, 2, 13)

    # Small cards: 2 rows of 5.
    small_w = (CW - 32) / 5.0
    small_h = 128
    for row in range(2):
        y0 = 374 + row * (small_h + 8)
        for col in range(5):
            s = SMALL[row * 5 + col]
            x = M + col * (small_w + 8)
            d.rectangle([x, y0, x + small_w, y0 + small_h], outline=INK, width=1)
            scene(d, s["scene"], x + 1, y0 + 1, small_w - 2, 52)
            nf = font(SERIF_B, 9)
            d.text((x + 6, y0 + 55), "No. %d" % s["n"], font=nf, fill=RED)
            draw_wrapped(d, x + 6, y0 + 68, s["head"], font(SERIF_B, 11),
                         small_w - 12, INK, 2, 13)
            draw_wrapped(d, x + 6, y0 + 96, s["body"], font(SERIF, 9),
                         small_w - 12, INK, 3, 11)

    # World map with numbered pins matching the card numbers.
    my0, my1 = 644, 796
    d.rectangle([M, my0, W - M, my1], outline=INK, width=1)
    d.rectangle([M, my0, W - M, my0 + 18], fill=INK)
    mf = font(SERIF_B, 11)
    d.text((M + 8, my0 + 3), "WHERE IT HAPPENED: pins match the story numbers",
           font=mf, fill=(255, 255, 255))
    mx, mw = M + 6, CW - 12
    mtop, mh = my0 + 22, my1 - my0 - 26
    d.rectangle([mx, mtop, mx + mw, mtop + mh], fill=SEA)
    for name, pts in CONTINENTS.items():
        poly = [project(lon, lat, mx, mtop, mw, mh) for lon, lat in pts]
        d.polygon(poly, fill=LAND, outline=LAND_LINE)
    lf = font(SANS_B, 9)
    for name, (lon, lat) in LABELS.items():
        px, py = project(lon, lat, mx, mtop, mw, mh)
        d.text((px - d.textlength(name, font=lf) / 2, py), name, font=lf,
               fill=(110, 95, 70))
    pf = font(SANS_B, 10)
    for s in LEADS + SMALL:
        px, py = project(s["lon"], s["lat"], mx, mtop, mw, mh)
        dx, dy = s["off"]
        qx, qy = px + dx, py + dy
        if dx or dy:
            d.line([px, py, qx, qy], fill=RED, width=1)
            d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=RED)
        num = str(s["n"])
        d.ellipse([qx - 9, qy - 9, qx + 9, qy + 9], fill=RED,
                  outline=(255, 255, 255), width=1)
        d.text((qx - d.textlength(num, font=pf) / 2, qy - 7), num, font=pf,
               fill=(255, 255, 255))

    # Briefs: 22 one-liners in 2 columns of 11.
    by0 = 804
    bf = font(SERIF_B, 11)
    d.text((M, by0), "IN BRIEF: 22 more stories from the day", font=bf, fill=INK)
    d.line([M, by0 + 16, W - M, by0 + 16], fill=INK, width=1)
    brief_f = font(SERIF, 10)
    col_w = (CW - 16) / 2.0
    for i, (text, region) in enumerate(BRIEFS):
        col = i // 11
        row = i % 11
        x = M + col * (col_w + 16)
        y = by0 + 22 + row * 12
        line = "\u2022  " + text
        assert d.textlength(line, font=brief_f) <= col_w, "BRIEF TOO LONG: " + line
        d.text((x, y), line, font=brief_f, fill=INK)

    # Date check footer.
    fy0 = 962
    d.line([M, fy0, W - M, fy0], fill=INK, width=2)
    ff = font(SERIF_B, 10)
    fb = font(SERIF, 10)
    d.text((M, fy0 + 6), "DATE CHECK", font=ff, fill=RED)
    body = EXCLUDED.split(": ", 1)[1]
    draw_wrapped(d, M, fy0 + 22, body, fb, CW, INK, 2, 13)
    d.text((M, fy0 + 50), "35 stories  |  7 regions  |  13 illustrated  |  "
           "Sunday 22 November 2026", font=ff, fill=GREY)

    img.save(path, format="PNG", compress_level=6)
    return img


if __name__ == "__main__":
    import os
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")
    build(out)
    print("wrote", out)
