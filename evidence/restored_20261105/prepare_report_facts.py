"""Use completed real logs only; never create a model response or human grade."""
import json, subprocess
from pathlib import Path
import xml.etree.ElementTree as ET

BASE=Path(__file__).resolve().parent
ROOT=BASE.parent/'CCNLTHD_LangGraph'
UI_RUN='live_conversation_2026-11-05T16-33-55-604Z'
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def save(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
manifest=read(ROOT/'docs/RESTORED_RUNTIME_IDENTITY.json')
graph=manifest['identity']['graph_id']
summary=read(BASE/'faiss_live_final_13/summary.json')
assert summary['n']==summary['planned']==13 and summary['fixture'] is False
ui=read(BASE/'ui_restore'/UI_RUN/'LIVE_CAPTURE_REPORT.json')
records=read(BASE/'ui_restore'/UI_RUN/'requests_responses.json')
assert len(records)==3 and all(r['response']['graph_id']==graph for r in records)
assert [r['response']['route'] for r in records]==['rag','answer','web']
assert all(r['http_status']==200 and r['response']['status']=='ok' for r in records)
suite=ET.parse(BASE/'unit_tests_light_final.xml').getroot()
nodes=list(suite.iter('testcase'))
skips=sum(n.find('skipped') is not None for n in nodes)
assert len(nodes)-skips==67 and skips==2
commit=subprocess.check_output(['git','-c',f'safe.directory={ROOT.as_posix()}','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
assert commit!=manifest['base_commit'],'Commit the reviewed source before final report'
tokens=sum(r['response']['usage']['total_tokens'] for r in records)
latencies=[round(r['latency_ms_browser']/1000,3) for r in records]
mean=summary['latency_ms']['mean']/1000
p50=summary['latency_ms']['p50']/1000
p95=summary['latency_ms']['p95']/1000
facts={
 'status':'verified',
 'paragraph_overrides':{
  '1076':f'B1: Lấy source tại repository vietdut2004/CCNLTHD_LangGraph, commit {commit[:12]}. Bản này được kiểm tra ngày 05/11/2026; mã nhận diện runtime là {graph}. Commit đầy đủ và hash từng tệp nằm trong hồ sơ bàn giao.',
  '1239':'Các phần trên ghi lại kết quả theo từng lần thử, kể cả lỗi và những câu bị từ chối. Bản chạy lại với giao diện hội thoại và FAISS được trình bày riêng ở mục 13.12 để người đọc có thể đối chiếu mà không nhầm với số liệu cũ.'},
 'new_section_paragraphs':[
  '13.12 Kết quả chạy lại sau khi khôi phục giao diện và FAISS',
  f'Ngày 05/11/2026, nhóm đối chiếu bản báo cáo hiện hành với source sau khi pull main (mốc ban đầu 78b118f). Bản đã kiểm tra được chốt tại commit {commit[:12]}, runtime {graph}. Phần sửa tập trung vào giao diện hội thoại, truy xuất bằng embedding và FAISS, và bước model chọn công cụ. Mô hình sinh vẫn là openai/gpt-oss-20b; Stress.pdf giữ nguyên nội dung và hash SHA-256 91c16764898a88f26bb73706d1188afd3e3631f8a462c08fd76130a64ebc736a.',
  'Giao diện được dựng lại theo ảnh đã có trong báo cáo: thanh bên có logo SGU, nền tím nhạt, tin nhắn trắng/hồng và ô nhập ở cuối màn hình. Source HTML của ảnh cũ không có trong repository đã lưu, nên phần bố cục được khôi phục từ ảnh; logo cũng lấy từ ảnh đó. Giao diện mới gửi yêu cầu thật đến /chatbot, giữ mã phiên qua các lượt và cho mở nguồn để đối chiếu. Ảnh cũ được giữ làm tư liệu, còn hình dưới đây là lượt chạy mới.',
  'RAG dùng checkpoint VoVanPhuc/sup-SimCSE-VietNamese-phobert-base, revision 608779b86741a8acd8c8d38132974ff04086b138, tách từ bằng PyVi và mean pooling trên CPU. Vector được chuẩn hóa trước khi đưa vào FAISS IndexFlatL2. Cấu hình được chọn là chunk 1.000 ký tự, overlap 180, top-k 6; PDF tạo ra 12 chunk. Cả 12 chunk đều nằm trong giới hạn 256 token của embedding. Model chọn mã đoạn trích trong ngữ cảnh; server đổi mã thành nguyên văn và kiểm tra đúng nguồn trước khi trả kết quả.',
  'Khi chạy lại cấu hình 500/50/top-2 chưa tách từ, 6/25 câu có đủ các đoạn cần đối chiếu, trong đó 1/8 câu cũ. Cấu hình sau điều chỉnh đạt đủ đoạn ở 25/25 câu có đáp án, gồm 8/8 câu cũ; hai câu ngoài PDF không được tính vào tỷ lệ này. Bộ 27 câu đã được dùng khi chọn tham số, vì vậy đây là kiểm tra hồi quy, chưa phải đánh giá trên bộ độc lập. Tìm đúng đoạn cũng chưa bảo đảm model trả lời đúng.',
  f'Bộ kiểm thử tự động đạt 67 bài, bỏ qua hai bài nạp embedding cần bật riêng. Các bài này kiểm tra luồng xử lý, API, phiên, cache và trích dẫn bằng fixture; không gọi Groq hoặc Tavily. Kiểm tra retrieval với embedding thật được chạy riêng. Hash của 154 tệp minh chứng cũ cùng chín tệp source lịch sử vẫn khớp bản đã lưu.',
  f'Với ba câu trên giao diện, model lần lượt chọn RAG, trả lời trò chuyện và tìm kiếm web. Cả ba yêu cầu trả HTTP 200 với status ok. Thời gian đo tại trình duyệt lần lượt là {latencies[0]:.3f}, {latencies[1]:.3f} và {latencies[2]:.3f} giây, tổng cộng {tokens:,} token theo usage của nhà cung cấp. Hai lượt cần công cụ có thêm lời gọi model để chọn tool. Bộ ba này chỉ xác nhận hành vi quan sát được; không được gộp với phép đo forced RAG ở đoạn sau.',
  f'Lượt forced RAG gồm tám câu cũ, ba câu bổ sung và hai câu ngoài PDF; chạy tuần tự trên cùng API, tắt cache, nghỉ 45 giây giữa các yêu cầu. Chỉ mục đã được chuẩn bị trước. Kết quả có {summary["technical_completed"]}/13 yêu cầu hoàn tất kỹ thuật, {summary["answers_returned"]} phản hồi trả lời, {summary["refused"]} phản hồi từ chối và {summary["technical_errors"]} lỗi kỹ thuật. Latency trung bình {mean:.3f} giây, p50 {p50:.3f} giây, p95 {p95:.3f} giây (nearest-rank); tổng token đã ghi nhận đầy đủ là {summary["usage_totals"]["total_tokens"]:,}. Câu hỏi, đáp án tham chiếu, phản hồi, chunk theo thứ hạng, trang, điểm, trích dẫn và trace được lưu riêng cho từng câu trong faiss_live_final_13/.',
  'Đối chiếu nội dung cho thấy hai câu ngoài PDF được từ chối đúng, nhưng câu hỏi về thời lượng thở cuộn bị từ chối dù ngữ cảnh có thông tin 3–5 phút. Các câu về tư thế khi mới tập, nâng đầu sau cùng và giữ ngực không di chuyển trả lời đúng ý tham chiếu nhưng đoạn trích còn thiếu phần trực tiếp xác nhận. Những nhận xét này do AI đối chiếu với PDF, không phải điểm người thật; chúng cho thấy HTTP 200 và quote khớp nguồn vẫn chưa đủ để kết luận đáp án đúng.',
  'Chưa có lượt chấm của người thật cho bản FAISS này. Điểm RAG 96/104 và web 20/32 ở các mục trước vẫn thuộc đúng những phản hồi cũ. Những lần thử ngày 05/11 có trả lời trực tiếp thay vì dùng RAG, từ chối do trích dẫn, lỗi schema Groq và thiếu RAM đều được giữ trong hồ sơ cùng source hoặc định danh của lần chạy đó. Không thay các kết quả này bằng kết quả của lượt đã sửa.'
 ],
 'evidence_screenshot_path':f'ui_restore/{UI_RUN}/conversation_actual_full.png',
 'evidence_screenshot_kind':'live',
 'evidence_screenshot_caption':'Hình 13.12. Giao diện hội thoại được khôi phục theo ảnh báo cáo; ba phản hồi thật qua RAG, trò chuyện và web trong cùng phiên, ngày 05/11/2026, model openai/gpt-oss-20b. Các phản hồi và nguồn được giữ nguyên từ API.',
 'evidence_trace_ids':[r['response']['trace_id'] for r in records],
 'evidence_run_id':UI_RUN,
 'evidence_supporting_logs':[f'evidence/restored_20261105/ui_restore/{UI_RUN}/{n}' for n in ('requests_responses.json','LIVE_CAPTURE_REPORT.json','LIVE_RESULTS.csv')]+['evidence/restored_20261105/server_traces_all.jsonl'],
 'appendix_paragraphs':[
  'Phụ lục B. Nhật ký chỉnh sửa và sử dụng AI',
  'Ngày 05/11/2026: pull main trước khi sửa, giữ bản source ban đầu và các thay đổi đang làm. Đối chiếu báo cáo mới nhất trên Drive với entrypoint main:app, hình giao diện và luồng RAG; khôi phục giao diện hội thoại và embedding + FAISS, giữ nguyên PDF và mô hình sinh.',
  'Sau khi sửa: khóa requirements của môi trường chạy, kiểm tra cơ chế bằng fixture, chạy retrieval bằng embedding thật, thử ba câu qua giao diện và chạy riêng bộ forced RAG. Mỗi lượt có source/hash, cấu hình, thời điểm và trace; kết quả chưa đạt được giữ cùng kết quả sau sửa. Báo cáo chỉ thêm số liệu khi đã có log.',
  'Codex hỗ trợ đọc source và tài liệu, dựng lại giao diện từ ảnh, sửa code, viết script kiểm tra, thu log, đối chiếu nguồn, biên tập và đóng gói. Phản hồi thật do Groq sinh, nội dung tìm kiếm do Tavily trả về. Nhận xét do AI đối chiếu được ghi riêng, không thay cho điểm người thật và không được coi là đánh giá chuyên gia.',
  'Các câu hỏi có AI hỗ trợ biên soạn và đã được dùng để điều chỉnh cấu hình. Nhóm cần đọc lại phản hồi và nguồn trước khi sử dụng; đồ án chưa đánh giá hiệu quả tư vấn tâm lý, chưa có kiểm thử độc lập về chất lượng và chưa triển khai lưu hội thoại bền vững bằng MySQL.'
 ]}
save(BASE/'report_verified_facts.json',facts)
save(BASE/'report_final_source_reference.json',{'commit':commit,'graph_id':graph,'ui_run':UI_RUN,'rag_summary':summary})
print(json.dumps({'commit':commit,'graph_id':graph,'report_facts':'ready','ui_tokens':tokens,'rag':summary},ensure_ascii=False))
