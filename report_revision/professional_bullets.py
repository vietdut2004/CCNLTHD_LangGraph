"""Replace geometric bullet glyphs without changing report text or numbered lists."""
from __future__ import annotations

import json
import shutil
import zipfile
from collections import Counter
from pathlib import Path

from lxml import etree

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
NS = {'w': W}
VAL = f'{{{W}}}val'


def apply_bullet_style(root):
    changes = Counter()
    for level in root.findall('.//w:lvl', NS):
        fmt = level.find('w:numFmt', NS)
        marker = level.find('w:lvlText', NS)
        if fmt is None or marker is None or fmt.get(VAL) != 'bullet':
            continue
        old = marker.get(VAL)
        new = '–' if old in {'●', '○', '■', '•', '◦', '▪', '+', '-'} else old
        if new == old:
            continue
        marker.set(VAL, new)
        changes[f'{old} → {new}'] += 1
        # Use a text font, avoiding symbol-font substitutions for the dash.
        props = level.find('w:rPr', NS)
        if props is None:
            props = etree.SubElement(level, f'{{{W}}}rPr')
        fonts = props.find('w:rFonts', NS)
        if fonts is None:
            fonts = etree.Element(f'{{{W}}}rFonts')
            props.insert(0, fonts)
        for name in ['ascii', 'hAnsi', 'eastAsia', 'cs']:
            fonts.set(f'{{{W}}}{name}', 'Times New Roman')
        for name in ['asciiTheme', 'hAnsiTheme', 'eastAsiaTheme', 'cstheme']:
            fonts.attrib.pop(f'{{{W}}}{name}', None)
    return dict(changes)


def main():
    here = Path(__file__).resolve().parent
    report = here.parent / 'Bao_cao_nhom_15_LangGraph_day_du.docx'
    output = here.parent / 'Bao_cao_nhom_15_LangGraph_trinh_bay_chuyen_nghiep.docx'
    backups = here / 'backups'
    backups.mkdir(exist_ok=True)
    for path in [report, report.with_suffix('.pdf')]:
        backup = backups / (path.stem + '_truoc_doi_ky_hieu' + path.suffix)
        if path.exists() and not backup.exists():
            shutil.copy2(path, backup)
    temp = output.with_name(output.stem + '.formatting.tmp.docx')
    with zipfile.ZipFile(report) as src, zipfile.ZipFile(temp, 'w') as out:
        before = etree.fromstring(src.read('word/numbering.xml'))
        changes = apply_bullet_style(before)
        xml = etree.tostring(before, encoding='UTF-8', xml_declaration=True, standalone=True)
        for entry in src.infolist():
            out.writestr(entry, xml if entry.filename == 'word/numbering.xml' else src.read(entry.filename))
    temp.replace(output)
    (here / 'bullet_formatting_changes.json').write_text(
        json.dumps({'report': str(output), 'definition_changes': changes}, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )
    print(json.dumps(changes, ensure_ascii=False))
    print(output)


if __name__ == '__main__':
    main()
