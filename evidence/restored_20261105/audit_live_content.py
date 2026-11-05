"""Codex source audit, explicitly separate from human grading."""
import json,csv
from pathlib import Path
BASE=Path(__file__).resolve().parent/'faiss_live_final_13'
rows=[json.loads(s) for s in (BASE/'results.jsonl').read_text(encoding='utf-8').splitlines()]
assert len(rows)==13,'Audit the completed batch, not a selected subset'
notes={
 'rag_01':('mostly_supported','partial','Đúng tác dụng giảm căng thẳng/nhịp tim/huyết áp. Câu trả lời rút gọn bước não gửi thông điệp đến toàn cơ thể; các quote bị lặp và có đoạn câu chưa hoàn chỉnh.'),
 'rag_02':('supported','direct','Vị trí hai tay khớp trang 2; có trích nguyên câu hỗ trợ trực tiếp.'),
 'rag_03':('supported','direct','Giữ đúng 3–10 lần, không đổi đơn vị; quote trang 2 có đủ con số.'),
 'rag_04':('supported','direct','Giữ 4/7/8 là số đếm, không tự đổi sang giây; ba quote trang 3 tương ứng từng bước.'),
 'rag_05':('supported','insufficient','Đáp án nằm ngửa/co đầu gối khớp tham chiếu, nhưng quote được chọn kết thúc ở bất kỳ vị trí; chưa trực tiếp chứng minh tư thế khi mới tập.'),
 'rag_06':('incorrect_refusal','none','Model báo thiếu thông tin dù ngữ cảnh đã truy xuất có 3–5 phút. Hoàn tất kỹ thuật và retrieval tìm đúng đoạn không đồng nghĩa trả lời đúng.'),
 'rag_07':('supported','insufficient','Đáp án nâng đầu sau cùng khớp tham chiếu; quote dừng ở bằng cách lăn, thiếu phần nâng đầu ở dòng tiếp theo.'),
 'rag_08':('supported','direct_with_noise','Đúng 10–20 phút, có một quote trực tiếp; quote bổ sung chỉ nêu bài tập mất vài phút nên không cần thiết.'),
 'new_01':('supported','direct','Mặc quần áo thoải mái, khớp nguyên văn trang 2.'),
 'new_03':('supported','incomplete','Đáp án giữ ngực không di chuyển đúng tham chiếu. Quote dừng ở Giữ nguyên vị trí của, thiếu từ ngực nằm ở phần kế tiếp.'),
 'new_06':('supported','direct','Nhắm mắt, khớp câu trích trực tiếp trang 5.'),
 'negative_01':('expected_refusal','not_applicable','PDF không có dân số Việt Nam 2026; model từ chối, không đưa số liệu.'),
 'negative_02':('expected_refusal','not_applicable','PDF không có học phí đại học năm 2026; model từ chối, không bịa số liệu.')}
audits=[]
for r in rows:
 content,citation,note=notes[r['id']]
 if r['id'].startswith('negative_'):assert r['body']['status']=='refused'
 if r['id']=='rag_06':assert r['body']['status']=='refused'
 audits.append({'id':r['id'],'trace_id':r['body']['trace_id'],'http_status':r['http_status'],
   'technical_completion':r['technical_completion'],'question':r['question'],
   'reference':r['reference'],'actual_response':r['body']['response'],
   'content_assessment':content,'citation_assessment':citation,'note':note,
   'reviewer':'Codex AI source audit','human_score':None})
result={'method':'AI comparison of full recorded response, reference and retrieved PDF contexts; not a human grade or independent evaluation',
 'scope':'All 13 cases in one completed batch; no cherry-picking',
 'human_grades_generated':False,'clinical_validation':False,'rows':audits}
(BASE/'content_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
with (BASE/'content_audit.csv').open('w',encoding='utf-8-sig',newline='') as f:
 writer=csv.DictWriter(f,fieldnames=list(audits[0]));writer.writeheader();writer.writerows(audits)
print(json.dumps({'audited':len(audits),'human_scores':0,'incorrect_refusal':['rag_06'],
 'citations_not_direct_or_incomplete':['rag_01','rag_05','rag_07','new_03']},ensure_ascii=False))
