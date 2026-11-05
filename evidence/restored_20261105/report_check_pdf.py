"""Compare native PDF exports and render changed deployment/evidence pages."""
import hashlib
import json
from pathlib import Path
import pymupdf

BASE = Path(__file__).resolve().parent
ANCHORS = {
    'chapter12': 'Chương 12: Mô tả',
    'chapter13': 'Chương 13: Triển khai',
    'historical_evaluation': '13.1 Phạm vi',
    'new_verification': '13.12 Kiểm tra',
    'chapter14': 'Chương 14: Đánh giá',
    'chapter15': 'Chương 15: Hướng',
    'appendix_a': 'Phụ lục A Hands-on',
    'appendix_b': 'Phụ lục B Nhật ký',
}


def describe(path):
    doc = pymupdf.open(path)
    texts = [page.get_text() for page in doc]
    anchors = {name: [i+1 for i, text in enumerate(texts) if value in text]
               for name, value in ANCHORS.items()}
    clipped = []
    for i, page in enumerate(doc):
        for block in page.get_text('dict')['blocks']:
            for line in block.get('lines', []):
                for span in line['spans']:
                    x0, y0, x1, y1 = span['bbox']
                    if x0 < -1 or y0 < -1 or x1 > page.rect.width+1 or y1 > page.rect.height+1:
                        clipped.append({'page': i+1, 'text': span['text'], 'bbox': span['bbox']})
    return doc, texts, {'pdf': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                        'pages': len(doc), 'anchors': anchors, 'text_spans_outside_page': clipped}


def main():
    old_doc, old_text, old = describe(BASE/'report_current.pdf')
    new_doc, new_text, new = describe(BASE/'report_restored_candidate.pdf')
    # The new result section is intentionally allowed to add pages.
    identical = [i+1 for i in range(min(len(old_text),len(new_text))) if old_text[i] == new_text[i]]
    selected = set()
    for key in ('chapter12', 'chapter13', 'historical_evaluation', 'new_verification', 'chapter14', 'appendix_b'):
        if new['anchors'][key]:
            start = new['anchors'][key][-1]-1
            selected.update(range(max(0,start-1),min(len(new_doc),start+2)))
    for index in sorted(selected):
        new_doc[index].get_pixmap(matrix=pymupdf.Matrix(1.15,1.15)).save(BASE/f'report_page_{index+1:03}.png')
    (BASE/'report_pdf_text.txt').write_text('\n\n'.join(f'PAGE {i+1}\n'+text for i,text in enumerate(new_text)),'utf-8')
    result = {
        'baseline': old, 'candidate': new,
        'same_physical_page_text': identical,
        'rendered_candidate_pages': [i+1 for i in sorted(selected)],
        'no_candidate_text_outside_page': not new['text_spans_outside_page'],
        'manual_visual_review_required': True,
        'no_pixel_equality_claim': True,
        'new_measurements_in_report': 'Only source/test owner verified facts; draft marker must be absent before publishing',
    }
    (BASE/'report_pdf_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps(result,ensure_ascii=False))


if __name__ == '__main__':
    main()
