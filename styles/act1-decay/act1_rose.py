"""暗面三部曲 · 第一幕《糜烂》· 玫瑰版
黑暗 / 糜烂 / 丧
参考：蚀刻版画（酸腐蚀铜板）× 贝克辛斯基。一朵垂头的玫瑰，
长满霉斑（Gray-Scott 反应扩散），花瓣散落，青色腐液往下流淌。
只用三色：#000030 底 / #610070 淤紫 / #18a69a 腐烂荧光（只在霉斑边缘）。
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage
import math, sys

SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 5
OUT = sys.argv[2] if len(sys.argv) > 2 else f"act1_rose_s{SEED}.png"
rng = np.random.default_rng(SEED)
W, H = 1200, 1500
PX = 2
BG = np.array([0x00, 0x00, 0x30]); PU = np.array([0x61, 0x00, 0x70]); TE = np.array([0x18, 0xa6, 0x9a])
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

def fbm(scale, octaves=4, shape=(H, W)):
    h, w = shape; out = np.zeros(shape, np.float32); amp = 1.0; tot = 0
    for o in range(octaves):
        s = max(2, int(scale / (2 ** o)))
        g = rng.random((h // s + 3, w // s + 3)).astype(np.float32)
        im = Image.fromarray((g * 255).astype(np.uint8)).resize((w + 3 * s, h + 3 * s), Image.BICUBIC)
        out += amp * np.asarray(im, np.float32)[s:s + h, s:s + w] / 255.0
        tot += amp; amp *= 0.5
    return out / tot

# ---------- 1. 一朵垂头的玫瑰（花瓣由外向内一层层叠，再用噪声揉烂） ----------
HX, HY = 660, 600
pf = Image.new("L", (W, H), 0); dp = ImageDraw.Draw(pf)      # 花瓣明暗
pm = Image.new("L", (W, H), 0); dm = ImageDraw.Draw(pm)      # 轮廓遮罩
lo = Image.new("L", (W, H), 0); dlo = ImageDraw.Draw(lo)        # 散落花瓣单独一层
def petal(cx, cy, rx, ry, ang, val, loose=False):
    pts = []
    for t in np.linspace(0, 2 * math.pi, 90):
        wob = 1 + 0.12 * math.sin(3 * t + ang * 2) + 0.06 * math.sin(7 * t)
        x = rx * math.cos(t) * wob; y = ry * math.sin(t) * wob
        if y < 0: y *= 0.75                                   # 花瓣尖一点、往外卷
        pts.append((cx + x * math.cos(ang) - y * math.sin(ang), cy + x * math.sin(ang) + y * math.cos(ang)))
    dp.polygon(pts, fill=int(min(1, val * 1.25) * 255), outline=0, width=6)    # 卷起的瓣缘更亮
    inset = [(cx + (px_ - cx) * 0.72, cy + (py_ - cy) * 0.72 + ry * 0.12) for px_, py_ in pts]
    dp.polygon(inset, fill=int(val * 0.55 * 255))                          # 瓣心往里陷、发暗
    dm.polygon(pts, fill=255)
    if loose:
        dlo.polygon(pts, fill=int(val * 255), outline=0, width=4)
        dlo.polygon(inset, fill=int(val * 0.6 * 255))
N = 30
for i in reversed(range(N)):
    t = i / (N - 1)
    a = i * 2.39996
    rpos = 12 + 175 * t ** 0.85
    cx = HX + rpos * math.cos(a); cy = HY + rpos * math.sin(a) * 0.62 + 40 * t   # 压扁 = 花头往前垂
    sz = 46 + 120 * t
    val = 0.55 + 0.35 * (1 - t) + rng.uniform(-0.06, 0.06)
    petal(cx, cy, sz, sz * 0.7, a + math.pi / 2, val)
sw_ = [(HX + (4 + 3.2 * th_) * math.cos(th_), HY + (4 + 3.2 * th_) * math.sin(th_) * 0.62 + 6) for th_ in np.linspace(0, 6 * math.pi, 200)]
dp.line(sw_, fill=0, width=4)
# 花萼和弯下去的茎
def bez(p0, p1, p2, p3, n=120):
    tt = np.linspace(0, 1, n)[:, None]
    return [tuple(q) for q in ((1 - tt) ** 3 * p0 + 3 * (1 - tt) ** 2 * tt * p1 + 3 * (1 - tt) * tt ** 2 * p2 + tt ** 3 * p3)]
stem = bez(np.array([470., 1520.]), np.array([420., 1150.]), np.array([380., 520.]), np.array([HX - 120., HY - 150.]))
dp.line(stem, fill=110, width=16, joint="curve"); dm.line(stem, fill=255, width=16, joint="curve")
for k in range(12, len(stem) - 10, 13):                     # 刺
    x, y = stem[k]; side = 1 if (k // 13) % 2 else -1
    tri = [(x + side * 6, y - 6), (x + side * 6, y + 6), (x + side * 26, y + 14)]
    dp.polygon(tri, fill=110); dm.polygon(tri, fill=255)
def leaf(x, y, L_, ang):
    pts = []
    for t in np.linspace(0, 1, 40):
        pts.append((t * L_, math.sin(t * math.pi) * L_ * 0.28 * (1 - 0.3 * t)))
    for t in np.linspace(1, 0, 40):
        pts.append((t * L_, -math.sin(t * math.pi) * L_ * 0.22 * (1 - 0.3 * t)))
    pts = [(x + px_ * math.cos(ang) - py_ * math.sin(ang), y + px_ * math.sin(ang) + py_ * math.cos(ang)) for px_, py_ in pts]
    dp.polygon(pts, fill=95, outline=0, width=4); dm.polygon(pts, fill=255)
    dp.line([pts[0], pts[40]], fill=0, width=3)
leaf(*stem[60], 190, 2.3)       # 往下耷拉的叶子
leaf(*stem[88], 150, 2.9)
# 掉在地上的花瓣
for j in range(18):                                          # 散落一地
    fx = rng.uniform(180, 1080); fy = rng.uniform(1330, 1450)
    petal(fx, fy, rng.uniform(28, 52), rng.uniform(12, 21), rng.uniform(-0.5, 0.5), rng.uniform(0.6, 0.8), True)
for j in range(9):                                           # 正在往下飘的
    fx = rng.uniform(300, 1000); fy = rng.uniform(880, 1280)
    if 480 < fx < 900 and fy < 1100: fx += 300 * (1 if fx > 690 else -1)
    petal(fx, fy, rng.uniform(26, 42), rng.uniform(12, 18), rng.uniform(0, 6.28), rng.uniform(0.7, 0.9), True)
petal_val0 = np.asarray(pf, np.float32) / 255.0
mask0 = np.asarray(pm.filter(ImageFilter.GaussianBlur(2)), np.float32) / 255.0
wx = (fbm(200, 4) - 0.5) * 22; wy = (fbm(200, 4) - 0.5) * 22      # 轻一点的扭曲，保住玫瑰的形
mask = ndimage.map_coordinates(mask0, [yy + wy, xx + wx], order=1, mode="constant")
petal_val = ndimage.map_coordinates(petal_val0, [yy + wy, xx + wx], order=1, mode="constant")

# ---------- 2. 霉斑：Gray-Scott 反应扩散 ----------
sh, sw = H // 3, W // 3
ms = np.asarray(Image.fromarray((mask * 255).astype(np.uint8)).resize((sw, sh)), np.float32) / 255.0
U = np.ones((sh, sw), np.float32); V = np.zeros((sh, sw), np.float32)
seeds = (rng.random((sh, sw)) < 0.009) & (ms > 0.4)
seeds = ndimage.binary_dilation(seeds, iterations=2)
U[seeds] = 0.5; V[seeds] = 0.25 + 0.05 * rng.random(seeds.sum())
F = 0.036 + 0.02 * fbm(30, 3, (sh, sw))            # 进料率随位置变：有的地方斑点，有的地方菌丝
K = np.where(ms > 0.3, 0.0605, 0.075)              # 人形外杀死率高，霉只长在身上
Du, Dv = 0.16, 0.08
def lap(Z):
    return (np.roll(Z, 1, 0) + np.roll(Z, -1, 0) + np.roll(Z, 1, 1) + np.roll(Z, -1, 1) - 4 * Z)
for i in range(3900):
    uvv = U * V * V
    U += Du * lap(U) - uvv + F * (1 - U)
    V += Dv * lap(V) + uvv - (F + K) * V
Vb = np.asarray(Image.fromarray(np.clip(V * 3 * 255, 0, 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32) / 255.0

# ---------- 3. 合成两层：淤紫的肉身 + 霉斑边缘的荧光 ----------
light = np.clip(1.2 - (yy / H) * 0.5 - np.abs(xx / W - 0.55) * 0.4, 0, 1)   # 从右上方来的一点点光
flesh = petal_val * (0.8 + 0.4 * fbm(90, 5)) * np.maximum(light, 1.05 * (yy > 860))
flesh = np.where((Vb > 0.32) & (fbm(160, 3) > 0.42), flesh * 0.3, flesh)      # 被霉吃掉的地方发黑
flesh += Vb * mask * 0.2
# 蚀刻坑：随机腐蚀的小洞（把紫色吃掉）
pits = ndimage.gaussian_filter((rng.random((H, W)) < 0.004).astype(np.float32), 2.2) * 25
flesh = np.clip(flesh - pits * mask, 0, 1)
# 霉斑边缘 = V 的梯度
gy, gx = np.gradient(ndimage.gaussian_filter(Vb, 1.2))
edge = np.sqrt(gx ** 2 + gy ** 2); edge = edge / (np.percentile(edge[mask > 0.3], 99.5) + 1e-6)
patch = np.clip((fbm(160, 4) - 0.44) * 4, 0, 1)                   # 荧光只成片出现，不撒满
glow = np.clip(edge, 0, 1) ** 1.3 * patch * mask * light * 1.0

# ---------- 4. 融化：像素往下淌 ----------
def melt(A, drip_len, decay):
    acc = A.copy()
    for k in range(drip_len):
        sh_ = np.zeros_like(acc); sh_[1:] = acc[:-1]
        acc = np.maximum(acc, sh_ * decay)
    return acc
cols = rng.random(W)
decay = np.where(cols < 0.4, 0.993 + 0.006 * rng.random(W), 0.9).astype(np.float32)[None, :]
decay = ndimage.uniform_filter1d(decay, 3, axis=1)
src = flesh * (yy > 700) * (yy < 860) * (flesh > 0.3) * (xx > 470)   # 从垂下的花头往下滴                                           # 只从下半身往下淌
flesh = np.maximum(flesh, melt(src, 420, decay) * 0.95)
glow = np.maximum(glow, melt(glow * (yy > 700) * (yy < 860), 300, decay) * 0.8)
# 底部淤积成一滩
pool = np.exp(-((yy - 1420) / 60) ** 2) * np.clip((fbm(120, 3) - 0.35) * 2, 0, 1) * \
       np.exp(-((xx - 620) / 520) ** 2) * 0.25
flesh = np.maximum(flesh, pool)

# 腐烂的青色汁液：从花头底部往下淌，粗细不一，末端成滴，地上积一滩
liq = Image.new("L", (W, H), 0); dq = ImageDraw.Draw(liq)
for j in range(17):
    x = rng.uniform(470, 900); y0 = 700 + 110 * math.exp(-((x - 690) / 170) ** 2) + rng.uniform(-20, 20)
    ln = rng.uniform(120, 640); wd = rng.uniform(3, 11); path = [(x, y0)]
    for _ in range(int(ln / 5)):
        px_, py_ = path[-1]; path.append((px_ + rng.normal(0, 0.7), py_ + 5))
    for k in range(1, len(path)):
        ww = wd * (1 - 0.5 * k / len(path))
        dq.line([path[k - 1], path[k]], fill=int(255 * (0.95 - 0.3 * k / len(path))), width=max(2, int(ww)))
    ex, ey = path[-1]; dq.ellipse([ex - wd * 0.9, ey - wd * 0.4, ex + wd * 0.9, ey + wd * 1.8], fill=255)
for j in range(0):                                           # 花头上的湿斑（关掉）
    x = rng.uniform(500, 880); y = rng.uniform(560, 800)
    r = rng.uniform(4, 14); dq.ellipse([x - r, y - r * 0.8, x + r, y + r * 1.4], fill=int(rng.uniform(150, 230)))
liquid = np.asarray(liq.filter(ImageFilter.GaussianBlur(1.0)), np.float32) / 255.0 * (mask > 0.2) + \
         np.asarray(liq.filter(ImageFilter.GaussianBlur(1.0)), np.float32) / 255.0 * (yy > 800)
pool_t = np.exp(-((yy - 1440) / 45) ** 2) * np.exp(-((xx - 690) / 300) ** 2) * np.clip((fbm(80, 3) - 0.3) * 2.5, 0, 1)
glow = np.maximum(glow, np.clip(liquid + pool_t * 0.6, 0, 1))

loose = np.asarray(lo, np.float32) / 255.0
has_lo = loose > 0.02
flesh = np.where(has_lo, loose * (0.85 + 0.3 * fbm(60, 3)), flesh)
glow = np.where(has_lo & (glow < 0.5), glow * 0.3, glow)

# 颗粒 + 暗角（暗部保持干净）
vig = np.clip(1 - 0.7 * (((xx / W - 0.52) ** 2 + (yy / H - 0.5) ** 2) * 2.2), 0, 1)
flesh = np.clip(flesh * vig + rng.normal(0, 0.02, (H, W)) * (flesh > 0.04), 0, 1)
glow = np.clip(glow * vig, 0, 1)
# 空中漂浮的孢子
spores = ndimage.gaussian_filter((rng.random((H, W)) < 0.0006).astype(np.float32), 1.0) * 8 * \
         np.clip(fbm(300, 2) - 0.45, 0, 1) * 3
glow = np.maximum(glow, np.clip(spores, 0, 1))

# ---------- 5. 三色有序抖动 ----------
def bayer(n):
    mm = np.array([[0, 2], [3, 1]])
    while mm.shape[0] < n: mm = np.block([[4 * mm, 4 * mm + 2], [4 * mm + 3, 4 * mm + 1]])
    return (mm + 0.5) / (n * n)
B = bayer(8)
iy = (yy // PX * PX).astype(int); ix = (xx // PX * PX).astype(int)
th = B[((yy // PX) % 8).astype(int), ((xx // PX) % 8).astype(int)]
out = np.empty((H, W, 3), np.uint8); out[:] = BG
out[flesh[iy, ix] > th] = PU
out[glow[iy, ix] > th] = TE
Image.fromarray(out).save(OUT)
print("ok", OUT)
