"""Read printed PDF page numbers and propose precise cached TOC updates."""
import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile
import pymupdf

BASE = Path(__file__).resolve().parent
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'


def normalize(text):
    text = unicodedata.normalize('NFD', text.casefold()).replace('đ','d')
    return ''.join(char for char in text if char.isalnum() and unicodedata.category(char) != 'Mn')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    pdf = pymupdf.open(BASE/'report_restored_candidate.pdf')
    render = json.loads((BASE/'report_render_candidate.json').read_text('utf-8'))
    assert render['input_sha256'] == hashlib.sha256((BASE/'report_restored_candidate.docx').read_bytes()).hexdigest(), 'Render the current candidate first'
    pages = []
    for index, page in enumerate(pdf):
        footers = [line.strip() for line in page.get_text(clip=pymupdf.Rect(0,page.rect.height-75,page.rect.width,page.rect.height)).splitlines()]
        numbers = [int(text) for text in footers if re.fullmatch(r'\d+',text)]
        pages.append({'physical':index+1,'printed':numbers[-1] if numbers else None,'text':normalize(page.get_text())})
    xml = ZipFile(BASE/'report_current.docx').read('word/document.xml')
    paragraphs = list(ET.fromstring(xml).iter(W+'p'))
    changes = {}
    checks = []
    previous_physical_page = 4
    for index in range(30,70):
        texts = [node.text or '' for node in paragraphs[index].iter(W+'t')]
        if len(texts) != 2 or not texts[-1].isdigit():
            checks.append({'index':index,'skipped':texts})
            continue
        title = 'a) Cấu trúc thư mục ứng dụng' if index == 62 else texts[0]
        key = normalize(title)
        hits = [page for page in pages if key in page['text'] and page['physical'] >= previous_physical_page]
        if not hits or hits[0]['printed'] is None:
            checks.append({'index':index,'title':title,'resolved':False})
            continue
        hit = hits[0]
        previous_physical_page = hit['physical']
        checks.append({'index':index,'title':title,'resolved':True,'printed_page':hit['printed'],'physical_page':hit['physical']})
        fields = {}
        if hit['printed'] != int(texts[-1]): fields['page'] = hit['printed']
        if title != texts[0]: fields['title'] = title
        if fields: changes[str(index)] = fields
    appendix_hits = [page for page in pages if normalize('Phụ lục B Nhật ký chỉnh sửa và sử dụng AI') in page['text'] and page['physical'] > 3]
    appendix_page = appendix_hits[-1]['printed'] if appendix_hits else None
    result = {'pdf_sha256':render['pdf_sha256'],'checks':checks,'toc_overrides':changes,'appendix_toc_page':appendix_page}
    (BASE/'report_toc_suggestions.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')
    if args.apply:
        facts_file = BASE/'report_verified_facts.json'
        facts = json.loads(facts_file.read_text('utf-8')) if facts_file.exists() else {}
        facts['toc_overrides'] = changes
        facts['appendix_toc_page'] = appendix_page
        facts_file.write_text(json.dumps(facts,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps(result,ensure_ascii=False))


if __name__ == '__main__':
    main()
