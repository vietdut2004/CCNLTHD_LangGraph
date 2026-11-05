"""Revise the latest reviewed report without rewriting unrelated OOXML parts.

The first invocation creates an explicit paragraph plan and a candidate DOCX.
Runtime assertions remain draft placeholders until report_verified_facts.json is
provided by the source/test owner. No provider result is generated here.
"""
import hashlib
import json
import re
import struct
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape
from zipfile import ZipFile

BASE = Path(__file__).resolve().parent
SOURCE = BASE / 'report_current.docx'
EXPECTED_SHA = '5ac33d056def26f9d0ad50f2effdd73e5a7f622567d5a2c71258ecc59a2bb3cb'
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def get_paragraphs(xml):
    return re.findall(rb'<w:p(?=[\s>])[^>]*>.*?</w:p>', xml, re.S)


def replace_text(raw, before, after):
    old = escape(before).encode('utf-8')
    assert raw.count(old) == 1, before
    return raw.replace(old, escape(after).encode('utf-8'), 1)


def paragraph(value, template):
    """Use an existing paragraph's exact style, without reserializing document."""
    # Templates for new paragraphs have a single text node and no image/field.
    template = re.sub(rb'<w:bookmark(?:Start|End)\b[^>]*/>', b'', template)
    template = re.sub(rb' w14:paraId="[^"]+"', b'', template)
    if value.startswith(('13.12 ', 'Phụ lục B ')):
        if b'<w:keepNext' in template:
            template = re.sub(rb'<w:keepNext\b[^>]*/>', b'<w:keepNext/>', template)
        else:
            template = template.replace(b'<w:pPr>', b'<w:pPr><w:keepNext/>', 1)
    values = list(re.finditer(rb'<w:t(?:\s[^>]*)?>(.*?)</w:t>', template, re.S))
    assert len(values) == 1
    match = values[0]
    return template[:match.start(1)] + escape(value).encode('utf-8') + template[match.end(1):]


def image_paragraph(path, template):
    data = path.read_bytes()
    assert data.startswith(b'\x89PNG\r\n\x1a\n')
    width, height = struct.unpack('>II', data[16:24])
    cx = 5655600
    cy = round(cx * height / width)
    if cy > 5943600:
        cx = round(cx * 5943600 / cy)
        cy = 5943600
    result = re.sub(rb'(<(?:wp:extent|a:ext)\b[^>]*?)cx="\d+" cy="\d+"',
                    lambda m: m.group(1) + f'cx="{cx}" cy="{cy}"'.encode(), template)
    result = re.sub(rb'r:embed="[^"]+"', b'r:embed="rIdReportUI20261105"', result)
    result = result.replace(b'wp:docPr id="10346"', b'wp:docPr id="29051105"')
    result = result.replace(b'image103.png', b'report_ui_20261105.png')
    result = result.replace(b'<w:pPr>', b'<w:pPr><w:keepNext/>', 1)
    return result, data


def main():
    source_data = SOURCE.read_bytes()
    assert digest(source_data) == EXPECTED_SHA, 'Latest report snapshot changed'
    with ZipFile(SOURCE) as source:
        xml = source.read('word/document.xml')
        elements = list(ET.fromstring(xml).iter(W + 'p'))
        raw = get_paragraphs(xml)
        old = [''.join(t.text or '' for t in p.iter(W + 't')) for p in elements]
        assert len(elements) == len(raw) == 1484

        # These edits concern product implementation, interpretation and provenance.
        # Scientific measurements and human scores remain in their original runs.
        changes = {
            115: 'Quản lý lịch sử hội thoại theo từng phiên; lưu trữ bằng MySQL là hướng mở rộng.',
            862: 'Lịch sử hội thoại được lưu trong State theo từng phiên để dùng cho lượt tiếp theo. Các kiểm tra của bản v1.3 được giữ ở mục 13.7; kết quả của bản khôi phục ngày 05/11 được trình bày riêng tại mục 13.12.',
            863: 'Bộ nhớ hiện dùng RAM nên mất khi khởi động lại. Các ảnh ConversationBufferWindowMemory dưới đây minh họa cơ chế cửa sổ hội thoại của LangChain, không phải ảnh kiểm thử bộ nhớ của ứng dụng.',
            891: 'Phần MySQL/FAISS dưới đây minh họa tìm kiếm tương đồng. Chức năng này khác với cache câu trả lời. Các kết quả exact cache trong RAM ở mục 13.6 thuộc bản v1.3 và được giữ để đối chiếu quá trình phát triển.',
            895: 'Cache có thể lưu trong RAM hoặc cơ sở dữ liệu. Các ca đã đo ở mục 13.6 dùng RAM; dữ liệu không được giữ sau khi khởi động lại.',
            945: 'Ứng dụng kết hợp trò chuyện trực tiếp với hai công cụ: RAGTOOL tra cứu tài liệu và SearchWebTool tìm kiếm trên web.',
            946: 'Agent điều phối các thành phần trên và trả lời người dùng qua API /chatbot. Phần triển khai cụ thể được trình bày ở Chương 12 và Chương 13.',
            1019: 'Giao diện trong hình gửi câu hỏi đến /ask_document và hiển thị phản hồi của chức năng hỏi đáp tài liệu. Ứng dụng tích hợp ở Chương 13 dùng endpoint /chatbot; kết quả chạy mới được lưu riêng cùng log và tài liệu nguồn.',
            1022: 'Ý tưởng: Xây dựng chatbot “Hỗ trợ tâm lý” để người dùng trò chuyện, tìm hiểu cách giảm căng thẳng và tra cứu nội dung từ tài liệu hoặc web. LangGraph tổ chức luồng xử lý, kết nối mô hình ngôn ngữ với các công cụ và lịch sử hội thoại.',
            1024: 'Tạo một giao diện hội thoại dễ sử dụng, cho phép người dùng chia sẻ cảm xúc và tiếp tục trao đổi trong cùng một phiên.',
            1026: 'Sử dụng Stress.pdf (6 trang) làm nguồn cho chức năng hỏi đáp về kỹ thuật thở. Nội dung tương ứng được tìm thấy trong bài “Các kỹ thuật thở sâu để giảm căng thẳng” của Vinmec, cập nhật ngày 22/07/2024. Do file PDF không ghi tác giả và ngày xuất bản, báo cáo giữ riêng thông tin đối chiếu và hash của file đã dùng.',
            1027: 'Tích hợp trò chuyện, truy xuất tài liệu, tìm kiếm web và bộ nhớ phiên; ghi nhận thời gian phản hồi, lượng token và lỗi để đánh giá kết quả triển khai.',
            1029: 'Trò chuyện nhiều lượt: người dùng gửi và nhận tin nhắn trong cùng một phiên, có thể xem lại các lượt đã trao đổi ngay trên giao diện.',
            1030: 'Gợi ý những hoạt động tự chăm sóc tinh thần như tập thở, thư giãn và tìm đọc nội dung phù hợp. Chatbot không thay thế chuyên gia, không chẩn đoán hay kê thuốc; đồ án chưa đánh giá hiệu quả lâm sàng.',
            1031: 'Hỏi đáp tài liệu: chia Stress.pdf thành các đoạn, tạo embedding và truy xuất bằng FAISS. Những đoạn liên quan được đưa vào ngữ cảnh để mô hình trả lời kèm nguồn.',
            1032: 'Tìm kiếm web: dùng Tavily lấy nội dung và đường dẫn để hỗ trợ các câu hỏi cần thông tin bên ngoài tài liệu, chẳng hạn tìm bài viết hoặc gợi ý phim. Phần kết quả phân biệt lượt thử chức năng này với bộ bốn câu kỹ thuật đã đo trước đó.',
            1036: 'LangGraph tổ chức luồng xử lý; mô hình openai/gpt-oss-20b được gọi qua Groq. Chức năng RAG dùng embedding tiếng Việt và FAISS, còn tìm kiếm web dùng Tavily. Các phép đo BM25 ở mục 13.3 thuộc một nhánh thử nghiệm trước đó, được lưu riêng để đối chiếu.',
            1041: 'Trò chuyện, tra cứu tài liệu/web và quản lý phiên',
            1043: 'Tách bước xử lý thành các node để theo dõi trạng thái và đường đi; chưa có phép đo so sánh tốc độ với cách viết hàm trực tiếp.',
            1050: 'Nhóm chọn cách tổ chức này để dễ theo dõi và thay đổi từng thành phần. Chất lượng trả lời vẫn phụ thuộc tài liệu, bước truy xuất, prompt và mô hình; chưa có benchmark so sánh các cách tổ chức luồng.',
            1054: 'Hiển thị các tin nhắn theo thứ tự trao đổi: phản hồi của chatbot bên trái, tin nhắn người dùng bên phải. Ô nhập và nút Gửi nằm cuối khung chat; thông tin nguồn được mở khi cần đối chiếu.',
            1058: 'Giao diện gửi câu hỏi và mã phiên đến /chatbot. Backend gọi agent, thực hiện bước trò chuyện hoặc truy xuất cần thiết rồi trả nội dung cho giao diện. Nguồn, mã truy vết và thông tin sử dụng token được lưu để kiểm tra từng yêu cầu.',
            1059: '* Luồng xử lý hội thoại và công cụ:',
            1061: 'Ở chế độ tự động, node classify gọi mô hình với lược đồ của rag_tool và search_web. Mô hình có thể trả lời trực tiếp hoặc chọn một công cụ. Nhánh RAG truy xuất FAISS; nhánh web truy vấn Tavily. Các nguồn được chuyển tới grounded để sinh và kiểm tra trích dẫn trước khi trả kết quả. StateGraph điều phối các bước và lưu lịch sử theo phiên.',
            1062: 'Với RAG, PDF được đọc, chia đoạn và chuyển thành vector trước khi tìm kiếm. Khi có câu hỏi, hệ thống dùng cùng mô hình embedding để tạo vector truy vấn, lấy các đoạn liên quan rồi chuyển cho mô hình sinh câu trả lời. Cấu hình và kết quả chạy của từng phiên bản được ghi riêng ở Chương 13.',
            1065: 'a) Cấu trúc thư mục ứng dụng',
            1067: 'Các thành phần chính vẫn được tổ chức theo giao diện, API, agent và công cụ như sơ đồ trên. Trong source hiện tại, main.py và các module nằm ở thư mục gốc; frontend/ chứa giao diện, benchmarks/ chứa lệnh kiểm tra và handover/ lưu minh chứng các lượt trước.',
            1068: 'agent.py: kết nối mô hình, công cụ và trạng thái hội thoại để xử lý yêu cầu từ API.',
            1069: 'searchweb_tool.py: gửi truy vấn đến Tavily và trả nội dung cùng URL nguồn.',
            1070: 'Rag_tool.py: đọc Stress.pdf, tạo embedding, lập chỉ mục FAISS và truy xuất các đoạn liên quan làm ngữ cảnh trả lời.',
            1073: 'requirements.txt và requirements-locked.txt: danh sách thư viện và phiên bản cần cài, gồm các phụ thuộc đọc PDF, embedding và FAISS. Bộ khóa của nhánh BM25 được giữ cùng minh chứng lịch sử.',
            1074: 'frontend/index.html: giao diện “Hỗ trợ tâm lý” với thanh bên, khung hội thoại và ô nhập tin nhắn; được FastAPI phục vụ tại /.',
            1076: 'B1: Giải nén gói mã nguồn kèm báo cáo hoặc lấy đúng commit trong hồ sơ bàn giao. Mở thư mục có main.py; commit và hash của bản đã kiểm tra được ghi trong manifest kèm source.',
            1077: 'B2: Dùng Python 3.13.2, tạo môi trường bằng python -m venv .venv. Trên PowerShell, gọi trực tiếp .\\.venv\\Scripts\\python.exe để dùng đúng môi trường.',
            1078: 'B3: Chạy .\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt. Đối chiếu requirements-locked.txt và manifest trước khi tái lập các phép kiểm tra; dùng bộ nguồn, thư viện và câu hỏi đi cùng phiên bản cần đo.',
            1080: 'B5: Chạy .\\.venv\\Scripts\\python.exe start_api.py. Lệnh này khởi động main:app trong main.py trên cổng 8000. Mở http://127.0.0.1:8000/docs để kiểm tra API hoặc /health để xem cấu hình đang chạy.',
            1081: 'B6: Mở http://127.0.0.1:8000/ để sử dụng chatbot. Các tin nhắn cùng một cuộc trò chuyện dùng chung mã phiên. Ứng dụng chuẩn bị mô hình embedding và chỉ mục FAISS khi khởi động; lần đầu cần tải mô hình. Thời gian chuẩn bị được ghi riêng trong log.',
            1085: 'Ảnh mã phía trên ghi lại bước tích hợp agent ban đầu với llama-3.1-8b-instant. Ứng dụng hiện giữ mô hình openai/gpt-oss-20b đang dùng trong các lượt đo gần đây; kết quả kiểm tra ngày 05/11 được ghi ở mục 13.12.',
            1086: 'RAGTOOL lấy thông tin từ tài liệu về kỹ thuật hít thở sâu, cung cấp ngữ cảnh để mô hình trả lời câu hỏi của người dùng.',
            1087: 'SearchWebTool tìm nội dung trên web và cung cấp đường dẫn cho câu trả lời. Các câu gợi ý phim trong hình thể hiện cách dùng chức năng này; bộ bốn câu kỹ thuật đã đo được trình bày riêng ở mục 13.4.',
            1088: 'Với những câu trò chuyện thông thường, mô hình trả lời dựa trên câu hỏi và lịch sử của phiên, không cần truy xuất tài liệu hoặc web.',
            1095: 'Giao diện trong hình gồm thanh bên có logo SGU, tiêu đề “Hỗ trợ tâm lý”, các tin nhắn hai phía và ô nhập ở cuối khung chat. Nội dung trao đổi được giữ theo thứ tự để người dùng tiếp tục cuộc trò chuyện.',
            1096: 'Các câu hỏi trong hình lần lượt minh họa hỏi đáp về hít thở sâu, trò chuyện thông thường và gợi ý phim. Đây là ảnh của phiên bản ban đầu. Ảnh chụp và log ngày 05/11 được bổ sung riêng để đối chiếu giao diện với đường gọi API.',
            1097: 'Log đi kèm ghi nhận lời gọi RAG, Groq, SearchWebTool và API /chatbot. Ảnh này xác nhận bước tích hợp ở thời điểm chụp; khi đánh giá nội dung cần xem thêm tài liệu hoặc đường dẫn mà câu trả lời đã sử dụng.',
            1098: 'Nhóm giữ nguyên các ảnh và kết quả đã thu thập. Các mục 13.2–13.11 trình bày số liệu theo phiên bản gốc; mục 13.12 dành cho bản khôi phục ngày 05/11/2026. Kết quả của một phiên bản không được chuyển sang phiên bản khác.',
            1101: 'Phần này ghi nhận quá trình kiểm tra ứng dụng qua các phiên bản. Dữ liệu hội thoại ngày 20/10, RAG FAISS ngày 24/10 và nhánh BM25/web ngày 28/10 được giữ nguyên. Các bài kiểm tra công cụ, cache, bộ nhớ và lỗi cũng được ghi theo bản đã chạy. Kiểm tra bản khôi phục ngày 05/11 được tách ở mục 13.12.',
            1103: '13.2 Hội thoại trực tiếp — kết quả ngày 20/10/2026',
            1117: '13.3 RAG — kết quả FAISS ngày 24/10 và BM25 ngày 28/10',
            1131: 'Ở nhánh thử nghiệm tuần 8, evidence-v1.3-rag-check dùng BM25 cân bằng các mục được hỏi, chunk tối đa 650 ký tự, overlap mục tiêu 180, top-3, giữ trang/offset gốc. Retrieval offline tìm đủ span ở 25/25 câu có đáp án. Ngày 28/10, 5 câu hồi quy chạy Groq thật đều trả lời có nguồn, AI đối chiếu khớp tham chiếu. TB 1.620,215 ms; p50 1.523,576 ms; p95 2.329,489 ms. Usage: 4.785 input + 1.448 output = 6.233 token.',
            1132: 'Trên cùng bản BM25 và model, bộ 8 câu mới giữ nguyên trước chạy: 6 câu có đáp án trả lời khớp PDF, 2 câu ngoài nguồn từ chối phù hợp theo đối chiếu AI; 0 lỗi kỹ thuật. TB 2.091,149 ms; p50 1.445,913 ms; p95 3.389,450 ms. Usage đủ 8/8: 9.003 input + 2.451 output = 11.454 token. Hai đợt không cache/retry/warm-up, p95 dùng nearest-rank. Thống kê riêng 5 câu hồi quy và 8 câu mới; các câu do AI soạn từ cùng PDF, chưa đại diện nguồn/cách hỏi khác.',
            1133: '13.4 Tìm kiếm web — kết quả ngày 28/10/2026',
            1134: 'Đo lại ngày 28/10 trên bản evidence-v1.3-rag-check: bốn câu kỹ thuật FastAPI/LangGraph chạy Tavily và Groq openai/gpt-oss-20b. 4/4 hoàn tất HTTP 200; web_03/04 trả lời có nguồn, web_01/02 từ chối do quote không khớp. Lượt 24/10 trả lời web_01/03; hai lượt được giữ riêng.',
            1147: '13.5 Công cụ toán và định tuyến của bản v1.3',
            1166: '13.6 Cache câu trả lời của bản v1.3',
            1178: '13.7 Bộ nhớ và tách phiên của bản v1.3',
            1181: '13.8 Đầu vào sai và xử lý lỗi đã kiểm tra',
            1198: 'Bản v1.3 có 57/57 unit test đạt, gồm kiểm tra retrieval và lỗi giả lập timeout/quota/auth/thiếu PDF/deadline. Model timeout 25 giây, web 20 giây, API deadline 60 giây; recursion_limit=12 giới hạn bước, output tối đa 1.536 token, retry=0. Đây là kết quả của bộ mã cũ, không phải 57 lượt gọi provider hay kết quả kiểm thử bản FAISS khôi phục.',
            1210: '13.10 Chấm nội dung các phản hồi ngày 28/10/2026',
            1212: 'Huỳnh Lê Sơn chấm 13 phản hồi RAG của bản BM25 ngày 28/10: 96/104, trung bình 7,38/8; 5 hồi quy: 7,60/8, 8 câu mới khóa trước chạy: 7,25/8. Các điểm này không áp dụng cho bản FAISS khôi phục. Một người chấm trên cùng PDF; điểm rubric không phải tỷ lệ đúng hoặc chấm chuyên gia.',
            1213: '13.11 Tổng hợp các kết quả đã lưu trữ',
            1220: 'RAG BM25',
            1236: '57 unit test của bản v1.3 đạt.',
            1239: 'Các kết quả trên được giữ cùng bộ câu hỏi, nguồn, trace và phiên bản mã tương ứng. Bản khôi phục dùng lại câu hỏi cũ được xem là kiểm tra hồi quy; cần đọc kết quả mới ở mục 13.12 thay vì sử dụng lại điểm của 13 phiếu RAG hoặc 4 phiếu web.',
            1243: 'Đề tài đã trình bày các thành phần State, Node, Edge và cách điều phối của LangGraph, đồng thời xây dựng ứng dụng “Hỗ trợ tâm lý”. Người dùng trao đổi qua giao diện hội thoại; mô hình kết hợp lịch sử phiên với công cụ hỏi đáp tài liệu bằng embedding/FAISS và tìm kiếm web bằng Tavily.',
            1244: 'Các lượt thử trước được giữ để thể hiện quá trình hoàn thiện: bản evidence-v1.3-rag-check đạt 57 unit test; bộ RAG BM25 ngày 28/10 có điểm 13 câu là 7,38/8; bộ web bốn câu có 2 trả lời, 2 từ chối và điểm 5,00/8. Đây là kết quả của bản đã đo, không dùng để xác nhận chất lượng của bản khôi phục.',
            1246: 'Frontend giao tiếp với FastAPI qua /chatbot. Trong đợt hội thoại ngày 20/10, 10 yêu cầu đều hoàn tất về kỹ thuật; latency trung bình 754,073 ms, p95 1.108,563 ms và tổng usage 4.709 token. Ba ca đầu vào sai trả HTTP 422. Phép đo này được giữ theo source ban đầu; phần kiểm tra ứng dụng sau khôi phục nằm ở mục 13.12.',
            1261: 'Nhóm đã chuẩn bị đáp án tham chiếu và rubric bốn tiêu chí. Các phiếu hiện có gồm 13 phản hồi RAG BM25 và 4 phản hồi web ngày 28/10, do một người chấm; chưa có đánh giá độc lập nhiều người hoặc phiếu cho bản khôi phục.',
            1309: 'Thư viện FAISS: https://github.com/facebookresearch/faiss/wiki',
            1310: 'Mô hình embedding tiếng Việt: https://huggingface.co/VoVanPhuc/sup-SimCSE-VietNamese-phobert-base',
        }

        facts_path = BASE / 'report_verified_facts.json'
        facts = json.loads(facts_path.read_text('utf-8')) if facts_path.exists() else {}
        # The test/source owner supplies verified prose after reading actual logs.
        changes.update({int(key): value for key, value in facts.get('paragraph_overrides', {}).items()})
        new_section = facts.get('new_section_paragraphs', [
            '13.12 Kiểm tra bản khôi phục ngày 05/11/2026',
            '[BẢN NHÁP NỘI BỘ — chưa đưa vào bài nộp] Chờ xác minh source cuối, cấu hình embedding/FAISS và log thực tế. Không lấy số liệu hoặc điểm người chấm của bản BM25 thay cho kết quả này.',
        ])
        appendix = facts.get('appendix_paragraphs', [
            'Phụ lục B Nhật ký chỉnh sửa và sử dụng AI',
            'Ngày 05/11/2026, nhóm đối chiếu source với báo cáo và phát hiện giao diện cùng phương pháp truy xuất đã thay đổi trong quá trình tích hợp các gói sửa. Nhóm khôi phục khung hội thoại theo ảnh gốc và RAG dùng embedding/FAISS; giữ các bản đo trước cùng nguồn gốc để đối chiếu.',
            'Codex hỗ trợ rà soát mã, sửa giao diện và RAG, tổ chức kiểm thử, đối chiếu minh chứng và biên tập phần triển khai. Trong các lượt trước, công cụ còn hỗ trợ soạn câu hỏi, đáp án tham chiếu và nhập/xuất phiếu chấm; điểm và nhận xét do người chấm lựa chọn. Các số liệu được giữ theo nguồn tương ứng, kết quả mới chỉ bổ sung sau khi có log. Nhóm chịu trách nhiệm kiểm tra và duyệt bản nộp.',
        ])
        plan = {
            'source': str(SOURCE), 'source_sha256': EXPECTED_SHA,
            'status': facts.get('status', 'draft_pending_runtime_verification'),
            'scope': 'Align restored implementation and UI, preserve all historical measurements and human grades',
            'edits': [{'paragraph_0_based': i, 'before': old[i], 'after': value} for i, value in sorted(changes.items())],
            'insert_before_paragraph_1240': new_section,
            'appendix': appendix,
            'untouched_scope': 'All unrelated theory examples, images, styles and table structures',
        }
        toc_overrides = {int(key): value for key, value in facts.get('toc_overrides', {}).items()}
        toc_overrides.setdefault(62, {'title': 'a) Cấu trúc thư mục ứng dụng'})
        plan['toc_edits'] = []
        replacement_media = {}
        flow_image = BASE / 'report_runtime_flow.png'
        if flow_image.exists():
            replacement_media['word/media/image99.png'] = flow_image.read_bytes()
        plan['media_changes'] = [{
            'docx_part': name,
            'before_sha256': digest(source.read(name)),
            'after_sha256': digest(value),
            'reason': 'Replace Codex keyword-router architecture diagram with source-derived model-tool-calling flow; all screenshots retained',
        } for name, value in replacement_media.items()]
        additions = {}
        ui_path = BASE / facts.get('evidence_screenshot_path', 'ui_restore/ui_restored_desktop_initial.png')
        evidence_caption = facts.get('evidence_screenshot_caption', (
            'Giao diện bản khôi phục chụp ngày 05/11/2026. Hình ghi nhận trang khởi tạo '
            'với lời chào cố định, chưa có phản hồi model. Các kiểm tra gửi tin, giữ phiên '
            'và xử lý lỗi của giao diện dùng dữ liệu mô phỏng; kết quả gọi model thật được '
            'ghi riêng trong log của bản khôi phục.'
        ))
        evidence_xml = b''
        if facts.get('evidence_screenshot_path'):
            assert ui_path.is_file(), 'Selected UI evidence screenshot does not exist'
        screenshot_kind = facts.get('evidence_screenshot_kind', 'initial')
        assert screenshot_kind in ('initial', 'live')
        if screenshot_kind == 'live':
            assert facts.get('evidence_trace_ids'), 'Live evidence requires its actual trace IDs'
            assert facts.get('evidence_screenshot_caption'), 'Live evidence requires an explicit factual caption'
        if ui_path.exists():
            picture, data = image_paragraph(ui_path, raw[1057])
            additions['word/media/report_ui_20261105.png'] = data
            evidence_xml = picture + paragraph(evidence_caption, raw[1101])
            plan['added_evidence_screenshot'] = {
                'path': str(ui_path), 'sha256': digest(data),
                'caption': evidence_caption,
                'kind': screenshot_kind,
                'trace_ids': facts.get('evidence_trace_ids', []),
                'run_id': facts.get('evidence_run_id'),
                'supporting_logs': facts.get('evidence_supporting_logs', []),
                'proves': ('Initial browser UI only; fixture checks are not model output'
                           if screenshot_kind == 'initial'
                           else 'Actual captured responses of this declared live run only; not automatic answer correctness'),
            }
        (BASE / 'report_edit_plan.json').write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n', 'utf-8')

        updated = xml
        for i, value in sorted(changes.items()):
            assert len(list(elements[i].iter(W + 't'))) == 1
            changed = replace_text(raw[i], old[i], value)
            assert updated.count(raw[i]) == 1
            updated = updated.replace(raw[i], changed, 1)
        for i, fields in sorted(toc_overrides.items()):
            parts = list(elements[i].iter(W + 't'))
            assert len(parts) == 2, 'TOC row structure changed'
            changed = raw[i]
            values = [fields.get('title', parts[0].text or ''), str(fields.get('page', parts[1].text or ''))]
            for before, after in zip(parts, values):
                if before.text != after:
                    changed = replace_text(changed, before.text or '', after)
            updated = updated.replace(raw[i], changed, 1)
            plan['toc_edits'].append({'paragraph_0_based': i, 'before': old[i], 'after': ''.join(values)})
        toc_extra_xml = b''
        if facts.get('appendix_toc_page') is not None:
            toc_extra_xml = raw[69]
            toc_extra_xml = re.sub(rb'<w:fldChar\b[^>]*/>', b'', toc_extra_xml)
            toc_extra_xml = re.sub(rb'<w:instrText\b[^>]*>.*?</w:instrText>', b'', toc_extra_xml, flags=re.S)
            toc_extra_xml = re.sub(rb' w14:paraId="[^"]+"', b'', toc_extra_xml)
            toc_extra_xml = re.sub(rb'w:anchor="[^"]+"', b'w:anchor="_report_restore_appendix_b"', toc_extra_xml)
            parts = list(elements[69].iter(W + 't'))
            toc_extra_xml = replace_text(toc_extra_xml, parts[0].text, 'Phụ lục B Nhật ký chỉnh sửa và sử dụng AI')
            toc_extra_xml = replace_text(toc_extra_xml, parts[1].text, str(facts['appendix_toc_page']))
            assert updated.count(raw[70]) == 1
            updated = updated.replace(raw[70], toc_extra_xml + raw[70], 1)
            plan['added_toc_entry'] = 'Phụ lục B Nhật ký chỉnh sửa và sử dụng AI'
        inserted = b''.join(paragraph(t, raw[1100] if index == 0 else raw[1101]) for index, t in enumerate(new_section)) + evidence_xml
        assert updated.count(raw[1240]) == 1
        updated = updated.replace(raw[1240], inserted + raw[1240], 1)
        appendix_xml = b''.join(paragraph(t, raw[1314] if index == 0 else raw[1101]) for index, t in enumerate(appendix))
        if toc_extra_xml:
            first_end = appendix_xml.index(b'</w:p>')
            appendix_xml = (appendix_xml[:first_end] +
                b'<w:bookmarkStart w:id="88001" w:name="_report_restore_appendix_b"/>'
                b'<w:bookmarkEnd w:id="88001"/>' + appendix_xml[first_end:])
        pos = updated.rfind(b'<w:sectPr')
        assert pos > 0
        updated = updated[:pos] + appendix_xml + updated[pos:]
        ET.fromstring(updated)

        output = BASE / 'report_restored_candidate.docx'
        modified_rels = source.read('word/_rels/document.xml.rels')
        if additions:
            assert b'rIdReportUI20261105' not in modified_rels
            relationship = (
                b'<Relationship Id="rIdReportUI20261105" '
                b'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
                b'Target="media/report_ui_20261105.png"/>'
            )
            modified_rels = modified_rels.replace(b'</Relationships>', relationship+b'</Relationships>', 1)
        with ZipFile(output, 'w') as target:
            for info in source.infolist():
                if info.filename == 'word/document.xml':
                    data = updated
                elif info.filename == 'word/_rels/document.xml.rels':
                    data = modified_rels
                else:
                    data = replacement_media.get(info.filename, source.read(info.filename))
                target.writestr(info, data)
            for name, value in additions.items():
                target.writestr(name,value)
        # Persist the final plan only after TOC/evidence edits are fully known.
        (BASE / 'report_edit_plan.json').write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n', 'utf-8')

    with ZipFile(SOURCE) as original, ZipFile(output) as result:
        changed_parts = [n for n in original.namelist() if original.read(n) != result.read(n)]
        expected_parts = ['word/document.xml'] + list(replacement_media)
        if additions:
            expected_parts += ['word/_rels/document.xml.rels']
        assert sorted(changed_parts) == sorted(expected_parts)
        assert set(result.namelist()) - set(original.namelist()) == set(additions)
        new_raw = get_paragraphs(result.read('word/document.xml'))
        if toc_extra_xml:
            new_raw.pop(70)
        inserted_count = len(new_section) + (2 if additions else 0)
        without_insertions = new_raw[:1240] + new_raw[1240 + inserted_count:-len(appendix)]
        assert len(without_insertions) == len(raw)
        for i, p in enumerate(raw):
            if i not in changes and i not in toc_overrides:
                assert p == without_insertions[i], f'Unrelated paragraph {i} changed'
        table_tags_before = re.findall(rb'</?w:(?:tbl|tr|tc)(?=[\s>])[^>]*>', xml)
        table_tags_after = re.findall(rb'</?w:(?:tbl|tr|tc)(?=[\s>])[^>]*>', updated)
        assert table_tags_before == table_tags_after
        # Protect raw numeric cells and complete metric paragraphs byte for byte.
        protected = list(range(1104, 1117)) + list(range(1118, 1131)) + list(range(1135, 1147)) + list(range(1148, 1166)) + list(range(1167, 1178)) + list(range(1179, 1181)) + list(range(1182, 1198)) + list(range(1200, 1210))
        assert all(raw[i] == without_insertions[i] for i in protected)

    validation = {
        'status': plan['status'],
        'source': str(SOURCE), 'source_sha256': EXPECTED_SHA,
        'output': str(output), 'output_sha256': digest(output.read_bytes()),
        'changed_docx_parts': changed_parts,
        'changed_existing_paragraphs': len(changes),
        'toc_cached_rows_updated': len(toc_overrides),
        'added_appendix_toc_entry': bool(toc_extra_xml),
        'inserted_new_test_paragraphs': len(new_section),
        'added_evidence_screenshot_and_caption': bool(additions),
        'appended_paragraphs': len(appendix),
        'all_unrelated_paragraph_xml_unchanged': True,
        'all_existing_parts_except_text_declared_diagram_and_image_relationship_unchanged': True,
        'all_existing_evidence_screenshots_unchanged': True,
        'media_changes': plan['media_changes'],
        'table_structure_unchanged': True,
        'protected_metric_paragraphs_byte_identical': protected,
        'historical_metric_values_and_human_grades_preserved': True,
        'new_human_scores_added': False,
        'provider_calls_by_report_editor': 0,
        'original_report_unchanged': digest(SOURCE.read_bytes()) == EXPECTED_SHA,
        'placeholder_present': '[BẢN NHÁP NỘI BỘ' in '\n'.join(new_section),
    }
    (BASE / 'report_edit_validation.json').write_text(json.dumps(validation, ensure_ascii=False, indent=2) + '\n', 'utf-8')
    print(json.dumps(validation, ensure_ascii=False))


if __name__ == '__main__':
    main()
