# 暗面三部曲 · Dark Trilogy

三组颜色、三种情绪，全部用纯代码画出来。整体走**版画语言**：每张只用三色，明暗过渡全靠有序抖动的网点，像一本暗黑铜版画册。

| 幕 | 情绪 | 颜色 | 人类参考 | 状态 |
|---|---|---|---|---|
| 第一幕《糜烂》 | 黑暗、糜烂、丧 | `#000030` `#610070` `#18a69a` | 蚀刻版画 × 贝克辛斯基 | v3 玫瑰 |
| 第二幕《机械解剖》 | 爱、死亡、机器人 | `#161a24` `#9aa9ad` `#401720` | 达芬奇式解剖图版 | v1 |
| 第三幕《无声》 | 无自由、禁锢、微弱的光、挣扎、无声 | `#17252d` `#75d6f2` `#ff002b` | 皮拉内西《想象的监狱》× 卡拉瓦乔 | v1 |

## 第一幕《糜烂》

![act1](examples/act1_rose_s5.png)

```bash
pip install numpy pillow scipy
python styles/act1-decay/act1_rose.py 5
```

## 第二幕《机械解剖》

![act2](examples/act2_anatomy_s3.png)

```bash
pip install numpy pillow scipy
python styles/act2-anatomy/act2_anatomy.py 3
```

FIG. II《穿心》：被剑扎穿的心、天使羽翼、玫瑰

![act2-fig2](examples/act2_pierced_s11.png)

```bash
python styles/act2-anatomy/act2_pierced.py 11
```

## 第三幕《无声》

![act3](examples/act3_silence_s7.png)

FIG. II《蔓延》：光更弱，红线从空笼爬满墙、顶和镜头前的栏杆

![act3 fig2](examples/act3_veins_s7.png)

```bash
pip install numpy pillow
python styles/act3-silence/act3_silence.py 7   # 参数是随机种子
```

## 结构
- `SKILL.md` — skill 主体：共用底层规则、三幕定义、路由、交付
- `styles/<幕>/` — 每一幕的代码和技法说明
- `examples/` — 示例图

---
by 绮思 & 澜
