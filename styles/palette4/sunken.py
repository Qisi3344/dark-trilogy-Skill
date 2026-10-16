"""暗面三部曲 · 配色 4 · FIG. I《沉没》
被淹没了，但还活着，还在爱。
深水底的森林，水草像头发一样往上飘；一颗还在跳的心沉在最底下，
红色从心里一丝丝渗出来，在绿里散开。
参考：米莱斯《奥菲莉亚》，换成从水底往上看。
只用三色：#122619 墨绿底 / #215d40 苔绿 / #6b0e0e 暗血红。
by 绮思 & 扶光
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import math, sys

SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 4
rng = np.random.default_rng(SEED)
W, H = 1200, 1500
PX = 2
BG = np.array([0x12, 0x26, 0x19])
GR = np.array([0x21, 0x5d, 0x40])
RD = np.array([0x6b, 0x0e, 0x0e])

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)


def layer():
    return Image.new("L", (W, H), 0)


def to_f(img, blur=0):
    if blur:
        img = img.filter(ImageFilter.GaussianBlur(blur))
    return np.asarray(img, dtype=np.float32) / 255.0


def fbm(scale, octaves=4):
    out = np.zeros((H, W), np.float32); amp = 1.0; tot = 0
    for o in range(octaves):
        s = max(2, int(scale / (2 ** o)))
        g = rng.random((H // s + 2, W // s + 2)).astype(np.float32)
        im = Image.fromarray((g * 255).astype(np.uint8)).resize((W + 2 * s, H + 2 * s), Image.BICUBIC)
        out += amp * (np.asarray(im, np.float32)[s:s + H, s:s + W] / 255.0)
        tot += amp; amp *= 0.5
    return out / tot


green = np.zeros((H, W), np.float32)

# ---------- 1. 水面：很远很远的光，碎成波纹 ----------
SX = W * 0.55
surf = np.exp(-((xx - SX) ** 2) / (2 * 260 ** 2)) * np.clip(1 - yy / 520, 0, 1) ** 2
caust = fbm(50, 4)
caust = np.clip(1 - np.abs(caust - 0.5) * 9, 0, 1)        # 焦散的亮网
green += surf * (0.35 + 0.65 * caust)
# 几道斜下来的光柱，越往下越淡，到心那里已经没了
for k in range(5):
    ang = math.radians(rng.uniform(-14, 10))
    x0 = SX + rng.normal(0, 140)
    off = (xx - x0) - (yy) * math.tan(ang)
    wid = rng.uniform(18, 50)
    shaft = np.exp(-(off ** 2) / (2 * wid ** 2)) * np.clip(1 - yy / 1050, 0, 1) ** 1.6
    green += shaft * rng.uniform(0.25, 0.45)

# ---------- 2. 水草：像头发一样往上飘 ----------
kelp = layer(); dk = ImageDraw.Draw(kelp)
HX, HY = W * 0.5, H * 0.83                                 # 心的位置
for i in range(70):
    side = rng.choice([-1, 1])
    bx = HX + side * abs(rng.normal(0, 330)) if rng.random() < 0.8 else rng.uniform(0, W)
    by = H + 20
    top = rng.uniform(150, 900)
    amp = rng.uniform(15, 60); freq = rng.uniform(0.004, 0.012); ph = rng.uniform(0, 6.3)
    lean = rng.normal(0, 0.12)
    pts = []
    y = by
    while y > top:
        t = (by - y) / (by - top)
        x = bx + amp * t * math.sin(y * freq + ph) + lean * (by - y)
        pts.append((x, y)); y -= 8
    near = math.exp(-((bx - HX) ** 2) / (2 * 260 ** 2))
    val = int(70 + 150 * rng.random() * (0.4 + 0.6 * near))
    for j in range(1, len(pts)):
        t = j / len(pts)
        w = max(1, int((7 if rng.random() < 0.3 else 3) * (1 - t * 0.8)))
        dk.line([pts[j - 1], pts[j]], fill=int(val * (1 - 0.5 * t)), width=w)
kf = to_f(kelp, 0.7)
# 离水面越近越被光勾亮，底部埋在黑里
green += kf * np.clip(0.35 + 0.65 * (1 - yy / H) + surf, 0, 1) * 0.85

# ---------- 3. 气泡：从心里往上冒，越来越少 ----------
bub = layer(); db = ImageDraw.Draw(bub)
for _ in range(60):
    t = rng.random() ** 1.8
    bx = HX + rng.normal(0, 30 + 120 * t); byy = HY - 60 - t * 1100
    r = rng.uniform(2, 9) * (1 - 0.5 * t)
    db.ellipse([bx - r, byy - r, bx + r, byy + r], outline=230, width=2)
green += to_f(bub) * 0.8

# ---------- 4. 心：沉在最底下，还在跳 ----------
heart = layer(); dh = ImageDraw.Draw(heart)
S = 5.2
pts = []
for i in range(200):
    a = 2 * math.pi * i / 200
    x = 16 * math.sin(a) ** 3
    y = -(13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a))
    # 微微歪着，像是落地时倒了一下
    xr = x * math.cos(0.35) - y * math.sin(0.35)
    yr = x * math.sin(0.35) + y * math.cos(0.35)
    pts.append((HX + xr * S, HY + yr * S))
dh.polygon(pts, fill=255)
# 主动脉的断口
dh.line([(HX - 18, HY - 58), (HX - 30, HY - 105)], fill=255, width=16)
dh.line([(HX + 22, HY - 70), (HX + 48, HY - 108)], fill=255, width=11)
hf = to_f(heart)
hrim = np.clip(hf - to_f(heart.filter(ImageFilter.MinFilter(7))), 0, 1)
green += hrim * 0.6                                       # 苔绿勾边
# 心跳的脉冲：围着心的几圈涟漪
dr = np.hypot(xx - HX, yy - HY)
for k, rr in enumerate((120, 175, 245)):
    green += np.exp(-((dr - rr) ** 2) / 10.0) * (0.55 - k * 0.15) * (np.sin(np.arctan2(yy - HY, xx - HX) * 3 + k) > -0.3)

# ---------- 5. 红：从心里一丝丝渗出来，往上散 ----------
red = hf * (0.55 + 0.45 * fbm(25, 3))                     # 心本身
thr = layer(); dt = ImageDraw.Draw(thr)
for i in range(26):
    x, y = HX + rng.normal(0, 25), HY - rng.uniform(0, 30)
    vx, vy = rng.normal(0, 0.6), -1.0
    L = rng.uniform(120, 520)
    steps = int(L / 4)
    for j in range(steps):
        vx += rng.normal(0, 0.18) + 0.02 * math.sin(y * 0.02 + i)
        vx *= 0.96
        nx, ny = x + vx * 4, y + vy * 4
        dt.line([(x, y), (nx, ny)], fill=int(255 * (1 - j / steps) ** 1.4), width=2 if j < steps * 0.4 else 1)
        x, y = nx, ny
red = np.maximum(red, to_f(thr, 0.4) * 0.9)
# 心周围化开的一小团红雾
red += np.exp(-(dr ** 2) / (2 * 70 ** 2)) * 0.28
red = np.clip(red, 0, 1)

# ---------- 6. 颗粒 + 暗角 ----------
grain = rng.normal(0, 0.02, (H, W)).astype(np.float32)
vig = 1 - 0.85 * (((xx / W - 0.5) ** 2 + (yy / H - 0.5) ** 2) * 2.2)
green = np.clip(green * np.clip(vig, 0, 1) + grain * (green > 0.05), 0, 1)

# ---------- 7. 三色有序抖动 ----------
def bayer(n):
    m = np.array([[0, 2], [3, 1]])
    while m.shape[0] < n:
        m = np.block([[4 * m, 4 * m + 2], [4 * m + 3, 4 * m + 1]])
    return (m + 0.5) / (n * n)


B = bayer(8)
th = B[((yy // PX) % 8).astype(int), ((xx // PX) % 8).astype(int)]
iy = (yy // PX * PX).astype(int); ix = (xx // PX * PX).astype(int)
gb, rb = green[iy, ix], red[iy, ix]
out = np.empty((H, W, 3), np.uint8); out[:] = BG
out[gb > th] = GR
out[rb > th] = RD
Image.fromarray(out).save(f"sunken_s{SEED}.png")
print("ok", SEED, "黑占比 %.2f" % (1 - ((gb > th) | (rb > th)).mean()))
