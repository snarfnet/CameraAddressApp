from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import shutil

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "screenshots"
ASSETS = ROOT / "CameraAddressApp" / "Assets.xcassets"
EMERGENCY = ASSETS / "GeneratedEmergency.imageset" / "generated_emergency.png"
STREET = ASSETS / "GeneratedStreet.imageset" / "generated_street.png"
PHONE = ASSETS / "GeneratedPhone.imageset" / "generated_phone.png"
SAVE = ASSETS / "GeneratedSave.imageset" / "generated_save.png"

SIZES = {
    "67": (1290, 2796),
    "61": (1179, 2556),
}

COPY_ALIASES = {
    "screenshot_iphone67_1.png": "iphone67_ja_1.png",
    "screenshot_iphone67_2.png": "iphone67_ja_2.png",
    "screenshot_iphone67_3.png": "iphone67_ja_3.png",
    "screenshot_iphone61_1.png": "iphone61_ja_1.png",
    "screenshot_iphone61_2.png": "iphone61_ja_2.png",
    "screenshot_iphone61_3.png": "iphone61_ja_3.png",
}

TEXT = {
    "ja": [
        {
            "eyebrow": "CameraAddress",
            "title": "事故・緊急時も場所を写真に",
            "body": "住所、郵便番号、近くの目印を一緒に記録。あとから状況を説明しやすく。",
            "address": "東京都新宿区西新宿2-8-1",
            "landmark": "都庁前駅まで約120m",
            "postal": "163-8001",
            "source": EMERGENCY,
        },
        {
            "eyebrow": "EMERGENCY RECORD",
            "title": "現場の住所をすぐ記録",
            "body": "事故、災害、トラブル時の写真に、現在地の情報を見やすく残せます。",
            "address": "東京都新宿区西新宿2-8-1",
            "landmark": "都庁前駅まで約120m",
            "postal": "163-8001",
            "source": PHONE,
        },
        {
            "eyebrow": "SAVE & SHARE",
            "title": "あとから共有しやすい",
            "body": "住所スタンプ付きの写真を保存。報告、連絡、記録に使いやすい一枚へ。",
            "address": "東京都新宿区西新宿2-8-1",
            "landmark": "都庁前駅まで約120m",
            "postal": "163-8001",
            "source": SAVE,
        },
    ],
    "en": [
        {
            "eyebrow": "CameraAddress",
            "title": "Record the place in urgent moments",
            "body": "Capture the address, postal code, and nearby landmark with the photo.",
            "address": "2-8-1 Nishi-Shinjuku, Tokyo",
            "landmark": "About 120 m from Tochomae Station",
            "postal": "163-8001",
            "source": EMERGENCY,
        },
        {
            "eyebrow": "EMERGENCY RECORD",
            "title": "Location details, ready fast",
            "body": "Helpful for accidents, trouble reports, field notes, and quick location records.",
            "address": "2-8-1 Nishi-Shinjuku, Tokyo",
            "landmark": "About 120 m from Tochomae Station",
            "postal": "163-8001",
            "source": PHONE,
        },
        {
            "eyebrow": "SAVE & SHARE",
            "title": "Easy to explain later",
            "body": "Save photos with a clean address stamp for reports, contact, and records.",
            "address": "2-8-1 Nishi-Shinjuku, Tokyo",
            "landmark": "About 120 m from Tochomae Station",
            "postal": "163-8001",
            "source": SAVE,
        },
    ],
}


def font(size, bold=False):
    candidates = [
        r"C:\Windows\Fonts\NotoSansJP-VF.ttf",
        r"C:\Windows\Fonts\YuGothB.ttc" if bold else r"C:\Windows\Fonts\YuGothM.ttc",
        r"C:\Windows\Fonts\meiryob.ttc" if bold else r"C:\Windows\Fonts\meiryo.ttc",
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def cover_image(path, size, anchor_y=0.5):
    im = Image.open(path).convert("RGB")
    w, h = im.size
    tw, th = size
    scale = max(tw / w, th / h)
    nw, nh = int(w * scale), int(h * scale)
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    x0 = (nw - tw) // 2
    y0 = int((nh - th) * anchor_y)
    y0 = max(0, min(y0, nh - th))
    return im.crop((x0, y0, x0 + tw, y0 + th))


def gradient(size, top, bottom):
    w, h = size
    im = Image.new("RGBA", size)
    px = im.load()
    for y in range(h):
        t = y / max(h - 1, 1)
        color = tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(4))
        for x in range(w):
            px[x, y] = color
    return im


def rounded(draw, xy, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def draw_text_wrap(draw, text, xy, max_width, fnt, fill, line_gap=10, max_lines=None):
    x, y = xy
    lines = []
    current = ""
    for ch in text:
        test = current + ch
        if draw.textlength(test, font=fnt) <= max_width or not current:
            current = test
        else:
            lines.append(current)
            current = ch
    if current:
        lines.append(current)
    if max_lines:
        lines = lines[:max_lines]
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill)
        y += fnt.size + line_gap
    return y


def draw_address_card(draw, x, y, w, scale, copy, compact=False):
    pad = int(34 * scale)
    radius = int(34 * scale)
    title = font(int(26 * scale), True)
    address = font(int((38 if not compact else 30) * scale), True)
    small = font(int(24 * scale), True)
    body = font(int(22 * scale), False)

    card_h = int((260 if not compact else 218) * scale)
    rounded(draw, (x, y, x + w, y + card_h), radius, (7, 18, 24, 222), (255, 255, 255, 58), max(1, int(2 * scale)))
    draw.text((x + pad, y + pad), "ADDRESS STAMP", font=title, fill=(105, 234, 212, 255))
    postal = "〒" + copy["postal"]
    postal_w = draw.textlength(postal, font=small)
    draw.text((x + w - pad - postal_w, y + pad + 2), postal, font=small, fill=(255, 255, 255, 215))
    yy = y + pad + int(48 * scale)
    yy = draw_text_wrap(draw, copy["address"], (x + pad, yy), w - pad * 2, address, (255, 255, 255, 255), int(8 * scale), 2)
    chip_h = int(48 * scale)
    chip_w = int(draw.textlength(copy["landmark"], font=body) + 44 * scale)
    rounded(draw, (x + pad, y + card_h - pad - chip_h, x + pad + chip_w, y + card_h - pad), int(24 * scale), (255, 255, 255, 32))
    draw.text((x + pad + int(22 * scale), y + card_h - pad - chip_h + int(10 * scale)), copy["landmark"], font=body, fill=(253, 230, 138, 255))


def draw_phone_chrome(draw, w, h, scale):
    draw.rounded_rectangle((int(70 * scale), int(80 * scale), w - int(70 * scale), h - int(80 * scale)), radius=int(60 * scale), outline=(255, 255, 255, 38), width=int(2 * scale))
    draw.rounded_rectangle((w // 2 - int(95 * scale), int(52 * scale), w // 2 + int(95 * scale), int(84 * scale)), radius=int(16 * scale), fill=(0, 0, 0, 120))


def draw_camera_ui(im, copy, lead=False):
    w, h = im.size
    scale = w / 1290
    overlay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    draw_phone_chrome(d, w, h, scale)
    overlay.alpha_composite(gradient((w, h), (0, 0, 0, 138), (0, 0, 0, 176)), (0, 0))
    d = ImageDraw.Draw(overlay)

    left = int(88 * scale)
    top = int(145 * scale)
    pill_h = int(74 * scale)
    rounded(d, (left, top, left + int(420 * scale), top + pill_h), int(38 * scale), (4, 13, 18, 166), (255, 255, 255, 40))
    d.ellipse((left + int(22 * scale), top + int(18 * scale), left + int(58 * scale), top + int(54 * scale)), fill=(239, 68, 68, 255))
    label = "緊急時の位置記録" if "東京都" in copy["address"] else "Emergency location"
    d.text((left + int(76 * scale), top + int(13 * scale)), label, font=font(int(24 * scale), True), fill=(255, 255, 255, 245))
    d.text((left + int(76 * scale), top + int(41 * scale)), "〒" + copy["postal"], font=font(int(19 * scale), True), fill=(255, 255, 255, 172))

    corner = int(95 * scale)
    inset = int(112 * scale)
    y1, y2 = int(715 * scale), int(1800 * scale)
    for sx in [inset, w - inset - corner]:
        d.line((sx, y1, sx + corner, y1), fill=(255, 255, 255, 125), width=int(5 * scale))
        d.line((sx, y2, sx + corner, y2), fill=(255, 255, 255, 110), width=int(5 * scale))
    d.line((inset, y1, inset, y1 + corner), fill=(255, 255, 255, 125), width=int(5 * scale))
    d.line((w - inset, y1, w - inset, y1 + corner), fill=(255, 255, 255, 125), width=int(5 * scale))
    d.line((inset, y2 - corner, inset, y2), fill=(255, 255, 255, 110), width=int(5 * scale))
    d.line((w - inset, y2 - corner, w - inset, y2), fill=(255, 255, 255, 110), width=int(5 * scale))

    card_w = w - int(150 * scale)
    draw_address_card(d, int(75 * scale), h - int(610 * scale), card_w, scale, copy)

    dock_y = h - int(295 * scale)
    rounded(d, (int(90 * scale), dock_y, w - int(90 * scale), dock_y + int(150 * scale)), int(56 * scale), (5, 13, 18, 170), (255, 255, 255, 50), int(2 * scale))
    cx = w // 2
    cy = dock_y + int(75 * scale)
    d.ellipse((cx - int(66 * scale), cy - int(66 * scale), cx + int(66 * scale), cy + int(66 * scale)), fill=(255, 255, 255, 255), outline=(255, 255, 255, 255), width=int(4 * scale))
    d.ellipse((cx - int(40 * scale), cy - int(40 * scale), cx + int(40 * scale), cy + int(40 * scale)), fill=(16, 24, 32, 255))
    d.rounded_rectangle((int(148 * scale), dock_y + int(36 * scale), int(226 * scale), dock_y + int(114 * scale)), radius=int(22 * scale), fill=(255, 255, 255, 38), outline=(255, 255, 255, 64), width=int(2 * scale))
    d.rounded_rectangle((w - int(226 * scale), dock_y + int(36 * scale), w - int(148 * scale), dock_y + int(114 * scale)), radius=int(22 * scale), fill=(255, 255, 255, 38), outline=(255, 255, 255, 64), width=int(2 * scale))

    if lead:
        title_font = font(int(62 * scale), True)
        body_font = font(int(28 * scale), True)
        y = int(300 * scale)
        d.text((int(92 * scale), y), copy["title"], font=title_font, fill=(255, 255, 255, 255))
        draw_text_wrap(d, copy["body"], (int(92 * scale), y + int(88 * scale)), int(890 * scale), body_font, (255, 255, 255, 220), int(12 * scale), 3)

    return Image.alpha_composite(im.convert("RGBA"), overlay).convert("RGB")


def draw_photo_panel(base, source, box, scale, copy, with_stamp=True):
    x1, y1, x2, y2 = box
    photo = cover_image(source, (x2 - x1, y2 - y1), 0.56).filter(ImageFilter.GaussianBlur(radius=0.15))
    mask = Image.new("L", photo.size, 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle((0, 0, photo.width, photo.height), radius=int(46 * scale), fill=255)
    base.paste(photo.convert("RGBA"), (x1, y1), mask)
    d = ImageDraw.Draw(base)
    d.rounded_rectangle(box, radius=int(46 * scale), outline=(255, 255, 255, 48), width=int(2 * scale))
    if with_stamp:
        draw_address_card(d, x1 + int(36 * scale), y2 - int(300 * scale), (x2 - x1) - int(72 * scale), scale, copy, True)


def draw_feature_screen(size, copy, step):
    w, h = size
    scale = w / 1290
    base = Image.new("RGBA", size, (9, 20, 25, 255))
    bg = cover_image(copy["source"], size, 0.5).filter(ImageFilter.GaussianBlur(radius=7))
    base.alpha_composite(bg.convert("RGBA"), (0, 0))
    base.alpha_composite(gradient(size, (0, 0, 0, 190), (3, 30, 28, 226)), (0, 0))
    d = ImageDraw.Draw(base)

    x = int(92 * scale)
    y = int(250 * scale)
    d.text((x, y), copy["eyebrow"], font=font(int(25 * scale), True), fill=(94, 234, 212, 255))
    draw_text_wrap(d, copy["title"], (x, y + int(70 * scale)), w - x * 2, font(int(66 * scale), True), (255, 255, 255, 255), int(10 * scale), 2)
    draw_text_wrap(d, copy["body"], (x, y + int(245 * scale)), w - x * 2, font(int(31 * scale), False), (232, 241, 239, 232), int(14 * scale), 3)

    if step == 2:
        draw_photo_panel(base, copy["source"], (int(115 * scale), int(1020 * scale), w - int(115 * scale), int(1785 * scale)), scale, copy, False)
        draw_address_card(d, int(92 * scale), int(1830 * scale), w - int(184 * scale), scale, copy)
        cx, cy = w // 2, int(890 * scale)
        d.ellipse((cx - int(88 * scale), cy - int(88 * scale), cx + int(88 * scale), cy + int(88 * scale)), outline=(94, 234, 212, 245), width=int(7 * scale))
        d.line((cx, cy - int(120 * scale), cx, cy + int(120 * scale)), fill=(94, 234, 212, 220), width=int(4 * scale))
        d.line((cx - int(120 * scale), cy, cx + int(120 * scale), cy), fill=(94, 234, 212, 220), width=int(4 * scale))
    else:
        draw_photo_panel(base, copy["source"], (int(130 * scale), int(1030 * scale), w - int(130 * scale), int(1845 * scale)), scale, copy, True)
        cx, cy = w // 2, int(860 * scale)
        d.ellipse((cx - int(78 * scale), cy - int(78 * scale), cx + int(78 * scale), cy + int(78 * scale)), outline=(94, 234, 212, 245), width=int(6 * scale))
        d.rounded_rectangle((cx - int(34 * scale), cy - int(34 * scale), cx + int(34 * scale), cy + int(34 * scale)), radius=int(10 * scale), outline=(94, 234, 212, 245), width=int(5 * scale))

    brand = "CameraAddress"
    d.text((w // 2 - d.textlength(brand, font=font(int(22 * scale), True)) / 2, h - int(145 * scale)), brand, font=font(int(22 * scale), True), fill=(255, 255, 255, 170))
    return base.convert("RGB")


def generate():
    OUT.mkdir(exist_ok=True)
    for size_key, size in SIZES.items():
        for lang, copies in TEXT.items():
            first = draw_camera_ui(cover_image(copies[0]["source"], size, 0.44), copies[0], True)
            first.save(OUT / f"iphone{size_key}_{lang}_1.png", optimize=True)
            draw_feature_screen(size, copies[1], 2).save(OUT / f"iphone{size_key}_{lang}_2.png", optimize=True)
            draw_feature_screen(size, copies[2], 3).save(OUT / f"iphone{size_key}_{lang}_3.png", optimize=True)

    for alias, source in COPY_ALIASES.items():
        shutil.copyfile(OUT / source, OUT / alias)


if __name__ == "__main__":
    generate()
    print(f"Generated screenshots in {OUT}")
