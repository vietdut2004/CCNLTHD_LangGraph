from pathlib import Path
from io import BytesIO
import json
from docx import Document
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(r'C:\Users\Admin\Downloads\Các báo cáo cần nôp')
OUT = ROOT / 'report_revision' / 'individual_assets'
OUT.mkdir(exist_ok=True)
items = []
for f in sorted(SRC.glob('BÁO CÁO CÁ NHÂN*.docx')):
    d = Document(f)
    sid = f.stem.split('_')[1]
    data = []
    for i, p in enumerate(d.paragraphs):
        for j, blip in enumerate(p._p.xpath('.//a:blip')):
            rid = blip.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
            part = d.part.related_parts[rid]
            im = Image.open(BytesIO(part.blob)).convert('RGB')
            im.save(OUT / f'{sid}_p{i}_{j}.png')
            data.append({'paragraph': i, 'rid': rid, 'size': im.size})
            if i > 15:
                items.append((f'{sid} | paragraph {i}', im))
    print(sid, json.dumps(data))
canvas = Image.new('RGB', (1300, ((len(items)+1)//2)*440), '#dddddd')
dr = ImageDraw.Draw(canvas)
for n, (label, im) in enumerate(items):
    x, y = (n % 2)*650, (n//2)*440
    im.thumbnail((630, 390))
    canvas.paste(im, (x+10, y+35))
    dr.text((x+10,y+10), label, fill='black', font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18))
canvas.save(OUT / 'original_images_contact.png')
