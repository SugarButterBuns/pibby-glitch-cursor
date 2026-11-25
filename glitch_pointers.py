"""
Glitched versions of every other pointer, drawn in the same pixel style as the
original arrow (images/cursor/mouse (1..10).png) and broken up with the same
glitch effects and rhythm:

  * bands of 1-4 rows shoved 1-3 px sideways
  * bits of outline breaking off and floating above the shape (slivers / dashes)
  * 1 px whole-shape jitter
  * per-frame intensity copied from the arrow: frame 1 heavy, 6-7 nearly clean

Credits: based on the "Pibby Apocalypse Cursor Recreation Script" by jarekboho
(https://gamebanana.com/tools/15314). Cursor art from Pibby: Apocalypse by the Pibby: Apocalypse
Team (https://gamebanana.com/wips/73842), licensed CC BY-NC 4.0. Full list: CREDITS.md.

Everything is deterministic (fixed seeds), so rebuilding gives identical files.
"""
import math
import random

from PIL import Image

# Palette sampled from the original arrow frames
OUTLINE = (19, 28, 27, 255)
FILL = (180, 191, 203, 255)
WHITE = (255, 255, 255, 255)
MID = (112, 122, 128, 255)
DARK = (66, 73, 73, 255)
SHADOW = (18, 28, 26, 126)
SHADOW_SOFT = (20, 30, 25, 51)
CHARS = {"f": FILL, "w": WHITE, "m": MID, "d": DARK, "k": OUTLINE}

CANVAS = 32
# Glitch intensity per frame, read off the original arrow animation.
RHYTHM = [3, 1, 1, 2, 2, 0, 0, 2, 2, 1]


# ------------------------------------------------------------------ drawing ---
def render(lines):
    """ASCII art -> RGBA sprite with outline, shading and drop shadow.
    '#' = auto-shaded fill, f/w/m/d/k = fixed palette colour, '.'/' ' = empty."""
    h, w = len(lines), max(len(l) for l in lines)
    cells = {(x, y): c for y, l in enumerate(lines) for x, c in enumerate(l) if c not in ". "}
    img = Image.new("RGBA", (w + 4, h + 4), (0, 0, 0, 0))
    px = img.load()
    inside = set(cells)
    out = lambda p: p not in inside
    for (x, y), c in cells.items():
        if c == "#":
            L, R, T, B = out((x - 1, y)), out((x + 1, y)), out((x, y - 1)), out((x, y + 1))
            col = FILL if (L and R) or (T and B) else DARK if B else MID if L else WHITE if (T or R) else FILL
        else:
            col = CHARS[c]
        px[x + 1, y + 1] = col
    outline = {(x + dx, y + dy) for x, y in inside for dx in (-1, 0, 1) for dy in (-1, 0, 1)} - inside
    for x, y in outline:
        px[x + 1, y + 1] = OUTLINE
    solid = inside | outline
    for x, y in solid:  # soft shadow down-right, like the arrow's
        for (dx, dy), col in (((1, 1), SHADOW), ((2, 2), SHADOW_SOFT)):
            q = (x + dx, y + dy)
            if q not in solid and px[q[0] + 1, q[1] + 1][3] < col[3]:
                px[q[0] + 1, q[1] + 1] = col
    return img


def grid(w, h, fn):
    return ["".join(fn(x, y) or "." for x in range(w)) for y in range(h)]


def ns_arrow(n=21, head=5):
    c = 2 + head - 1
    def f(x, y):
        dx = abs(x - c)
        if y < head and dx <= y: return "#"
        if y >= n - head and dx <= n - 1 - y: return "#"
        if dx == 0: return "#"
    return grid(2 * c + 1, n, f)


def diag_arrow(n=17, head=6):
    def f(x, y):
        if x + y <= head: return "#"
        if (n - 1 - x) + (n - 1 - y) <= head: return "#"
        if x == y: return "#"
    return grid(n, n, f)


def move_arrows(n=23, head=4):
    c = n // 2
    def f(x, y):
        dx, dy = abs(x - c), abs(y - c)
        if (y < head and dx <= y) or (n - 1 - y < head and dx <= n - 1 - y): return "#"
        if (x < head and dy <= x) or (n - 1 - x < head and dy <= n - 1 - x): return "#"
        if dx == 0 or dy == 0: return "#"
    return grid(n, n, f)


def crosshair(n=21, gap=2):
    c = n // 2
    return grid(n, n, lambda x, y: "#" if (x == c and abs(y - c) > gap) or (y == c and abs(x - c) > gap) else None)


def no_sign(n=21):
    c = (n - 1) / 2
    def f(x, y):
        d = math.hypot(x - c, y - c)
        if 6.6 <= d <= 9.4: return "#"
        if d < 7 and abs((x - c) - (y - c)) <= 1.0: return "#"
    return grid(n, n, f)


def pen(n=20):
    def f(x, y):
        t = ((x - 1) + (n - 2 - y)) / 2          # distance along the pen from the tip
        u = abs((x - 1) - (n - 2 - y)) / 2       # distance across the pen
        if t < 0 or t > n - 3: return None
        if t <= 1.5 and u <= t * 0.5: return "d"        # graphite tip
        if t <= 4 and u <= min(1.5, t * 0.5): return "w"  # sharpened wood
        if t > n - 6 and u <= 1.5: return "m"          # eraser end
        if u <= 1.5: return "#"
    return grid(n, n, f)


IBEAM = [
    "###.###",
    "...#...",
    "...#...",
    "...#...",
    "...#...",
    "...#...",
    "...#...",
    "...#...",
    "...#...",
    "...#...",
    "...#...",
    "...#...",
    "...#...",
    "...#...",
    "...#...",
    "...#...",
    "...#...",
    "###.###",
]

HAND = [
    "....##.........",
    "...####........",
    "...####........",
    "...####........",
    "...####........",
    "...####........",
    "...####d###....",
    "...####d####...",
    "...####d####d##",
    ".##.###d####d##",
    "####.##########",
    "#####.#########",
    ".##############",
    ".##############",
    "..#############",
    "..############.",
    "...###########.",
    "...##########..",
    "....#########..",
    "....#########..",
]

HOURGLASS = [
    "mmmmmmmmmmmmm",
    "mmmmmmmmmmmmm",
    ".###########.",
    ".###########.",
    "..##ddddd##..",
    "...##ddd##...",
    "....##d##....",
    ".....###.....",
    "......#......",
    ".....###.....",
    "....##d##....",
    "...##ddd##...",
    "..##ddddd##..",
    ".##ddddddd##.",
    ".###########.",
    "mmmmmmmmmmmmm",
    "mmmmmmmmmmmmm",
]

SMALL_HOURGLASS = [
    "mmmmmmmmm",
    ".#######.",
    ".##ddd##.",
    "..##d##..",
    "...###...",
    "....#....",
    "...###...",
    "..##d##..",
    ".##ddd##.",
    ".#ddddd#.",
    "mmmmmmmmm",
]

QUESTION = [
    ".#####.",
    "##...##",
    "##...##",
    "....##.",
    "...##..",
    "..##...",
    "..##...",
    ".......",
    "..##...",
    "..##...",
]

PIN = [
    "..#####..",
    ".#######.",
    "####d####",
    "###ddd###",
    "####d####",
    ".#######.",
    ".#######.",
    "..#####..",
    "...###...",
    "...###...",
    "....#....",
]

PERSON = [
    "...###...",
    "..#####..",
    "..#####..",
    "..#####..",
    "...###...",
    ".........",
    ".#######.",
    "#########",
    "#########",
    "#########",
]

UP_ARROW = grid(13, 21, lambda x, y: "#" if (y < 7 and abs(x - 6) <= y) or (y >= 7 and abs(x - 6) <= 1) else None)


# ------------------------------------------------------------------- glitch ---
def glitch(img, frame, rng, keep=None):
    """Apply the arrow's glitch vocabulary to one frame. `keep` = rows/cols box
    that must stay put (unused for now, everything is allowed to break)."""
    level = RHYTHM[frame]
    w, h = img.size
    src = img.load()
    out = img.copy()
    o = out.load()
    box = img.getbbox() or (0, 0, w, h)
    x0, y0, x1, y1 = box

    def shift_rows(top, height, dx):
        for y in range(top, min(top + height, h)):
            row = [src[x, y] for x in range(w)]
            for x in range(w):
                sx = x - dx
                o[x, y] = row[sx] if 0 <= sx < w else (0, 0, 0, 0)

    # whole-shape 1px jitter on quiet frames (arrow frames 6->7 do this)
    if level == 0 and frame % 2:
        out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        out.paste(img, (1, 0))
        return out

    bands = {1: 1, 2: 2, 3: 3}.get(level, 0)
    for _ in range(bands):
        top = rng.randrange(y0, max(y0 + 1, y1 - 1))
        height = rng.randint(1, 4 if level < 3 else 5)
        dx = rng.choice([-1, 1]) * rng.randint(1, 2 if level < 3 else 3)
        shift_rows(top, height, dx)
        src = out.copy().load()

    if level >= 2:
        # a sliver of the top outline breaks off and floats above
        ty = y0 + rng.randint(0, 2)
        seg = [x for x in range(w) if src[x, ty][3] == 255]
        if seg:
            sx = rng.choice(seg)
            ln = rng.randint(2, 4)
            lift = rng.randint(2, 3)
            for x in range(sx, min(sx + ln, w)):
                y = ty - lift
                if 0 <= y < h and src[x, ty][3]:
                    o[x, y] = OUTLINE
        # and a short dash off to the side, like frames 8-10
        if rng.random() < 0.7:
            dy = rng.randint(max(0, y0 - 2), min(h - 1, y0 + (y1 - y0) // 3))
            dx0 = rng.randint(x0 + (x1 - x0) // 3, max(x0 + (x1 - x0) // 3 + 1, min(w - 5, x1)))
            for x in range(dx0, min(dx0 + rng.randint(3, 5), w)):
                if o[x, dy][3] == 0:
                    o[x, dy] = OUTLINE
    return out


def place(sprite, canvas=CANVAS, at=None):
    img = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
    if at is None:
        at = ((canvas - sprite.width) // 2, (canvas - sprite.height) // 2)
    img.alpha_composite(sprite, at)
    return img, at


def standalone(lines, hot_in_art, seed):
    """Self-contained shape centred on a 32x32 canvas, glitched per frame."""
    base, (ax, ay) = place(render(lines))
    rng = random.Random(seed)
    frames = [glitch(base, i, rng) for i in range(10)]
    return frames, (ax + 1 + hot_in_art[0], ay + 1 + hot_in_art[1])


def with_arrow(arrow_frames, lines, at, seed):
    """Original arrow frame (untouched) + a glitched badge, in sync with it."""
    badge, _ = place(render(lines), at=at)
    rng = random.Random(seed)
    frames = []
    for i, a in enumerate(arrow_frames):
        img = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
        img.paste(a, (0, 0))
        img.alpha_composite(glitch(badge, i, rng))
        frames.append(img)
    return frames, (0, 0)


def build(arrow_frames):
    """Return {windows_role: (frames, hotspot)} for every pointer except Arrow."""
    ns, diag, mv = ns_arrow(), diag_arrow(), move_arrows()
    ns_c = (len(ns[0]) // 2, len(ns) // 2)
    we = ["".join(r[y] for r in ns) for y in range(len(ns[0]))]  # transpose
    nesw = [r[::-1] for r in diag]
    return {
        "Help":        with_arrow(arrow_frames, QUESTION, (14, 1), 101),
        "AppStarting": with_arrow(arrow_frames, SMALL_HOURGLASS, (13, 0), 102),
        "Wait":        standalone(HOURGLASS, (6, 8), 103),
        "Crosshair":   standalone(crosshair(), (10, 10), 104),
        "IBeam":       standalone(IBEAM, (3, 9), 105),
        "NWPen":       standalone(pen(), (1, 18), 106),
        "No":          standalone(no_sign(), (10, 10), 107),
        "SizeNS":      standalone(ns, ns_c, 108),
        "SizeWE":      standalone(we, (ns_c[1], ns_c[0]), 109),
        "SizeNWSE":    standalone(diag, (8, 8), 110),
        "SizeNESW":    standalone(nesw, (8, 8), 111),
        "SizeAll":     standalone(mv, (11, 11), 112),
        "UpArrow":     standalone(UP_ARROW, (6, 0), 113),
        "Hand":        standalone(HAND, (4, 0), 114),
        "Pin":         with_arrow(arrow_frames, PIN, (13, 0), 115),
        "Person":      with_arrow(arrow_frames, PERSON, (13, 0), 116),
    }
