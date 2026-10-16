"""暗面三部曲 · 第一幕《糜烂》
黑暗 / 糜烂 / 丧
参考：蚀刻版画（酸腐蚀铜板）× 贝克辛斯基。一个低头的无脸人形，
身上长满霉斑（Gray-Scott 反应扩散），被噪声揉烂，往下融化流淌。
只用三色：#000030 底 / #610070 淤紫 / #18a69a 腐烂荧光（只在霉斑边缘）。
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage
import math, sys

SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 5
OUT = sys.argv[2] if len(sys.argv) > 2 else f"act1_decay_s{SEED}.png"
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

# ---------- 1. 低头的人形（椭圆拼起来，再用噪声揉烂） ----------
m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m)
def ell(cx, cy, rx, ry, ang=0, val=255):
    pts = [(cx + rx * math.cos(t) * math.cos(ang) - ry * math.sin(t) * math.sin(ang),
            cy + rx * math.cos(t) * math.sin(ang) + ry * math.sin(t) * math.cos(ang))
           for t in np.linspace(0, 2 * math.pi, 120)]
    d.polygon(pts, fill=val)
ell(540, 560, 165, 205, -0.6)          # 低垂的头
ell(630, 760, 80, 120, -0.4)            # 脖子
ell(620, 980, 410, 230, 0.05)          # 肩背
ell(370, 900, 140, 190, 0.5)           # 塌下去的一侧肩
mask0 = np.asarray(m.filter(ImageFilter.GaussianBlur(10)), np.float32) / 255.0
# 域扭曲：把轮廓揉得像在腐烂
wx = (fbm(220, 4) - 0.5) * 110; wy = (fbm(220, 4) - 0.5) * 110
mask = ndimage.map_coordinates(mask0, [yy + wy, xx + wx], order=1, mode="constant")

# ---------- 2. 霉斑：Gray-Scott 反应扩散 ----------
sh, sw = H // 3, W // 3
ms = np.asarray(Image.fromarray((mask * 255).astype(np.uint8)).resize((sw, sh)), np.float32) / 255.0
U = np.ones((sh, sw), np.float32); V = np.zeros((sh, sw), np.float32)
seeds = (rng.random((sh, sw)) < 0.012) & (ms > 0.4)
seeds = ndimage.binary_dilation(seeds, iterations=2)
U[seeds] = 0.5; V[seeds] = 0.25 + 0.05 * rng.random(seeds.sum())
F = 0.036 + 0.02 * fbm(30, 3, (sh, sw))            # 进料率随位置变：有的地方斑点，有的地方菌丝
K = np.where(ms > 0.3, 0.0605, 0.075)              # 人形外杀死率高，霉只长在身上
Du, Dv = 0.16, 0.08
def lap(Z):
    return (np.roll(Z, 1, 0) + np.roll(Z, -1, 0) + np.roll(Z, 1, 1) + np.roll(Z, -1, 1) - 4 * Z)
for i in range(5000):
    uvv = U * V * V
    U += Du * lap(U) - uvv + F * (1 - U)
    V += Dv * lap(V) + uvv - (F + K) * V
Vb = np.asarray(Image.fromarray(np.clip(V * 3 * 255, 0, 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32) / 255.0

# ---------- 3. 合成两层：淤紫的肉身 + 霉斑边缘的荧光 ----------
light = np.clip(1.15 - (yy / H) * 0.6 - np.abs(xx / W - 0.62) * 0.5, 0, 1)   # 从右上方来的一点点光
flesh = mask * (0.18 + 0.42 * fbm(90, 5)) * light
flesh += Vb * mask * 0.55
# 蚀刻坑：随机腐蚀的小洞（把紫色吃掉）
pits = ndimage.gaussian_filter((rng.random((H, W)) < 0.004).astype(np.float32), 2.2) * 25
flesh = np.clip(flesh - pits * mask, 0, 1)
# 霉斑边缘 = V 的梯度
gy, gx = np.gradient(ndimage.gaussian_filter(Vb, 1.2))
edge = np.sqrt(gx ** 2 + gy ** 2); edge = edge / (np.percentile(edge[mask > 0.3], 99.5) + 1e-6)
patch = np.clip((fbm(160, 4) - 0.42) * 4, 0, 1)                   # 荧光只成片出现，不撒满
glow = np.clip(edge, 0, 1) ** 1.3 * patch * mask * light * 1.4

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
src = flesh * (yy > 850) * (flesh > 0.25)                                           # 只从下半身往下淌
flesh = np.maximum(flesh, melt(src, 420, decay) * 0.95)
glow = np.maximum(glow, melt(glow * (yy > 850), 260, decay) * 0.8)
# 底部淤积成一滩
pool = np.exp(-((yy - 1420) / 60) ** 2) * np.clip((fbm(120, 3) - 0.35) * 2, 0, 1) * \
       np.exp(-((xx - 620) / 520) ** 2) * 0.5
flesh = np.maximum(flesh, pool)

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
