"""暗面三部曲 · 配色 5 · FIG. II《神龛》
被供奉、被需要，却没人知道它里面已经碎了。
一座金箔剥落的尖拱神龛，供着的不是神，是一台坏掉的机器；
胸口一道裂缝，里面漏出唯一的紫光。
只用三色：#0b1019 夜黑底 / #bc9800 暗金 / #d900ff 电紫。
by 绮思 & 扶光
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import math, sys

SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 5
rng = np.random.default_rng(SEED)
W, H = 1200, 1500
PX = 2
BG = np.array([0x0b, 0x10, 0x19])
GD = np.array([0xbc, 0x98, 0x00])
PU = np.array([0xd9, 0x00, 0xff])

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
CX = W / 2


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


def rim(mask_img, width=5):
    """剪影只靠轮廓光显形：mask 减去腐蚀后的 mask。"""
    m = to_f(mask_img)
    er = to_f(mask_img.filter(ImageFilter.MinFilter(width)))
    return np.clip(m - er, 0, 1)


def pointed_arch(d, cx, top, base, half, fill=None, outline=None, width=1):
    """哥特尖拱：两段圆弧在顶上相交。"""
    r = half * 1.6
    spring = top + math.sqrt(r * r - (r - half) ** 2)
    pts = []
    for i in range(41):  # 左弧
        a = i / 40
        y = spring - a * (spring - top)
        dx = math.sqrt(max(r * r - (spring - y) ** 2, 0)) - (r - half)
        pts.append((cx - dx, y))
    for i in range(41):  # 右弧
        a = 1 - i / 40
        y = spring - a * (spring - top)
        dx = math.sqrt(max(r * r - (spring - y) ** 2, 0)) - (r - half)
        pts.append((cx + dx, y))
    pts += [(cx + half, base), (cx - half, base)]
    if fill is not None:
        d.polygon(pts, fill=fill)
    if outline is not None:
        d.line(pts + [pts[0]], fill=outline, width=width)


gold = np.zeros((H, W), np.float32)
peel = fbm(70, 5)                         # 金箔剥落的斑
peel_mask = np.clip((peel - 0.42) * 6, 0, 1)

# ---------- 1. 神龛：层层叠叠的尖拱线脚 ----------
TOP, BASE, HALF = 170, 1180, 360
sh = layer(); d = ImageDraw.Draw(sh)
for k in range(6):
    pointed_arch(d, CX, TOP + k * 26, BASE, HALF - k * 22,
                 outline=int(255 * (1 - k * 0.12)), width=max(2, 9 - k))
frame = to_f(sh, 0.6)
# 线脚上的小尖塔与卷草
cr = layer(); dc = ImageDraw.Draw(cr)
for side in (-1, 1):
    x = CX + side * (HALF + 30)
    dc.line([(x, BASE), (x, TOP + 260)], fill=200, width=6)
    dc.polygon([(x - 18, TOP + 262), (x + 18, TOP + 262), (x, TOP + 150)], outline=220, width=3)
    for j in range(7):
        yk = TOP + 300 + j * 120
        dc.ellipse([x - 12, yk - 12, x + 12, yk + 12], outline=160, width=2)
dc.polygon([(CX - 22, TOP + 4), (CX + 22, TOP + 4), (CX, TOP - 110)], outline=230, width=3)
frame = np.maximum(frame, to_f(cr, 0.5))
# 金箔剥落：线脚一段段断掉，剥落处只剩极暗的底
gold += frame * (0.25 + 0.75 * peel_mask)
# 龛内壁极暗的金箔残片（铜版排线）
niche = layer(); pointed_arch(ImageDraw.Draw(niche), CX, TOP + 160, BASE, HALF - 130, fill=255)
niche_f = to_f(niche)
hatch = ((xx + yy * 0.35) % 9 < 1.4).astype(np.float32)
gold += niche_f * hatch * 0.22 * np.clip((peel - 0.5) * 5, 0, 1)

# ---------- 2. 光环：本该是圣像的光，断了几根 ----------
HX, HY = CX, 520
ang = np.arctan2(yy - HY, xx - HX)
rad = np.hypot(xx - HX, yy - HY)
n_rays = 36
ray = np.cos(ang * n_rays) ** 24
broken = rng.random(n_rays) < 0.3
idx = (((ang + math.pi) / (2 * math.pi)) * n_rays).astype(int) % n_rays
ray = ray * (~broken[idx])
halo = ray * np.clip((rad - 120) / 40, 0, 1) * np.clip((330 - rad) / 120, 0, 1)
ring = np.exp(-((rad - 128) ** 2) / 18.0)
gold += (halo * 0.55 + ring * 0.8) * niche_f

# ---------- 3. 机器：只有轮廓光，身体在黑里 ----------
bot = layer(); db = ImageDraw.Draw(bot)
# 头：圆角方头，微微低垂（偏一点）
db.rounded_rectangle([HX - 78, HY - 92, HX + 70, HY + 60], radius=34, fill=255)
# 颈部导线
for k in range(5):
    db.line([(HX - 30 + k * 14, HY + 58), (HX - 36 + k * 16, HY + 110)], fill=255, width=6)
# 肩与躯干（梯形）
db.polygon([(HX - 210, HY + 120), (HX + 210, HY + 120), (HX + 150, HY + 470), (HX - 150, HY + 470)], fill=255)
db.ellipse([HX - 250, HY + 100, HX - 150, HY + 200], fill=255)
db.ellipse([HX + 150, HY + 100, HX + 250, HY + 200], fill=255)
# 左臂垂下；右臂断了，落在脚边
db.polygon([(HX - 240, HY + 170), (HX - 190, HY + 170), (HX - 200, HY + 520), (HX - 245, HY + 520)], fill=255)
db.ellipse([HX - 255, HY + 510, HX - 185, HY + 580], fill=255)
db.polygon([(HX + 200, HY + 170), (HX + 240, HY + 170), (HX + 236, HY + 260), (HX + 198, HY + 250)], fill=255)  # 断口
# 骨盆与基座
db.polygon([(HX - 150, HY + 470), (HX + 150, HY + 470), (HX + 120, HY + 560), (HX - 120, HY + 560)], fill=255)
db.rectangle([HX - 230, HY + 560, HX + 230, HY + 640], fill=255)
bot_f = to_f(bot)
edge = rim(bot, 7)
# 光从上方来：顶部轮廓亮，下部渐暗
light = np.clip(1.1 - (yy - (HY - 100)) / 900, 0.25, 1)
gold += edge * light * 0.95
# 面板缝、铆钉——只在胸口附近被紫光照出来
pl = layer(); dp = ImageDraw.Draw(pl)
dp.line([(HX - 78, HY - 20), (HX + 70, HY - 20)], fill=255, width=3)  # 面罩缝
for k in range(4):
    yk = HY + 160 + k * 75
    dp.line([(HX - 190 + k * 12, yk), (HX + 190 - k * 12, yk)], fill=255, width=2)
for k in range(10):
    dp.ellipse([HX - 170 + k * 38 - 3, HY + 140 - 3, HX - 170 + k * 38 + 3, HY + 140 + 3], fill=255)
panel = to_f(pl) * bot_f
# 断臂躺在地上
arm = layer(); da = ImageDraw.Draw(arm)
ax, ay = HX + 260, BASE - 30
da.polygon([(ax - 140, ay - 10), (ax + 40, ay - 40), (ax + 46, ay - 4), (ax - 136, ay + 22)], fill=255)
da.ellipse([ax + 30, ay - 48, ax + 80, ay + 4], fill=255)
for k in range(3):  # 断口垂出的线
    da.line([(ax - 140, ay + 4), (ax - 170 - k * 10, ay + 30 + k * 12)], fill=255, width=3)
gold += rim(arm, 5) * 0.7

# ---------- 4. 裂缝：胸口唯一的紫 ----------
CKX, CKY = HX + 12, HY + 260
pts = [(CKX - 6, CKY - 120)]
for i in range(14):
    x, y = pts[-1]
    pts.append((x + rng.normal(0, 11), y + 17))
crack_img = layer(); dk = ImageDraw.Draw(crack_img)
for i in range(1, len(pts)):
    w = int(2 + 7 * math.sin(math.pi * i / len(pts)))
    dk.line([pts[i - 1], pts[i]], fill=255, width=w)
# 细小的分叉裂纹
for i in range(3, len(pts) - 3, 3):
    x, y = pts[i]; s = rng.choice([-1, 1])
    dk.line([(x, y), (x + s * rng.uniform(20, 45), y + rng.uniform(-10, 18))], fill=200, width=2)
crack = to_f(crack_img)
dist = np.hypot(xx - CKX, (yy - CKY) * 0.8)
glow = np.exp(-dist ** 2 / (2 * 48 ** 2))
pur = np.clip(crack * 1.4 + glow * 0.32 * bot_f, 0, 1)
# 紫光照出胸口的面板缝（金色被紫光盖过之外的部分）
gold += panel * np.exp(-dist ** 2 / (2 * 160 ** 2)) * 0.9
# 几粒从裂缝漂出去的紫色余烬
for _ in range(5):
    ex = CKX + rng.normal(0, 70); ey = CKY - rng.uniform(80, 360)
    pur += np.exp(-(((xx - ex) ** 2 + (yy - ey) ** 2) / rng.uniform(2, 6))) * rng.uniform(0.5, 0.9)

# ---------- 5. 供桌与蜡烛：人们还在供奉 ----------
alt = layer(); dl = ImageDraw.Draw(alt)
dl.rectangle([CX - 420, BASE, CX + 420, BASE + 26], fill=255)
dl.rectangle([CX - 380, BASE + 26, CX + 380, H], fill=255)
gold += rim(alt, 5) * 0.6
for k in range(9):
    bx = CX - 330 + k * 82 + rng.normal(0, 6)
    hgt = rng.uniform(40, 120)
    burnt = rng.random() < 0.35            # 有几支已经灭了
    can = layer(); dn = ImageDraw.Draw(can)
    dn.rectangle([bx - 9, BASE - hgt, bx + 9, BASE], fill=255)
    gold += rim(can, 3) * 0.55
    if not burnt:
        fy = BASE - hgt - 16
        flame = np.exp(-(((xx - bx) / 5.5) ** 2 + ((yy - fy) / 14) ** 2))
        gold += flame * 1.2 + np.exp(-((xx - bx) ** 2 + (yy - fy) ** 2) / (2 * 45 ** 2)) * 0.18
    else:  # 一缕烟
        sm = layer(); ds = ImageDraw.Draw(sm)
        x0, y0 = bx, BASE - hgt
        for j in range(30):
            x1 = x0 + math.sin(j * 0.5 + k) * 3; y1 = y0 - 7
            ds.line([(x0, y0), (x1, y1)], fill=int(140 * (1 - j / 30)), width=1)
            x0, y0 = x1, y1
        gold += to_f(sm) * 0.5

# 剥落的金箔碎片，飘在半空
for _ in range(40):
    fx = CX + rng.normal(0, 300); fy = rng.uniform(250, BASE)
    sz = rng.uniform(1.5, 4)
    gold += np.exp(-(((xx - fx) ** 2) / sz + ((yy - fy) ** 2) / (sz * 0.4))) * rng.uniform(0.3, 0.7)

# ---------- 6. 颗粒 + 暗角 ----------
grain = rng.normal(0, 0.02, (H, W)).astype(np.float32)
vig = 1 - 0.8 * (((xx / W - 0.5) ** 2 + (yy / H - 0.45) ** 2) * 2.2)
gold = np.clip(gold * np.clip(vig, 0, 1) + grain * (gold > 0.05), 0, 1)
pur = np.clip(pur, 0, 1)

# ---------- 7. 三色有序抖动 ----------
def bayer(n):
    m = np.array([[0, 2], [3, 1]])
    while m.shape[0] < n:
        m = np.block([[4 * m, 4 * m + 2], [4 * m + 3, 4 * m + 1]])
    return (m + 0.5) / (n * n)


B = bayer(8)
th = B[((yy // PX) % 8).astype(int), ((xx // PX) % 8).astype(int)]
iy = (yy // PX * PX).astype(int); ix = (xx // PX * PX).astype(int)
gb, pb = gold[iy, ix], pur[iy, ix]
out = np.empty((H, W, 3), np.uint8); out[:] = BG
out[gb > th] = GD
out[pb > th] = PU
Image.fromarray(out).save(f"shrine_s{SEED}.png")
print("ok", SEED, "黑占比 %.2f" % (1 - ((gb > th) | (pb > th)).mean()))
