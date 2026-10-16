"""暗面 · 配色 5《咒火》—— 火刑柱上仰头尖叫的女人。她是不是女巫，无人知道；
但怒意到了顶点，紫色的诅咒从她嘴里升起，又落回围观者头上。
#0b1019 底 / #bc9800 火 / #d900ff 诅咒；参考：猎巫时代木刻传单 × 戈雅。"""
import numpy as np, math, sys
from PIL import Image, ImageDraw, ImageFilter
SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 13
rng = np.random.default_rng(SEED)
W, H = 1200, 1500; PX = 2
BG, GO, VI = np.array([0x0b, 0x10, 0x19]), np.array([0xbc, 0x98, 0x00]), np.array([0xd9, 0x00, 0xff])
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
def noise(sy, sx, oct=4):
    out = np.zeros((H, W), np.float32); a = 1; t = 0
    for o in range(oct):
        ny, nx = max(2, int(H / sy * 2 ** o)), max(2, int(W / sx * 2 ** o))
        g = rng.random((ny + 2, nx + 2)).astype(np.float32)
        im = np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32) / 255
        out += a * im; t += a; a *= .5
    return out / t
def L(img, b=0):
    if b: img = img.filter(ImageFilter.GaussianBlur(b))
    return np.asarray(img, np.float32) / 255

CX = 600; BASE = 1290
# ---------- 火：竖向拉长的湍流，一条条火舌往上舔 ----------
warp = noise(260, 260, 3)
xw = xx + (warp - 0.5) * 140 * np.clip((BASE - yy) / 600, 0, 1)
turb = noise(170, 18, 4)
turb = turb[yy.astype(int), np.clip(xw, 0, W - 1).astype(int)]
d = np.clip((BASE + 40 - yy) / 760, 0, 1.5)                              # 0 在柴堆，1 到火顶
env = np.exp(-((xw - CX) / (330 * (1 - 0.55 * np.clip(d, 0, 1)) + 1)) ** 2)
fire = np.clip((turb * 1.7 - d * 1.0 + env * 0.3 - 0.45) * 2.4, 0, 1) * env * (yy < BASE + 60)
fire *= np.clip(1.2 - d * 0.6, 0, 1)
# 柴堆
wood = Image.new("L", (W, H), 0); dw = ImageDraw.Draw(wood)
for k in range(46):
    y = BASE + rng.uniform(-30, 70); x0 = CX + rng.normal(0, 170); ln = rng.uniform(120, 260); a = rng.normal(0, 0.35)
    dw.line([(x0 - math.cos(a) * ln / 2, y - math.sin(a) * ln / 2), (x0 + math.cos(a) * ln / 2, y + math.sin(a) * ln / 2)], fill=255, width=int(rng.uniform(10, 18)))
woodm = L(wood) > 0.5

# ---------- 人：被绑在柱上，仰头尖叫，长发被火往上卷 ----------
fig = Image.new("L", (W, H), 0); df = ImageDraw.Draw(fig)
df.rectangle([CX - 16, 240, CX + 16, BASE + 40], fill=255)                          # 柱
df.line([(CX - 70, 330), (CX + 70, 330)], fill=255, width=20)                       # 横木
# 躯干：弓起的背、往前挺的胸，裙摆破碎，下半身被火吞掉
body = [(CX - 78, 668), (CX - 92, 720), (CX - 70, 820), (CX - 80, 900), (CX - 110, 1010), (CX - 150, 1130), (CX - 120, 1200),
        (CX + 130, 1200), (CX + 160, 1120), (CX + 118, 1000), (CX + 96, 890), (CX + 108, 790), (CX + 104, 712), (CX + 80, 668)]
df.polygon(body, fill=255)
for sgn in (-1, 1):                                                                 # 双手被高高吊绑在横木上
    df.line([(CX + sgn * 74, 690), (CX + sgn * 150, 520), (CX + sgn * 58, 352)], fill=255, width=30, joint="curve")
    df.ellipse([CX + sgn * 58 - 18, 334, CX + sgn * 58 + 18, 370], fill=255)
# 头：侧脸，猛地后仰，嘴张到最大，冲着天
prof = [(-30, 50), (-55, 0), (-35, -50), (15, -55), (40, -30), (42, -18), (60, -2), (45, 6), (48, 15),
        (34, 22), (16, 30), (36, 52), (40, 72), (16, 80), (8, 100), (4, 128), (-28, 128)]
mouth = [(34, 22), (16, 30), (36, 52), (46, 34)]
A = math.radians(58); sc = 1.55
def rot(p):
    x, y = p[0] * sc, p[1] * sc
    return (x * math.cos(A) + y * math.sin(A), -x * math.sin(A) + y * math.cos(A))
ox, oy = CX - 6, 540                                                               # 颅骨中心
nb = rot((-12, 118)); df.line([(CX + 4, 690), (ox + nb[0], oy + nb[1])], fill=255, width=52)   # 绷紧的脖子
headpoly = [(ox + rot(p)[0], oy + rot(p)[1]) for p in prof]
df.polygon(headpoly, fill=255)
mouthpoly = [(ox + rot(p)[0], oy + rot(p)[1]) for p in mouth]
df.polygon(mouthpoly, fill=0)
hx, hy = ox, oy
mx, my = [sum(c) / len(c) for c in zip(*mouthpoly)]
mo = Image.new("L", (W, H), 0); ImageDraw.Draw(mo).polygon(mouthpoly, fill=255); mouthm = L(mo) > 0.5
# 头发：一缕缕往上、往左右甩
for k in range(34):
    a0 = rng.uniform(-3.4, -1.0); x, y = hx + math.cos(a0) * 45, hy - 10 + math.sin(a0) * 40
    ang = a0; pts = [(x, y)]
    for s in range(int(rng.uniform(20, 46))):
        ang += rng.normal(0, 0.14) + (-math.pi / 2 - ang) * 0.03
        x += math.cos(ang) * 6 + math.sin(s * 0.5 + k) * 2; y += math.sin(ang) * 6; pts.append((x, y))
    df.line(pts, fill=255, width=int(rng.uniform(4, 9)), joint="curve")
figm = L(fig) > 0.5
# 绳子（火光照亮的几道）
rope = Image.new("L", (W, H), 0); dr = ImageDraw.Draw(rope)
for y in (790, 900):
    dr.arc([CX - 112, y - 14, CX + 112, y + 14], 0, 180, fill=200, width=2)
for sgn in (-1, 1):
    dr.line([(CX + sgn * 40, 345), (CX + sgn * 76, 360)], fill=220, width=4)
ropem = L(rope)

# ---------- 围观的人群：前景黑剪影 ----------
crowd = Image.new("L", (W, H), 0); dc = ImageDraw.Draw(crowd)
heads = []
for k in range(11):
    x = -40 + k * 125 + rng.normal(0, 25); y = 1360 + rng.normal(0, 30) + (25 if 380 < x < 820 else 0)
    r = rng.uniform(42, 58)
    dc.ellipse([x - r * 0.85, y - r, x + r * 0.85, y + r], fill=255)
    dc.ellipse([x - r * 2.2, y + r * 0.7, x + r * 2.2, y + r * 4.5], fill=255)
    if rng.random() < 0.35:                                                         # 举着的火把/干草叉
        dc.line([(x + r, y + 40), (x + r * 1.6, y - 170)], fill=255, width=9)
    heads.append((x, y, r))
crowdm = L(crowd) > 0.5

# ---------- 诅咒：紫色从她张开的嘴里螺旋升起，在天上结成一圈咒文，再垂落到人群头上 ----------
cur = Image.new("L", (W, H), 0); dv = ImageDraw.Draw(cur)
for k in range(5):                                                                  # 螺旋升起的咒烟
    ph = k * 2 * math.pi / 5; pts = []
    for t in np.linspace(0, 1, 160):
        y = my - t * (my - 210); r = 14 + 150 * t ** 1.4
        pts.append((mx + (CX - mx) * t + r * math.sin(ph + t * 9), y))
    for i in range(1, len(pts)):
        dv.line([pts[i - 1], pts[i]], fill=int(120 + 135 * i / len(pts)), width=2 + int(3 * i / len(pts)))
RC, RY, RR = CX, 200, 210                                                           # 咒文之环
dv.ellipse([RC - RR, RY - RR * 0.42, RC + RR, RY + RR * 0.42], outline=255, width=3)
dv.ellipse([RC - RR + 26, RY - RR * 0.42 + 11, RC + RR - 26, RY + RR * 0.42 - 11], outline=200, width=2)
for k in range(30):                                                                 # 环上的符文
    a = k / 30 * 2 * math.pi; gx = RC + math.cos(a) * (RR - 13); gy = RY + math.sin(a) * (RR - 13) * 0.42
    for s in range(3):
        a1 = rng.uniform(0, 6.28); l1 = rng.uniform(4, 9)
        dv.line([(gx, gy), (gx + math.cos(a1) * l1, gy + math.sin(a1) * l1 * 0.6)], fill=255, width=2)
for k in range(200):                                                                # 诅咒像灰一样落下来，越往下越密，落在人群头上
    x = rng.uniform(0, W); y = 700 + (rng.random() ** 0.5) * 700
    ln = rng.uniform(6, 16); c = int(90 + 165 * ((y - 700) / 700) ** 1.5)
    dv.line([(x, y), (x + rng.normal(0, 2), y + ln)], fill=c, width=2)
for (x, y, r) in heads:
    dv.arc([x - r * 0.9, y - r - 6, x + r * 0.9, y - r + 14], 180, 360, fill=255, width=3)
curse = L(cur, 0.6)

# ---------- 合成 ----------
haze = np.exp(-(((xx - CX) / 300) ** 2 + ((yy - 820) / 460) ** 2)) * (0.12 + 0.3 * noise(160, 160, 3))   # 火光映亮的烟，给剪影当背景
haze += np.exp(-(((xx - CX) / 520) ** 2 + ((yy - 1330) / 120) ** 2)) * 0.35                           # 地面火光，衬出人群
haze *= np.clip((yy - 200) / 350, 0, 1)

gold = np.maximum(fire, haze)
gold = np.maximum(gold, woodm * 0)                                                  # 柴是黑的
glow_near = L(Image.fromarray((np.clip(fire, 0, 1) * 255).astype(np.uint8)), 28) * 1.6
def rim(mask, w=4):
    m = Image.fromarray((mask * 255).astype(np.uint8))
    return (L(m.filter(ImageFilter.MaxFilter(1))) - L(m.filter(ImageFilter.MinFilter(2 * w + 1))) > 0.5)
fr = rim(figm, 3) * np.clip(0.55 + glow_near, 0, 1)
wr = rim(woodm, 3) * np.clip(glow_near, 0, 1)
cr = rim(crowdm, 3) * 0.6 * (yy < 1440)
gold = np.where(figm | woodm | crowdm, 0, gold)
gold = np.maximum(gold, np.where(figm, fr, 0)); gold = np.maximum(gold, np.where(woodm, wr, 0))
gold = np.maximum(gold, np.where(crowdm, cr, 0))
gold = np.maximum(gold, ropem * figm * np.clip(0.6 + glow_near, 0, 1))
gold = np.where(figm & (yy > 960) & (fire > 0.35), fire, gold)                       # 火舔到身前
for _ in range(220):                                                                # 往上飞的火星
    x = CX + rng.normal(0, 210); y = BASE - rng.uniform(150, 1100)
    if 0 < x < W - 3 and 0 < y < H - 3: gold[int(y):int(y) + 2, int(x):int(x) + 2] = rng.uniform(0.4, 1.0)
vio = np.maximum(curse * ~figm, mouthm * 1.0)
vio = np.maximum(vio, np.exp(-(((xx - mx) ** 2 + (yy - my) ** 2) / 900)) * 0.9 * ~figm)
vig = np.clip(1 - 0.55 * (((xx / W - 0.5) ** 2 + (yy / H - 0.5) ** 2) * 2.2), 0, 1)
g = np.clip(gold * vig + rng.normal(0, 0.02, (H, W)) * (gold > 0.08), 0, 1)
v = np.clip(vio * vig, 0, 1)

m = np.array([[0, 2], [3, 1]])
while m.shape[0] < 8: m = np.block([[4 * m, 4 * m + 2], [4 * m + 3, 4 * m + 1]])
B = (m + .5) / 64
iy, ix = (yy // PX * PX).astype(int), (xx // PX * PX).astype(int)
th = B[(yy // PX % 8).astype(int), (xx // PX % 8).astype(int)]
out = np.empty((H, W, 3), np.uint8); out[:] = BG
out[g[iy, ix] > th] = GO; out[v[iy, ix] > th] = VI
Image.fromarray(out).save(f"witch_s{SEED}.png"); print("ok", (out == BG).all(-1).mean())
