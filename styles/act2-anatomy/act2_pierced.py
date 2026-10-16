"""暗面三部曲 · 第二幕《机械解剖》· FIG. II《穿心》
一颗铆钉铁壳的心被一把剑斜着扎穿，背后张开天使羽翼，剑格上开着一朵玫瑰，
锈血从伤口渗出，几片羽毛在往下落。圣心图像 × 解剖图版。
只用三色：#161a24 底 / #9aa9ad 金属灰 / #401720 锈血。
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy import ndimage
import math, sys

import os
TEXT = os.environ.get("TEXT") == "1"   # 默认无字；TEXT=1 时加回图版文字与编号引线
SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 11
OUT = sys.argv[2] if len(sys.argv) > 2 else f"act2_pierced_s{SEED}.png"
rng = np.random.default_rng(SEED)
W, H = 1200, 1500
PX = 2; SS = 2
BG = np.array([0x16, 0x1a, 0x24]); GR = np.array([0x9a, 0xa9, 0xad]); RU = np.array([0x40, 0x17, 0x20])
FONT_LAT = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
FONT_CJK = "/workspace/tools/qhw-poster-fonts/NotoSansCJKsc-Bold.otf"
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

def mask_of(draw_fn):
    m = Image.new("L", (W, H), 0); draw_fn(ImageDraw.Draw(m)); return np.asarray(m, np.float32) / 255.0 > 0.5
def hatch(angle_deg, period, density):
    a = math.radians(angle_deg); u = xx * math.cos(a) + yy * math.sin(a)
    return (np.abs(((u / period) % 1.0) - 0.5) < 0.5 * np.clip(density, 0, 1)).astype(np.float32)

# 线稿层（超采样）
line = Image.new("L", (W * SS, H * SS), 0); dl = ImageDraw.Draw(line)
def P(p): return (p[0] * SS, p[1] * SS)
def poly(pts, val=255, w=2): dl.line([P(p) for p in pts], fill=val, width=max(1, int(w * SS)), joint="curve")
def closed(pts, val=255, w=2): poly(list(pts) + [pts[0]], val, w)

gray = np.zeros((H, W), np.float32)
occ = np.zeros((H, W), bool)          # 已被前景占住的区域（画后面的东西时避开）

# ---------- 心 ----------
CX, CY, SC = 600, 760, 19.0
def heart_pts(n=500, sc=SC):
    t = np.linspace(0, 2 * np.pi, n)
    x = 16 * np.sin(t) ** 3; y = -(13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t))
    return [(CX + sc * a, CY + sc * b) for a, b in zip(x, y)]
heart = mask_of(lambda d: d.polygon(heart_pts(), fill=255))
dist = ndimage.distance_transform_edt(heart).astype(np.float32); hgt = np.sqrt(dist / dist.max())
gy, gx = np.gradient(ndimage.gaussian_filter(hgt, 6))
nl = np.sqrt(gx ** 2 + gy ** 2 + 0.02 ** 2)
shade = np.where(heart, np.clip((-gx * -0.6 + -gy * -0.7 + 0.02 * 0.4) / nl, 0, 1) * 0.8 + 0.2 * hgt, 0)

# ---------- 剑：从右上斜插到左下 ----------
HILT = np.array([985., 250.]); TIP = np.array([250., 1235.])
ax = (TIP - HILT) / np.linalg.norm(TIP - HILT); nx_ = np.array([-ax[1], ax[0]])
def S(a, b): return tuple(HILT + ax * a + nx_ * b)      # 沿剑轴的坐标
Ltot = np.linalg.norm(TIP - HILT)
g0, g1 = 34, 165            # 握把
cg = 185                    # 剑格位置
blade = [S(cg, -24), S(Ltot - 90, -17), S(Ltot, 0), S(Ltot - 90, 17), S(cg, 24)]
guard = [S(cg - 14, -120), S(cg + 4, -128), S(cg + 14, -110), S(cg + 14, 110), S(cg + 4, 128), S(cg - 14, 120)]
grip = [S(g0, -15), S(g1, -13), S(g1, 13), S(g0, 15)]
bladem = mask_of(lambda d: d.polygon(blade, fill=255))
guardm = mask_of(lambda d: d.polygon(guard, fill=255))
gripm = mask_of(lambda d: d.polygon(grip, fill=255))
pomm = mask_of(lambda d: d.ellipse([S(14, 0)[0] - 26, S(14, 0)[1] - 26, S(14, 0)[0] + 26, S(14, 0)[1] + 26], fill=255))
sword_vis = (bladem & ~heart) | guardm | gripm | pomm

# ---------- 羽翼（在心后面） ----------
def feather(root, ang, Lf, wf, val, outline=True, region=None):
    pts = []
    for t in np.linspace(0, 1, 30):
        pts.append((t * Lf, wf * math.sin(math.pi * t ** 0.55) ** 0.7))
    for t in np.linspace(1, 0, 30):
        pts.append((t * Lf, -wf * 0.75 * math.sin(math.pi * t ** 0.55) ** 0.7))
    ca, sa = math.cos(ang), math.sin(ang)
    pts = [(root[0] + x * ca - y * sa, root[1] + x * sa + y * ca) for x, y in pts]
    m = mask_of(lambda d: d.polygon(pts, fill=255)) & ~occ
    return pts, m, (root, (root[0] + Lf * ca, root[1] + Lf * sa))
wing_fill = np.zeros((H, W), np.float32); wing_m = np.zeros((H, W), bool)
feathers_drawn = []
for side in (-1, 1):
    base = np.array([CX + side * 150, CY - 170])
    for row, (n, L0, wf, spread, val) in enumerate([(10, 360, 46, 1.2, 0.5), (8, 250, 42, 1.1, 0.68), (7, 160, 36, 0.95, 0.85)]):
        for k in range(n):
            t = k / (n - 1)
            ang0 = -math.pi / 2 - side * (0.15 + spread * t)       # 由上往外展开
            if side == 1: ang = ang0
            else: ang = ang0
            root = base + np.array([side * 30 * t, 18 * row + 30 * t])
            Lf = L0 * (1.0 - 0.35 * t) * (0.92 + 0.16 * rng.random())
            a = -math.pi / 2 + side * (0.25 + spread * t) * 1.0
            pts, m, quill = feather(root, a, Lf, wf, val)
            feathers_drawn.append((pts, quill, row))
            wing_fill = np.where(m & ~wing_m, val, wing_fill); wing_m |= m
# 羽毛内部：顺着各自方向的细排线 → 用统一斜线近似，亮度按层
wing_tex = hatch(70, 6, 0.25 + 0.35 * wing_fill) * wing_fill
gray = np.where(wing_m & ~heart & ~sword_vis, wing_tex * 0.9, gray)

# 心壳刻线
u = (xx * math.cos(0.5) + yy * math.sin(0.5)) + hgt * 40
h1 = (np.abs(((u / 7.0) % 1.0) - 0.5) < 0.18 * (0.3 + shade)).astype(np.float32)
v = (xx * math.cos(1.7) + yy * math.sin(1.7)) + hgt * 30
h2 = (np.abs(((v / 9.0) % 1.0) - 0.5) < 0.32 * np.clip(shade - 0.45, 0, 1)).astype(np.float32)
gray = np.where(heart, np.clip(h1 * (0.35 + 0.8 * shade) + h2 * 0.6, 0, 1), gray)
# 剑：刃面亮、中脊一条线，剑格/握把排线
gray = np.where(bladem & ~heart, 0.25 + 0.55 * hatch(-35, 4, 0.55), gray)
gray = np.where(guardm | pomm, hatch(20, 5, 0.6) * 0.95, gray)
gray = np.where(gripm, hatch(-60, 7, 0.45), gray)

# ---------- 线稿 ----------
for pts, quill, row in reversed(feathers_drawn):
    closed(pts, 210 - row * 10, 1.4); poly([quill[0], quill[1]], 190, 1)
dl.polygon([P(p) for p in heart_pts()], fill=0)
for poly_ in (blade, guard, grip):
    dl.polygon([P(p) for p in poly_], fill=0)
closed(heart_pts(), 255, 3)
for (x, y) in heart_pts(80, SC * 0.92):
    dl.ellipse([P((x - 3, y - 3)), P((x + 3, y + 3))], outline=255, width=SS)
# 剑轮廓（心里那段不画）
def poly_clip(pts, val, w, avoid):
    seg = []
    dense = []
    for i in range(len(pts) - 1):
        for t in np.linspace(0, 1, 40, endpoint=False):
            dense.append((pts[i][0] + (pts[i + 1][0] - pts[i][0]) * t, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * t))
    dense.append(pts[-1])
    for p in dense:
        inside = avoid[int(min(H - 1, max(0, p[1]))), int(min(W - 1, max(0, p[0])))]
        if inside:
            if len(seg) > 1: poly(seg, val, w)
            seg = []
        else: seg.append(p)
    if len(seg) > 1: poly(seg, val, w)
poly_clip(blade + [blade[0]], 255, 2.5, heart)
poly_clip([S(cg, 0), S(Ltot - 110, 0)], 255, 1.5, heart)          # 中脊
closed(guard, 255, 2.5); closed(grip, 255, 2)
for k in range(9):                                                 # 缠绳
    a = g0 + (g1 - g0) * (k + 0.5) / 9
    poly([S(a - 6, -14), S(a + 6, 14)], 255, 1.5)
pc = S(14, 0); dl.ellipse([P((pc[0] - 26, pc[1] - 26)), P((pc[0] + 26, pc[1] + 26))], outline=255, width=3 * SS)
dl.ellipse([P((pc[0] - 9, pc[1] - 9)), P((pc[0] + 9, pc[1] + 9))], outline=255, width=2 * SS)

# ---------- 玫瑰：开在剑格上，藤缠着剑刃 ----------
RX, RY = CX, CY - 235
for i in reversed(range(16)):
    t = i / 15; a = i * 2.39996
    r = 6 + 62 * t ** 0.85
    cx = RX + r * math.cos(a); cy = RY + r * math.sin(a) * 0.7
    sz = 18 + 40 * t
    pts = []
    for th in np.linspace(0, 2 * math.pi, 60):
        wob = 1 + 0.12 * math.sin(3 * th + a)
        x = sz * math.cos(th) * wob; y = sz * 0.65 * math.sin(th) * wob
        pts.append((cx + x * math.cos(a + 1.57) - y * math.sin(a + 1.57), cy + x * math.sin(a + 1.57) + y * math.cos(a + 1.57)))
    pm_ = mask_of(lambda d: d.polygon(pts, fill=255))
    gray = np.where(pm_, hatch(45, 5, 0.25 + 0.4 * (1 - t)) * 0.9, gray)
    dl.polygon([P(p) for p in pts], fill=0); closed(pts, 255, 1.6)
sw = [(RX + (2 + 1.6 * th) * math.cos(th), RY + (2 + 1.6 * th) * math.sin(th) * 0.7) for th in np.linspace(0, 5 * math.pi, 120)]
poly(sw, 255, 1.3)
# 花茎插进心口的凹处，两片叶子
stem = [(RX + 4 * math.sin(i * 0.3), RY + 50 + i * 2.2) for i in range(30)]
poly(stem, 255, 2.5)
for (lx0, ly0, la, Ll) in [(RX, RY + 70, -0.5, 80), (RX, RY + 95, math.pi + 0.45, 70)]:
    leaf = []
    for t in np.linspace(0, 1, 30): leaf.append((t * Ll, 20 * math.sin(math.pi * t)))
    for t in np.linspace(1, 0, 30): leaf.append((t * Ll, -14 * math.sin(math.pi * t)))
    leaf = [(lx0 + x * math.cos(la) - y * math.sin(la), ly0 + x * math.sin(la) + y * math.cos(la)) for x, y in leaf]
    dl.polygon([P(p) for p in leaf], fill=0); closed(leaf, 255, 1.6); poly([leaf[0], leaf[30]], 200, 1)
    lm = mask_of(lambda d: d.polygon(leaf, fill=255)); gray = np.where(lm, hatch(la * 57 + 30, 5, 0.35) * 0.8, gray)

# ---------- 落下的羽毛 ----------
for j in range(5):
    rx_ = rng.uniform(150, 1050); ry_ = rng.uniform(1000, 1220)
    if abs(rx_ - CX) < 200 and ry_ < 1150: rx_ += 330 * np.sign(rx_ - CX + 1)
    a = rng.uniform(-0.8, 0.8) + (math.pi / 2 if rng.random() < 0.5 else 0)
    Lf = rng.uniform(60, 95)
    pts = []
    for t in np.linspace(0, 1, 24): pts.append((t * Lf, 11 * math.sin(math.pi * t ** 0.8)))
    for t in np.linspace(1, 0, 24): pts.append((t * Lf, -9 * math.sin(math.pi * t ** 0.8)))
    pts = [(rx_ + x * math.cos(a) - y * math.sin(a), ry_ + x * math.sin(a) + y * math.cos(a)) for x, y in pts]
    fm = mask_of(lambda d: d.polygon(pts, fill=255))
    gray = np.where(fm, hatch(a * 57 + 60, 4, 0.4) * 0.8, gray)
    closed(pts, 230, 1.3); poly([pts[0], pts[24]], 200, 1)

# ---------- 图版框与图注 ----------
flat = ImageFont.truetype(FONT_LAT, 22 * SS); flat_s = ImageFont.truetype(FONT_LAT, 17 * SS)
fcjk = ImageFont.truetype(FONT_CJK, 19 * SS); fcjk_b = ImageFont.truetype(FONT_CJK, 26 * SS)
closed([(50, 50), (W - 50, 50), (W - 50, H - 50), (50, H - 50)], 220, 2)
closed([(62, 62), (W - 62, 62), (W - 62, H - 62), (62, H - 62)], 140, 1)
TEXT and dl.text(P((90, 80)), "TAB. II", font=flat, fill=255)
TEXT and dl.text(P((W - 330, 80)), "COR TRANSFIXUM", font=flat, fill=255)
labels = [(S(80, 0), (1090, 470), "1"), ((CX - 300, CY - 330), (110, 300), "2"),
          ((RX + 40, RY - 20), (760, 230), "3"), ((CX - 150, CY + 140), (110, 980), "4")]
for (a, b, n) in (labels if TEXT else []):
    poly([a, b], 200, 1); dl.ellipse([P((a[0] - 3, a[1] - 3)), P((a[0] + 3, a[1] + 3))], fill=255)
    TEXT and dl.text(P((b[0] - 8, b[1] - 30)), n, font=flat, fill=255)
legend = ["1. gladius — 剑", "2. alae — 羽翼", "3. rosa — 玫瑰", "4. vulnus — 伤口"]
for i, s in enumerate(legend):
    lat, cjk = s.split(" — "); x = 110 + i * 255; y = 1310
    TEXT and dl.text(P((x, y)), lat, font=flat_s, fill=220)
    w = dl.textlength(lat, font=flat_s) / SS
    TEXT and dl.text(P((x + w + 10, y - 3)), cjk, font=fcjk, fill=220)
TEXT and dl.text(P((W / 2 - 150, 1398)), "FIG. II", font=flat, fill=255)
TEXT and dl.text(P((W / 2 - 25, 1394)), "穿 心", font=fcjk_b, fill=255)
lines = np.asarray(line.resize((W, H), Image.LANCZOS), np.float32) / 255.0
gray = np.maximum(gray, lines)

# ---------- 锈血：从剑进出心脏的两处伤口渗出 ----------
rl = Image.new("L", (W, H), 0); dr = ImageDraw.Draw(rl)
# 找剑轴和心脏边界的交点
pts_axis = [S(s_, 0) for s_ in np.linspace(cg, Ltot, 800)]
inside = [heart[int(p[1]), int(p[0])] for p in pts_axis]
wounds = []
for i in range(1, len(inside)):
    if inside[i] != inside[i - 1]: wounds.append(pts_axis[i])
for (wx_, wy_) in wounds:
    dr.ellipse([wx_ - 26, wy_ - 18, wx_ + 26, wy_ + 18], fill=255)
    for k in range(6):
        x = wx_ + rng.uniform(-24, 24); y = wy_ + rng.uniform(0, 12)
        ln = rng.uniform(50, 230); wd = rng.uniform(2, 6); path = [(x, y)]
        for _ in range(int(ln / 6)):
            px_, py_ = path[-1]; path.append((px_ + rng.normal(0, 0.8), py_ + 6))
        dr.line(path, fill=235, width=int(wd))
        ex, ey = path[-1]; dr.ellipse([ex - wd, ey - wd * 0.6, ex + wd, ey + wd * 1.6], fill=255)
rust = np.asarray(rl.filter(ImageFilter.GaussianBlur(1.2)), np.float32) / 255.0
seep = ndimage.gaussian_filter(np.asarray(rl, np.float32) / 255.0, 18) * 2.2
rust = np.clip(rust + seep * heart, 0, 1)
# 剑刃沾血：心脏下方那截刃
bl_low = bladem & ~heart & (yy > CY)
rust = np.maximum(rust, bl_low * (0.5 + 0.4 * hatch(-35, 4, 0.5)) * np.clip((1100 - yy) / 300, 0.2, 1))

# ---------- 质感 + 抖动 ----------
gray = gray * (1 - 0.45 * ((yy % 4) < 1))
vig = np.clip(1 - 0.55 * (((xx / W - 0.5) ** 2 + (yy / H - 0.47) ** 2) * 2.2), 0, 1)
gray = np.clip(gray * vig + rng.normal(0, 0.02, (H, W)) * (gray > 0.05), 0, 1)
gray = np.maximum(gray, (rng.random((H, W)) < 0.0015) * 0.9)
rust = np.clip(rust * (1 - 0.3 * ((yy % 4) < 1)), 0, 1)
def bayer(n):
    m = np.array([[0, 2], [3, 1]])
    while m.shape[0] < n: m = np.block([[4 * m, 4 * m + 2], [4 * m + 3, 4 * m + 1]])
    return (m + 0.5) / (n * n)
B = bayer(8)
iy = (yy // PX * PX).astype(int); ix = (xx // PX * PX).astype(int)
th = B[((yy // PX) % 8).astype(int), ((xx // PX) % 8).astype(int)]
out = np.empty((H, W, 3), np.uint8); out[:] = BG
out[(gray[iy, ix] > th) | (lines > 0.45)] = GR
out[rust[iy, ix] > th] = RU
Image.fromarray(out).save(OUT)
print("ok", OUT)
