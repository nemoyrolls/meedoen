"""Little Memphis shapes (zigzag, bolt, speckled arcs, dot, triangle) as inline SVG.

Every shape has a black outline and a hard offset copy behind it in light "paper",
like the Yestalgia inspiration. A black shadow would vanish on our black page.
"""
import math
import random

LIME = "#B7D14B"
PINK = "#EFA9CE"
ORANGE = "#F29A55"
TEAL = "#3E8E86"
BLUE = "#6E97B5"
PAPER = "#F3F3F3"
INK = "#000"
SHADOW = (6, 6)


def _svg(width, height, body, style=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
            f'width="{width}" height="{height}" style="overflow:visible;{style}">{body}</svg>')


def _with_shadow(shape):
    """shape(fill, stroke) -> svg elements. Draws the paper copy, then the real one."""
    dx, dy = SHADOW
    return (f'<g transform="translate({dx},{dy})">{shape(PAPER, PAPER)}</g>'
            f'{shape(None, INK)}')


def _confetti(cx, cy, r_in, r_out, a0, a1, count, seed):
    """Short black squiggles scattered inside a ring (or a full circle when r_in=0)."""
    rng = random.Random(seed)
    lines = []
    for _ in range(count):
        angle = math.radians(rng.uniform(a0, a1))
        radius = rng.uniform(r_in + 4, r_out - 4)
        x, y = cx + radius * math.cos(angle), cy + radius * math.sin(angle)
        tilt = rng.uniform(0, math.pi)
        dx, dy = 4 * math.cos(tilt), 4 * math.sin(tilt)
        lines.append(f'<line x1="{x - dx:.1f}" y1="{y - dy:.1f}" x2="{x + dx:.1f}" y2="{y + dy:.1f}"/>')
    return f'<g stroke="{INK}" stroke-width="2" stroke-linecap="round">{"".join(lines)}</g>'


def zigzag(color=PINK):
    points = "4,10 40,10 40,38 76,38 76,66 112,66 112,94 148,94"

    def shape(fill, stroke):
        if fill is None:
            return (f'<polyline points="{points}" fill="none" stroke="{INK}" stroke-width="22" stroke-linejoin="miter"/>'
                    f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="15" stroke-linejoin="miter"/>')
        return f'<polyline points="{points}" fill="none" stroke="{fill}" stroke-width="22" stroke-linejoin="miter"/>'
    return _svg(152, 104, _with_shadow(shape))


def bolt(color=LIME):
    points = "40,4 108,4 76,48 104,48 30,128 52,68 20,68"

    def shape(fill, stroke):
        return (f'<polygon points="{points}" fill="{fill or color}" stroke="{stroke}" '
                f'stroke-width="3.5" stroke-linejoin="round"/>')
    return _svg(112, 132, _with_shadow(shape))


def arc(color=BLUE, seed=1):
    # A thick half ring, open at the top, with confetti.
    def ring(fill, stroke):
        path = "M8,40 A62,62 0 0 0 132,40 L106,40 A36,36 0 0 1 34,40 Z"
        extra = "" if fill else _confetti(70, 40, 36, 62, 10, 170, 22, seed)
        return (f'<path d="{path}" fill="{fill or color}" stroke="{stroke}" stroke-width="3.5" '
                f'stroke-linejoin="round"/>{extra}')
    return _svg(140, 106, _with_shadow(ring))


def half_arc(color=PINK, seed=2):
    def ring(fill, stroke):
        path = "M30,6 A34,34 0 1 1 6,62 L22,52 A16,16 0 1 0 34,24 Z"
        extra = "" if fill else _confetti(40, 40, 16, 34, -120, 150, 10, seed)
        return (f'<path d="{path}" fill="{fill or color}" stroke="{stroke}" stroke-width="3" '
                f'stroke-linejoin="round"/>{extra}')
    return _svg(80, 80, _with_shadow(ring))


def dot(color=ORANGE, seed=3):
    def circle(fill, stroke):
        extra = "" if fill else _confetti(40, 40, 0, 36, 0, 360, 18, seed)
        return (f'<circle cx="40" cy="40" r="36" fill="{fill or color}" stroke="{stroke}" '
                f'stroke-width="3.5"/>{extra}')
    return _svg(80, 80, _with_shadow(circle))


def triangle(color=TEAL):
    def shape(fill, stroke):
        return (f'<polygon points="4,4 96,4 50,86" fill="{fill or color}" stroke="{stroke}" '
                f'stroke-width="3.5" stroke-linejoin="round"/>')
    return _svg(100, 90, _with_shadow(shape))


def avatar():
    """The profile picture: a lime confetti circle with a pink zigzag across it."""
    body = (
        f'<circle cx="34" cy="34" r="30" fill="{PAPER}" transform="translate(4,4)"/>'
        f'<circle cx="34" cy="34" r="30" fill="{LIME}" stroke="{INK}" stroke-width="3"/>'
        f'{_confetti(34, 34, 0, 28, 0, 360, 10, 7)}'
        f'<polyline points="14,46 24,46 24,36 34,36 34,26 44,26 44,16" fill="none" stroke="{INK}" '
        f'stroke-width="8" stroke-linejoin="miter"/>'
        f'<polyline points="14,46 24,46 24,36 34,36 34,26 44,26 44,16" fill="none" stroke="{PINK}" '
        f'stroke-width="4.5" stroke-linejoin="miter"/>'
    )
    return _svg(70, 70, body)


def decoration(layout="home"):
    """A fixed layer of shapes around the edges of the page. It never takes clicks."""
    if layout == "profile":
        # Right edge only: the left side of this page is full of content.
        items = [(triangle(), "top:90px;right:5%;transform:rotate(14deg) scale(.8)"),
                 (dot(), "top:52%;right:2%;transform:scale(.8)"),
                 (zigzag(), "bottom:6%;right:-30px;transform:rotate(-8deg) scale(.7)")]
    elif layout == "mission":
        items = [(zigzag(), "top:120px;left:calc(var(--main-left) + 16px);transform:rotate(8deg) scale(.75)"),
                 (triangle(), "top:90px;right:5%;transform:rotate(14deg) scale(.8)"),
                 (dot(), "top:55%;right:3%;transform:scale(.85)"),
                 (bolt(), "bottom:10%;left:calc(var(--main-left) + 24px);transform:rotate(-12deg) scale(.8)")]
    elif layout == "results":
        # Only one shape here, at the edge, so nothing sits on top of a card or button.
        items = [(zigzag(), "top:46%;right:-34px;transform:rotate(-8deg) scale(.7)")]
    else:
        items = [(zigzag(), "top:80px;left:calc(var(--main-left) + 12px);transform:rotate(8deg) scale(.8)"),
                 (half_arc(), "top:120px;right:10%;transform:rotate(-20deg)"),
                 (bolt(), "bottom:12%;left:calc(var(--main-left) + 20px);transform:rotate(-12deg) scale(.85)"),
                 (dot(), "top:46%;right:3%"),
                 (arc(), "bottom:-24px;right:6%;transform:rotate(-14deg)"),
                 (triangle(), "top:-18px;right:24%;transform:rotate(12deg) scale(.7)")]
    shapes_html = "".join(f'<div class="shape" style="{style}">{svg}</div>' for svg, style in items)
    return f'<div class="deco deco-{layout}">{shapes_html}</div>'
