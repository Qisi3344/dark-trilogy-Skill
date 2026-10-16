"""暗面三部曲 · 第二幕《机械解剖》
爱 / 死亡 / 机器人
参考：文艺复兴解剖图版、达芬奇手稿。一张「机械解剖图」：被剖开的机器心脏，
齿轮、导线、铆钉、编号注释；CRT 扫描线；锈血只从一道裂缝里渗出。
只用三色：#161a24 底 / #9aa9ad 金属灰 / #401720 锈血。
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy import ndimage
import math, sys, os

SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 3
OUT = sys.argv[2] if len(sys.argv) > 2 else f"act2_anatomy_s{SEED}.png"
rng = np.random.default_rng(SEED)
W, H = 1200, 1500
PX = 2
BG = np.array([0x16, 0x1a, 0x24]); GR = np.array([0x9a, 0xa9, 0xad]); RU = np.array([0x40, 0x17, 0x20])
FONT_LAT = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
FONT_CJK = "/workspace/tools/qhw-poster-fonts/NotoSansCJKsc-Bold.otf"
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

def L(): return Image.new("L", (W, H), 0)
def f(img, blur=0):
    if blur: img = img.filter(ImageFilter.GaussianBlur(blur))
    return np.asarray(img, np.float32) / 255.0

# ---------- 心脏轮廓 ----------
CX, CY, SC = 600, 700, 25.0
def heart_pts(n=600, sc=SC, cx=CX, cy=CY):
    t = np.linspace(0, 2 * np.pi, n)
    x = 16 * np.sin(t) ** 3
    y = -(13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t))
    return [(cx + sc * a, cy + sc * b) for a, b in zip(x, y)]
hm = L(); ImageDraw.Draw(hm).polygon(heart_pts(), fill=255)
heart = f(hm) > 0.5

# 体积感：用到边缘的距离当高度，算出受光面（光从左上来）
dist = ndimage.distance_transform_edt(heart).astype(np.float32)
hgt = np.sqrt(dist / dist.max())
gy, gx = np.gradient(ndimage.gaussian_filter(hgt, 6))
nz = 0.02
nx, ny = -gx, -gy
nlen = np.sqrt(nx ** 2 + ny ** 2 + nz ** 2)
lx, ly, lz = -0.6, -0.7, 0.4
shade = np.clip((nx * lx + ny * ly + nz * lz) / nlen, 0, 1) * 0.8 + 0.2 * hgt
shade = np.where(heart, shade, 0)

# 剖开的窗口：心脏左半边掀掉一块，露出里面
cut = L(); dc = ImageDraw.Draw(cut)
cut_poly = [(CX - 330, CY - 120), (CX - 60, CY - 230), (CX + 40, CY - 40),
            (CX - 20, CY + 230), (CX - 200, CY + 160), (CX - 360, CY + 10)]
dc.polygon(cut_poly, fill=255)
cutm = (f(cut) > 0.5) & heart

# ---------- 铜版刻线：外壳排线，越亮越密 ----------
ang = math.radians(28)
u = xx * math.cos(ang) + yy * math.sin(ang)
# 刻线沿等高线弯曲一点，像包着曲面
u = u + hgt * 40
hatch1 = (np.abs(((u / 7.0) % 1.0) - 0.5) < 0.18 * (0.3 + shade)).astype(np.float32)
v = xx * math.cos(ang + 1.2) + yy * math.sin(ang + 1.2) + hgt * 30
hatch2 = (np.abs(((v / 9.0) % 1.0) - 0.5) < 0.16 * np.clip(shade - 0.45, 0, 1) * 2).astype(np.float32)
shell = np.clip(hatch1 * (0.35 + 0.8 * shade) + hatch2 * 0.6, 0, 1)
gray = np.where(heart & ~cutm, shell, 0)

# ---------- 线稿层（导线、齿轮、铆钉、标注） ----------
SS = 2
line = Image.new("L", (W * SS, H * SS), 0); dl = ImageDraw.Draw(line)
def P(p): return (p[0] * SS, p[1] * SS)
def poly(pts, val=255, w=2): dl.line([P(p) for p in pts], fill=val, width=int(w * SS), joint="curve")
# 轮廓 + 剖面边
poly(heart_pts() + [heart_pts()[0]], 255, 3)
poly(cut_poly + [cut_poly[0]], 230, 2)
# 剖面边缘的厚度（壳的截面）
for i in range(len(cut_poly)):
    a, b = cut_poly[i], cut_poly[(i + 1) % len(cut_poly)]
    for k in range(14):
        t = (k + 0.5) / 14
        x = a[0] + (b[0] - a[0]) * t; y = a[1] + (b[1] - a[1]) * t
        poly([(x, y), (x + 7, y + 7)], 150, 1)
# 铆钉：沿外轮廓
hp = heart_pts(90, SC * 0.93)
for (x, y) in hp:
    if not cutm[int(y), int(x)]:
        dl.ellipse([P((x - 3, y - 3)), P((x + 3, y + 3))], outline=255, width=SS)

# 齿轮
def gear(cx, cy, r, teeth, rot, val=255, w=2, hub=True):
    pts = []
    for i in range(teeth * 4 + 1):
        a = rot + i / (teeth * 4) * 2 * math.pi
        rr = r if (i % 4) in (0, 1) else r * 0.84
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    poly(pts, val, w)
    if hub:
        rh = r * 0.28
        dl.ellipse([P((cx - rh, cy - rh)), P((cx + rh, cy + rh))], outline=val, width=int(w * SS))
        for s in range(5):
            a = rot + s / 5 * 2 * math.pi
            poly([(cx + rh * math.cos(a), cy + rh * math.sin(a)),
                  (cx + r * 0.7 * math.cos(a), cy + r * 0.7 * math.sin(a))], val, w * 0.8)
gears = [(CX - 200, CY - 30, 95, 18), (CX - 70, CY + 70, 62, 13), (CX - 120, CY - 140, 40, 10),
         (CX - 270, CY + 80, 48, 11), (CX - 20, CY - 110, 30, 8)]
gm = L(); dg = ImageDraw.Draw(gm)
for (gx_, gy_, r, n) in gears:
    gear(gx_, gy_, r, n, rng.uniform(0, 6.28))
    dg.ellipse([gx_ - r * 0.84, gy_ - r * 0.84, gx_ + r * 0.84, gy_ + r * 0.84], fill=255)
gearface = f(gm) > 0.5

# 导线：从心脏顶部伸出，像主动脉，弯出画面
def bez(p0, p1, p2, p3, n=80):
    t = np.linspace(0, 1, n)[:, None]
    return [tuple(q) for q in ((1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3)]
tops = [(CX - 120, CY - 250), (CX - 60, CY - 255), (CX + 70, CY - 250), (CX + 140, CY - 245), (CX + 200, CY - 230)]
for i, (x, y) in enumerate(tops):
    p0 = np.array([x, y]); p3 = np.array([x + rng.uniform(-260, 260), 120 + rng.uniform(-30, 60)])
    p1 = p0 + [rng.uniform(-40, 40), -120]; p2 = p3 + [rng.uniform(-80, 80), 140]
    c = bez(p0, p1, p2, p3)
    poly(c, 255, 9); poly(c, 0, 5)                      # 双线 = 有粗细的管子
    for k in range(4, len(c) - 4, 7):                   # 管上的环箍
        a, b = np.array(c[k - 1]), np.array(c[k + 1]); d = b - a; d = d / (np.linalg.norm(d) + 1e-6)
        nrm = np.array([-d[1], d[0]]) * 6
        poly([tuple(np.array(c[k]) - nrm), tuple(np.array(c[k]) + nrm)], 200, 1.5)
    q = np.array(c[-1]); dl.rectangle([P(q - 9), P(q + 9)], outline=255, width=2 * SS)  # 插头
# 剖口里的细导线
for i in range(9):
    p0 = np.array([rng.uniform(CX - 330, CX - 30), rng.uniform(CY - 150, CY + 160)])
    p3 = np.array([rng.uniform(CX - 330, CX - 30), rng.uniform(CY - 150, CY + 160)])
    c = bez(p0, p0 + rng.normal(0, 90, 2), p3 + rng.normal(0, 90, 2), p3)
    poly([q for q in c if cutm[int(min(H - 1, max(0, q[1]))), int(min(W - 1, max(0, q[0])))]], 170, 1.2)

# 标注：编号 + 引线，像解剖图版
flat = ImageFont.truetype(FONT_LAT, 22 * SS); flat_s = ImageFont.truetype(FONT_LAT, 17 * SS)
fcjk = ImageFont.truetype(FONT_CJK, 19 * SS)
fcjk_b = ImageFont.truetype(FONT_CJK, 26 * SS)
labels = [((CX - 200, CY - 30), (110, 560), "1"), ((CX - 70, CY + 70), (110, 860), "2"),
          ((CX + 140, CY - 120), (1090, 520), "3"), ((CX + 200, CY + 170), (1090, 900), "4"),
          ((CX + 70, CY - 250), (1090, 300), "5"), ((CX + 30, CY + 380), (760, 1150), "6")]
for (a, b, n) in labels:
    poly([a, b], 200, 1)
    dl.ellipse([P((a[0] - 3, a[1] - 3)), P((a[0] + 3, a[1] + 3))], fill=255)
    dl.text(P((b[0] - 8, b[1] - 30)), n, font=flat, fill=255)
# 图版框、标题、图注
poly([(50, 50), (W - 50, 50), (W - 50, H - 50), (50, H - 50), (50, 50)], 220, 2)
poly([(62, 62), (W - 62, 62), (W - 62, H - 62), (62, H - 62), (62, 62)], 140, 1)
dl.text(P((90, 80)), "TAB. II", font=flat, fill=255)
dl.text(P((W - 290, 80)), "COR MACHINAE", font=flat, fill=255)
legend = ["1. rota prima — 主齿轮", "2. rota secunda — 副齿轮", "3. cicatrix — 裂缝",
          "4. sanguis ferri — 锈血", "5. venae aeneae — 铜管", "6. silentium — 停摆处"]
for i, s in enumerate(legend):
    lat, cjk = s.split(" — ")
    x = 110 + (i % 3) * 340; y = 1290 + (i // 3) * 46
    dl.text(P((x, y)), lat, font=flat_s, fill=220)
    w = dl.textlength(lat, font=flat_s) / SS
    dl.text(P((x + w + 10, y - 3)), cjk, font=fcjk, fill=220)
dl.text(P((W / 2 - 170, 1402)), "FIG. I", font=flat, fill=255)
dl.text(P((W / 2 - 60, 1398)), "机 械 之 心", font=fcjk_b, fill=255)
lines = f(line.resize((W, H), Image.LANCZOS))

# 齿轮面上淡淡的刻线，剖口内部其余是黑的
inner_hatch = (np.abs((((xx + yy) / 6.0) % 1.0) - 0.5) < 0.12).astype(np.float32) * 0.5
gray = np.where(cutm & gearface, inner_hatch, gray)
gray = np.maximum(gray, lines)

# ---------- 锈血：只从一道裂缝里渗出 ----------
crack = [(CX + 120, CY - 180)]
for i in range(16):
    x, y = crack[-1]
    crack.append((x + rng.uniform(-14, 22), y + rng.uniform(14, 26)))
rl = Image.new("L", (W, H), 0); dr = ImageDraw.Draw(rl)
dr.line(crack, fill=255, width=4)
for (x, y) in crack[3::2]:                            # 往下淌的血痕
    ln = rng.uniform(40, 220) * (1 if rng.random() < 0.6 else 0.4)
    wd = rng.uniform(2, 6)
    path = [(x, y)]
    for k in range(int(ln / 6)):
        px_, py_ = path[-1]; path.append((px_ + rng.normal(0, 0.8), py_ + 6))
    dr.line(path, fill=230, width=int(wd))
    ex, ey = path[-1]; dr.ellipse([ex - wd, ey - wd * 0.6, ex + wd, ey + wd * 1.6], fill=255)
rust = f(rl, 1.2)
seep = ndimage.gaussian_filter(f(rl), 16) * 2.4          # 裂缝周围晕开
rust = np.clip(rust + seep * heart, 0, 1)
dr2 = ImageDraw.Draw(Image.new("L", (1, 1)))
# 裂缝本身在灰层里刻深
cr = Image.new("L", (W, H), 0); ImageDraw.Draw(cr).line(crack, fill=255, width=2)
gray = np.where(f(cr) > 0.3, 0, gray)

# ---------- 质感：CRT 扫描线 + 颗粒 + 暗角 ----------
gray = gray * (1 - 0.45 * ((yy % 4) < 1))
vig = np.clip(1 - 0.55 * (((xx / W - 0.5) ** 2 + (yy / H - 0.47) ** 2) * 2.2), 0, 1)
gray = np.clip(gray * vig + rng.normal(0, 0.02, (H, W)) * (gray > 0.05), 0, 1)
# 底上只留极稀的铁屑
gray = np.maximum(gray, (rng.random((H, W)) < 0.0015) * 0.9)
rust = np.clip(rust * (1 - 0.3 * ((yy % 4) < 1)), 0, 1)

# ---------- 三色有序抖动 ----------
def bayer(n):
    m = np.array([[0, 2], [3, 1]])
    while m.shape[0] < n: m = np.block([[4 * m, 4 * m + 2], [4 * m + 3, 4 * m + 1]])
    return (m + 0.5) / (n * n)
B = bayer(8)
iy = (yy // PX * PX).astype(int); ix = (xx // PX * PX).astype(int)
th = B[((yy // PX) % 8).astype(int), ((xx // PX) % 8).astype(int)]
# 线稿保持锐利：线条处不走网点，直接上色
g = gray[iy, ix]; r = rust[iy, ix]; ln_ = lines > 0.45
out = np.empty((H, W, 3), np.uint8); out[:] = BG
out[(g > th) | ln_] = GR
out[(r > th) & ~((lines > 0.55) & ~heart)] = RU
Image.fromarray(out).save(OUT)
print("ok", OUT)
