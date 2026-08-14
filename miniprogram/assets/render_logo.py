#!/usr/bin/env python3
# 星鉴人格 Logo（B2 流光环）渲染脚本
# 4 倍超采样抗锯齿，输出 1024px PNG：透明底（应用内）+ 暖底（小程序图标）
import math
import os
from PIL import Image, ImageDraw

VIOLET = (139, 92, 246)
CORAL = (242, 84, 91)
ORANGE = (245, 158, 11)
BLUE = (59, 158, 216)
WARM_BG = (250, 247, 242)

SIZE = 1024
SS = 4          # 超采样倍率
W = SIZE * SS   # 工作画布 4096
K = W / 200.0   # viewBox 200 → 4096

def lerp(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))

def pt(deg, r=70.0, cx=100.0, cy=100.0):
    rad = math.radians(deg)
    return ((cx + r * math.cos(rad)) * K, (cy + r * math.sin(rad)) * K)

def stamp_arc(draw, deg_from, deg_to, c_from, c_to, r=70.0, w=13.0):
    """沿圆弧逐点盖章（圆点即圆角线帽），颜色从 c_from 渐变到 c_to"""
    step = 0.15 if deg_to > deg_from else -0.15
    total = abs(deg_to - deg_from)
    n = int(total / 0.15) + 1
    rad = (w / 2) * K
    for i in range(n + 1):
        t = i / n
        deg = deg_from + (deg_to - deg_from) * t
        x, y = pt(deg, r)
        col = lerp(c_from, c_to, t)
        draw.ellipse([x - rad, y - rad, x + rad, y + rad], fill=col)

def cubic(p0, p1, p2, p3, n=64):
    pts = []
    for i in range(n):
        t = i / n
        mt = 1 - t
        x = mt**3 * p0[0] + 3 * mt**2 * t * p1[0] + 3 * mt * t**2 * p2[0] + t**3 * p3[0]
        y = mt**3 * p0[1] + 3 * mt**2 * t * p1[1] + 3 * mt * t**2 * p2[1] + t**3 * p3[1]
        pts.append((x * K, y * K))
    return pts

def make_mark(with_bg):
    img = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # 四段流光弧（颜色首尾相接：紫→红→橙→蓝→紫）
    # 参数间隙 15°：圆角线帽每端吃掉 ~5.3°，最终视觉间隙 ~4.5°
    stamp_arc(d, -127.5, -52.5, VIOLET, CORAL)  # 上弧
    stamp_arc(d, -37.5, 37.5, CORAL, ORANGE)    # 右弧
    stamp_arc(d, 52.5, 127.5, ORANGE, BLUE)     # 下弧
    stamp_arc(d, 217.5, 142.5, VIOLET, BLUE)    # 左弧（经 180° 下行）

    # 中心渐变星（先画形 mask，再贴对角渐变）
    star = []
    segs = [
        ((100, 68), (104, 86), (114, 96), (132, 100)),
        ((132, 100), (114, 104), (104, 114), (100, 132)),
        ((100, 132), (96, 114), (86, 104), (68, 100)),
        ((68, 100), (86, 96), (96, 86), (100, 68)),
    ]
    for s in segs:
        star.extend(cubic(*s))
    mask = Image.new('L', (W, W), 0)
    ImageDraw.Draw(mask).polygon(star, fill=255)

    # 对角线性渐变（bbox 68,68-132,132，左上珊瑚 → 右下紫罗兰）
    ix0, iy0, ix1, iy1 = int(68 * K), int(68 * K), int(132 * K), int(132 * K)
    gw, gh = ix1 - ix0, iy1 - iy0
    mid = lerp(CORAL, VIOLET, 0.5)
    tiny = Image.new('RGB', (2, 2))
    tiny.putpixel((0, 0), CORAL); tiny.putpixel((1, 0), mid)
    tiny.putpixel((0, 1), mid);   tiny.putpixel((1, 1), VIOLET)
    grad = tiny.resize((gw, gh), Image.BICUBIC).convert('RGBA')
    img.paste(grad, (ix0, iy0), mask.crop((ix0, iy0, ix1, iy1)))

    img = img.resize((SIZE, SIZE), Image.LANCZOS)
    if with_bg:
        bg = Image.new('RGBA', (SIZE, SIZE), WARM_BG + (255,))
        bg.alpha_composite(img)
        return bg
    return img

mark = make_mark(with_bg=False)
mark.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png"))
icon = make_mark(with_bg=True)
icon.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo-icon.png"))
print("rendered: logo.png / logo-icon.png")
