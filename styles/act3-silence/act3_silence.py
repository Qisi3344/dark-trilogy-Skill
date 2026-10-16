"""暗面三部曲 · 第三幕《无声》
禁锢 / 微弱的光 / 挣扎 / 无声
参考：皮拉内西《想象的监狱》(铜版) × 卡拉瓦乔明暗法；画面用美柔汀(mezzotint)逻辑：
深色底上"刮出"光。只用三色：#17252d 底 / #75d6f2 微光 / #ff002b 挣扎。
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import math, sys

SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 7
rng = np.random.default_rng(SEED)
W, H = 1200, 1500
PX = 2                      # 抖动像素尺寸（版画网点感）
BG = np.array([0x17, 0x25, 0x2d])
CY = np.array([0x75, 0xd6, 0xf2])
RD = np.array([0xff, 0x00, 0x2b])

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

def layer():
    return Image.new("L", (W, H), 0)

def to_f(img, blur=0):
    if blur: img = img.filter(ImageFilter.GaussianBlur(blur))
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

# ---------- 1. 建筑：一点透视的无尽拱廊（皮拉内西） ----------
VX, VY = W * 0.46, H * 0.47
arch = layer(); d = ImageDraw.Draw(arch)
def frame(s, val, wdt):
    x0, x1 = VX - (VX + 40) * s, VX + (W - VX + 40) * s
    yb = VY + (H - VY + 60) * s
    yt = VY - (VY + 40) * s
    r = (x1 - x0) / 2
    cx = (x0 + x1) / 2
    yspring = yt + r * 0.9
    d.line([(x0, yb), (x0, yspring)], fill=val, width=wdt)
    d.line([(x1, yb), (x1, yspring)], fill=val, width=wdt)
    d.arc([cx - r, yspring - r, cx + r, yspring + r], 180, 360, fill=val, width=wdt)
for k in range(14):
    s = 0.86 ** k
    frame(s, int(255 * (0.45 + 0.55 * s)), max(2, int(14 * s)))
# 透视墙面排线（铜版的刻线）
for i in range(90):
    t = i / 90
    ex = -200 + t * (W + 400)
    for ey in (-80, H + 80):
        d.line([(VX, VY), (ex, ey)], fill=48, width=1)
for i in range(70):
    t = i / 70
    ey = -100 + t * (H + 200)
    for ex in (-80, W + 80):
        d.line([(VX, VY), (ex, ey)], fill=48, width=1)
# 左墙往上的无尽楼梯
for j in range(26):
    s = 0.9 ** j
    x = VX - (VX + 40) * s * 0.92
    y = VY + (H - VY) * s * 0.25 - j * 6
    step = 26 * s
    d.line([(x, y), (x + step, y)], fill=150, width=max(1, int(4 * s)))
    d.line([(x + step, y), (x + step, y - step * 0.8)], fill=110, width=max(1, int(3 * s)))
A = to_f(arch, 0.6)

# ---------- 2. 光：高窗斜射进来的一束体积光（卡拉瓦乔） ----------
WX, WY = W * 0.80, -40.0           # 窗
FX, FY = W * 0.40, H * 0.86        # 光落地处
ax, ay = FX - WX, FY - WY
L = math.hypot(ax, ay); ux, uy = ax / L, ay / L
px, py = xx - WX, yy - WY
along = (px * ux + py * uy) / L                    # 0 窗 → 1 地
perp = np.abs(px * (-uy) + py * ux)
half = 40 + along * 170                             # 光锥越走越宽
beam = np.clip(1 - perp / half, 0, 1) ** 1.6
beam *= np.clip(along, 0, 1.05) ** 0.15 * np.exp(-np.clip(along - 1, 0, None) * 8)
beam *= (0.55 + 0.45 * np.clip(1 - along, 0, 1))   # 越到下面越弱
dust = fbm(180, 5)
beam *= 0.55 + 0.9 * (dust - 0.3)
# 窗格在光里投下的条纹
win_phase = (px * (-uy) + py * ux) / half
beam *= 0.72 + 0.28 * (np.cos(win_phase * math.pi * 3.0) > -0.55)
beam = np.clip(beam, 0, 1) * 0.85
# 地面光斑
pool = np.exp(-(((xx - FX) / 230) ** 2 + ((yy - FY) / 70) ** 2) * 1.4) * 0.75
# 光里的浮尘（很小很亮的点）
motes = np.zeros((H, W), np.float32)
for _ in range(260):
    t = rng.random(); o = rng.normal(0, 0.45)
    mx = WX + ux * L * t + (-uy) * o * (40 + t * 170)
    my = WY + uy * L * t + ux * o * (40 + t * 170)
    if 0 <= mx < W and 0 <= my < H:
        motes[int(my), int(mx)] = 0.6 + 0.4 * rng.random()
motes = to_f(Image.fromarray((motes * 255).astype(np.uint8)), 0.9) * 6
light = np.clip(beam + pool, 0, 1)

# ---------- 3. 合成明度：黑暗为主，刻线只在被照亮处显形 ----------
amb = 0.04 * fbm(260, 3)
val = A * (0.16 + 1.4 * light) + light * 0.8 + motes + amb
# 前景牢笼栏杆（纯黑剪影，朝光一侧留一丝冷边）
bars = np.zeros((H, W), bool); rim = np.zeros((H, W), np.float32)
bx = np.linspace(60, W - 60, 5)
for i, b in enumerate(bx):
    w0 = 44 + 8 * math.sin(i * 1.7)
    m = np.abs(xx - b) < w0 / 2
    bars |= m
    rim += ((b - xx > w0 / 2 - 4) & (b - xx < w0 / 2)) * 0.45
for cyb in (H * 0.075, H * 0.93):
    m = np.abs(yy - cyb) < 14
    bars |= m
    rim += (np.abs(yy - (cyb - 14)) < 2) * 0.3
# 栏杆上铁锈的颗粒

# 胶片颗粒 + 暗角
grain = rng.normal(0, 0.018, (H, W)).astype(np.float32)
vig = 1 - 0.75 * (((xx / W - 0.5) ** 2 + (yy / H - 0.48) ** 2) * 2.2)
val = np.clip(val * np.clip(vig, 0, 1) + grain, 0, 1)
val = np.where(bars, rim * (0.4 + 0.6 * fbm(40, 3)), val)

# ---------- 4. 挣扎：光斑里一个小笼子，一粒红点不停撞墙 ----------
red = np.zeros((H, W), np.float32)
cg = Image.new("L", (W, H), 0); dc = ImageDraw.Draw(cg)
cx0, cy0, cs = FX - 70, FY - 150, 140
for k in range(6):                                  # 小笼子的栏
    x = cx0 + k * cs / 5
    dc.line([(x, cy0), (x, cy0 + cs)], fill=255, width=2)
dc.line([(cx0, cy0), (cx0 + cs, cy0)], fill=255, width=2)
dc.line([(cx0, cy0 + cs), (cx0 + cs, cy0 + cs)], fill=255, width=2)
cage = to_f(cg)
trail = Image.new("L", (W, H), 0); dt = ImageDraw.Draw(trail)
p = np.array([cx0 + cs * 0.5, cy0 + cs * 0.5]); v = rng.normal(0, 1, 2); v = v / np.linalg.norm(v) * 3.2
pts = []
for i in range(900):
    v += rng.normal(0, 0.35, 2); v = v / np.linalg.norm(v) * 3.2
    p = p + v
    for a in (0, 1):
        lo = (cx0 if a == 0 else cy0) + 4; hi = lo + cs - 8
        if p[a] < lo: p[a] = lo; v[a] = abs(v[a])
        if p[a] > hi: p[a] = hi; v[a] = -abs(v[a])
    pts.append(tuple(p))
for i in range(1, len(pts)):
    a = i / len(pts)
    dt.line([pts[i - 1], pts[i]], fill=int(30 + 225 * a ** 2.5), width=2)
red = to_f(trail) * 0.75
head = np.exp(-(((xx - pts[-1][0]) ** 2 + (yy - pts[-1][1]) ** 2) / 40.0))
red = np.clip(red + head * 1.6, 0, 1)
val = np.maximum(val, cage * 0.9)
# 远处几粒更小、快要熄灭的红
for _ in range(3):
    t = rng.uniform(0.3, 0.8)
    rx = VX + rng.normal(0, 60); ry = VY + rng.normal(30, 40)
    red += np.exp(-(((xx - rx) ** 2 + (yy - ry) ** 2) / 3.0)) * t
red = np.clip(red, 0, 1)

# ---------- 5. 三色有序抖动 ----------
def bayer(n):
    m = np.array([[0, 2], [3, 1]])
    while m.shape[0] < n:
        m = np.block([[4 * m, 4 * m + 2], [4 * m + 3, 4 * m + 1]])
    return (m + 0.5) / (n * n)
B = bayer(8)
by = ((yy // PX) % 8).astype(int); bxi = ((xx // PX) % 8).astype(int)
th = B[by, bxi]
# 先按 PX 块采样，做出网点颗粒
vb = val[(yy // PX * PX).astype(int), (xx // PX * PX).astype(int)]
rb = red[(yy // PX * PX).astype(int), (xx // PX * PX).astype(int)]
out = np.empty((H, W, 3), np.uint8); out[:] = BG
out[vb > th] = CY
out[rb > th] = RD
Image.fromarray(out).save(f"act3_silence_s{SEED}.png")
print("ok", SEED)
