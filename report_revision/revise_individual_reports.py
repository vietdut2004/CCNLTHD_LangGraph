from pathlib import Path
from copy import deepcopy
import hashlib
import json
import zipfile
import sys

from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(r'C:\Users\Admin\Downloads\Các báo cáo cần nôp')
OUT = ROOT / 'Bao_cao_ca_nhan_LangGraph'
OUT.mkdir(exist_ok=True)

PEOPLE = {
    '3122410469': ('Nguyễn Văn Việt', 'Nhóm trưởng; nghiên cứu, triển khai Agent và kết nối API', [
        ('Tổ chức và phối hợp nhóm', 'Em đảm nhận vai trò nhóm trưởng, cùng các thành viên lựa chọn đề tài, phân chia công việc theo tuần, theo dõi tiến độ và tổng hợp ý kiến trong các buổi báo cáo. Khi cập nhật sang LangGraph, nội dung cần thống nhất giữa mã nguồn và báo cáo là state, node, edge, công cụ và cách quản lý hội thoại.'),
        ('Xây dựng đồ thị hội thoại', 'Phần Agent được thể hiện trong agent.py bằng StateGraph(MessagesState). Node assistant là hàm bất đồng bộ, ghép SystemMessage với lịch sử messages rồi gọi mô hình qua ainvoke. Kết quả trả về dưới dạng cập nhật messages. Hai công cụ rag_tool và search_web được gắn vào mô hình bằng bind_tools.'),
        ('Điều phối việc gọi công cụ', 'Em tập trung tìm hiểu luồng START → assistant; nếu phản hồi có tool_calls thì tools_condition chuyển sang ToolNode, sau đó quay về assistant để mô hình sử dụng kết quả công cụ. Nếu không có yêu cầu công cụ, đồ thị đi đến END. tools_condition kiểm tra yêu cầu công cụ trong phản hồi; quyết định cần tra cứu xuất phát từ mô hình, không phải bộ phân loại từ khóa được lập trình riêng.'),
        ('Kết nối đồ thị với máy chủ', 'graph.py xuất đối tượng graph; langgraph.json đăng ký assistant có mã chatbot trỏ đến ./graph.py:graph. API tạo thread, đọc state và chạy đồ thị do LangGraph Agent Server cung cấp. main.py bổ sung đường dẫn giao diện và tệp tĩnh qua http.app; không tự cài đặt lại các API hội thoại.'),
        ('Giao tiếp với frontend', 'Frontend tạo hội thoại bằng POST /threads, khôi phục bằng GET /threads/{id}/state và gửi tin bằng POST /threads/{id}/runs/wait. Mỗi lần gửi chỉ cần bổ sung tin nhắn mới; runtime nạp lịch sử theo thread. Giá trị recursion_limit = 16 giới hạn số bước đồ thị trong một lượt chạy, không phải số tin nhắn được lưu.'),
        ('Kết quả và bài học', 'Phần việc Agent và API giúp em hiểu rõ cách tách điều phối AI khỏi giao diện web, cách giữ trạng thái giữa các lượt và cách đưa kết quả công cụ trở lại mô hình. Em cũng rèn luyện kỹ năng phân công, trao đổi kỹ thuật và tổng hợp tài liệu để các phần của nhóm sử dụng cùng một kiến trúc.')
    ]),
    '3122410269': ('Lý Chí Nguyên', 'Nghiên cứu SearchWebTool và bộ nhớ hội thoại', [
        ('Phối hợp thực hiện đề tài', 'Em tham gia lựa chọn đề tài, cập nhật tiến độ hàng tuần với nhóm trưởng và trao đổi với các thành viên về nội dung kỹ thuật. Phần chuyên môn tập trung vào công cụ tìm kiếm web và cơ chế sử dụng lại ngữ cảnh hội thoại.'),
        ('Công cụ tìm kiếm web', 'Trong searchweb_tool.py, SearchWebTool kế thừa BaseTool, có tên search_web và nhận query theo schema SearchWebInput. Công cụ sử dụng TAVILY_API_KEY, ưu tiên TavilySearch của langchain-tavily và có nhánh tương thích TavilySearchResults. Số kết quả yêu cầu tối đa là 3.'),
        ('Định dạng và xử lý kết quả', 'Hàm _format_results nhận kết quả dạng dictionary hoặc list, lấy tối đa ba mục và ghép tiêu đề, đoạn mô tả cùng URL nguồn. Mô tả được lấy tối đa 200 ký tự mỗi mục. Khi thiếu khóa hoặc gặp lỗi kết nối, _run trả thông báo chưa thể tìm kiếm; nội dung ngoại lệ thô không được đưa vào câu trả lời công cụ.'),
        ('Tích hợp công cụ vào LangGraph', 'Agent gắn search_web vào mô hình bằng bind_tools. Ví dụ, với yêu cầu tìm thông tin mới về phim truyền cảm hứng, mô hình có thể tạo tool_call để ToolNode thực thi search_web; kết quả quay lại assistant để tạo câu trả lời. Không mặc định rằng mọi câu hỏi về phim đều gọi web: hành vi chọn công cụ còn phụ thuộc phản hồi của mô hình.'),
        ('Bộ nhớ và trạng thái hội thoại', 'Qua phần thực hành Memory, em phân biệt được việc truyền lịch sử thủ công với lưu trạng thái bằng checkpoint. Chương trình hiện tại dùng MessagesState và runtime Agent Server để quản lý lịch sử theo thread. Frontend chỉ lưu thread_id trong sessionStorage; tạo cuộc trò chuyện mới sẽ tạo thread riêng và không xóa thread cũ trên máy chủ.'),
        ('Phân biệt bài tập với sản phẩm', 'Bài tập Agent tính cộng, nhân bằng @tool giúp em hiểu tool schema và vòng gọi công cụ. Các công cụ tính toán này không được đăng ký trong Agent chatbot hiện tại. Tương tự, các ví dụ memory trong notebook là tài liệu thực hành, không phải cơ chế lưu hội thoại của ứng dụng web.'),
        ('Kết quả và bài học', 'Em hiểu rõ hơn cách đóng gói dịch vụ tìm kiếm thành công cụ, cách giữ URL nguồn và cách xử lý tình huống dịch vụ không sẵn sàng. Việc nghiên cứu thread giúp em tránh nhầm rằng ChatModel tự nhớ thông tin hoặc lịch sử được lưu toàn bộ trong trình duyệt.')
    ]),
    '3122410129': ('Trần Duy Hoàng', 'Nghiên cứu kiến trúc Agent, truy xuất tài liệu và RAG', [
        ('Phối hợp nghiên cứu', 'Em tham gia lựa chọn đề tài, thực hiện phần chuyên môn theo phân công và báo cáo tiến độ với nhóm. Nội dung nghiên cứu gồm Agent, công cụ, prompt, Document Loader, Retriever và kiến trúc RAG; đồng thời tìm hiểu khả năng tracing và đánh giá của LangSmith.'),
        ('Phân tích kiến trúc RAG', 'Em tập trung tìm hiểu cách bổ sung dữ liệu riêng vào câu trả lời của LLM. Trong phiên bản hiện tại, Rag_tool.py đóng gói RAG thành công cụ rag_tool để đồ thị hội thoại gọi khi cần tra cứu Stress.pdf. RAG hỗ trợ trả lời có căn cứ tham khảo, nhưng không bảo đảm mọi câu trả lời đều chính xác.'),
        ('Chuẩn bị và lập chỉ mục tài liệu', 'RAGTOOL dùng PyPDFLoader đọc Stress.pdf, RecursiveCharacterTextSplitter chia đoạn với chunk_size = 500 và chunk_overlap = 50, tính theo ký tự. HuggingFaceEmbeddings sử dụng EMBEDDING_MODEL; giá trị mặc định là VoVanPhuc/sup-SimCSE-VietNamese-phobert-base. Các vector được lập chỉ mục bằng FAISS, không phải Chroma hay Pinecone.'),
        ('Truy xuất theo câu hỏi', 'Retriever lấy k = 2 đoạn theo mặc định. Hàm _retrieve ghép nội dung với nhãn [Stress.pdf, trang ...], trong đó page metadata được cộng 1 để hiển thị số trang bắt đầu từ 1. Retriever được khởi tạo khi cần và giữ lại trong đối tượng công cụ; mã hiện tại không ghi chỉ mục FAISS ra tệp để tái sử dụng sau khi khởi động lại.'),
        ('Đồ thị xử lý RAG', 'Luồng trong công cụ được xây bằng StateGraph(RAGState), gồm query, context và answer: START → retrieve → answer → END. Node answer gửi câu hỏi và ngữ cảnh tới ChatGroq, yêu cầu trả lời bằng tiếng Việt, dựa vào tài liệu và dẫn tên tài liệu cùng trang. Đồ thị này được gọi bên trong _run của rag_tool; không dùng RetrievalQA trong luồng ứng dụng.'),
        ('Giới hạn và khả năng kiểm chứng', 'Nếu context rỗng, công cụ trả thông báo không có thông tin phù hợp; nếu xảy ra lỗi thì trả thông báo chưa thể tra cứu. Khi đã có đoạn truy xuất nhưng nội dung không trả lời được câu hỏi, việc thừa nhận thiếu dữ liệu được hướng dẫn qua prompt; mã chưa có bộ chấm điểm độ liên quan hoặc xác minh trích dẫn độc lập.'),
        ('Kết quả và bài học', 'Em nắm rõ hơn các bước tải tài liệu, chia đoạn, embedding, tìm kiếm vector và tạo câu trả lời, cùng cách tích hợp chúng với vòng gọi công cụ LangGraph. Việc tìm hiểu LangSmith giúp em có định hướng đánh giá hệ thống; chưa có căn cứ để khẳng định đã xây dựng bộ đánh giá tự động hoàn chỉnh trong phiên bản hiện tại.')
    ]),
    '3122410459': ('Lầu Vỉ Tường', 'Hướng dẫn môi trường; thực hành ChatModel và prompt', [
        ('Phối hợp và chuẩn bị môi trường', 'Em tham gia lựa chọn đề tài, thực hiện nhiệm vụ theo tuần và trao đổi kết quả với các thành viên. Phần chuyên môn tập trung vào hướng dẫn cài đặt môi trường, sử dụng môi trường ảo và thực hành các thành phần mô hình, lịch sử hội thoại và prompt.'),
        ('Cài đặt dự án LangGraph', 'Môi trường theo README.md yêu cầu Python 3.11 trở lên. Tạo môi trường bằng python -m venv .venv, sau đó dùng .venv\\Scripts\\python.exe -m pip install -r requirements.txt. Các thư viện phục vụ dự án gồm langgraph, langgraph-sdk, langchain-groq, các gói truy xuất tài liệu, FAISS và Tavily; requirements.txt ghim langgraph-cli[inmem]==0.4.33.'),
        ('Cấu hình và khởi động', 'Nếu chưa có .env, sao chép .env.example và điền GROQ_API_KEY; cấu hình thêm TAVILY_API_KEY cho tìm kiếm web. Không ghi khóa vào mã frontend. Chạy .venv\\Scripts\\python.exe start_langgraph.py hoặc run_langgraph.bat rồi truy cập http://127.0.0.1:2024. Lệnh run_langgraph.bat --restart dùng khi cần khởi động lại máy chủ của dự án.'),
        ('So sánh stateless và lịch sử hội thoại', 'btap1.py dùng cùng lớp ChatGroq cho hai cách gọi: gửi từng câu độc lập và gửi danh sách HumanMessage, AIMessage, SystemMessage có lịch sử. Sự khác biệt xuất phát từ dữ liệu đầu vào, không phải hai loại mô hình có hoặc không có bộ nhớ tự động. Trong ứng dụng hiện tại, LangGraph quản lý lịch sử theo thread thay vì yêu cầu người dùng tự ghép danh sách ở mỗi lượt.'),
        ('Prompt và mô hình trong bài tập', 'chain.py minh họa ChatPromptTemplate với user_feeling, user_topic, ChatGroq và StrOutputParser nối bằng toán tử |; btap1.py và chain.py dùng llama-3.1-8b-instant. Đây là các bài tập nền tảng được giữ lại để tham khảo, không phải điểm chạy chatbot web và không cần đổi tên thư viện LangChain trong các đoạn mã này thành LangGraph.'),
        ('Prompt và mô hình trong ứng dụng', 'agent.py dùng SYSTEM_PROMPT kết hợp MessagesState, hướng dẫn trò chuyện tiếng Việt, sử dụng lịch sử, tra cứu công cụ khi cần và không tự nhận là bác sĩ. ChatGroq đọc GROQ_MODEL, mặc định openai/gpt-oss-20b, với temperature = 0, timeout = 60 và max_retries = 1. Đây là cấu hình mặc định trong mã, không khẳng định giá trị đang được ghi trong .env của người chạy.'),
        ('Kết quả và bài học', 'Em hiểu rõ hơn cách tách môi trường của dự án, phân biệt script bài tập với chương trình chính và xác định đúng nguồn tạo ra ngữ cảnh hội thoại. Việc đối chiếu prompt trong chain.py và agent.py cũng giúp em thấy cách chuyển từ ví dụ tuyến tính sang luồng xử lý có trạng thái và công cụ.')
    ])
}


def p(doc, text, heading=None):
    para = doc.add_paragraph(text, style=heading)
    if not heading:
        para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    return para


def build(student_id, name, role, contributions):
    source = next(SOURCE.glob(f'*{student_id}*.docx'))
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    doc = Document(source)
    thanks = next(x.text for x in doc.paragraphs if x.text.startswith('Em xin'))
    identity = deepcopy(doc.tables[0]._element) if doc.tables else None
    # Retain the original cover, including its drawing and personal information.
    # Element references are retained explicitly, avoiding proxy identity changes.
    cover = [x._p for x in doc.paragraphs[:15]]
    body = doc._element.body
    for el in list(body):
        if el.tag != qn('w:sectPr') and el not in cover:
            body.remove(el)
    for para in doc.paragraphs:
        if 'FRAMEWORK LANGCHAIN' in para.text:
            for run in para.runs:
                run.text = run.text.replace('LANGCHAIN', 'LANGGRAPH')
            if 'LANGCHAIN' in para.text:
                para.text = 'FRAMEWORK LANGGRAPH'
    normal = doc.styles['Normal']
    normal.font.name = 'Times New Roman'
    normal.font.size = Pt(13)
    normal.paragraph_format.line_spacing = 1.15
    normal.paragraph_format.space_after = Pt(7)
    for style in ('Heading 1', 'Heading 2'):
        doc.styles[style].font.name = 'Times New Roman'
        doc.styles[style].font.size = Pt(14 if style == 'Heading 1' else 13)
        doc.styles[style].font.color.rgb = RGBColor(0, 0, 0)
        doc.styles[style].paragraph_format.keep_with_next = True
    for section in doc.sections:
        section.page_width, section.page_height = Cm(21), Cm(29.7)
        section.top_margin, section.bottom_margin = Cm(2), Cm(2)
        section.left_margin, section.right_margin = Cm(3), Cm(2)

    doc.add_page_break()
    p(doc, 'LỜI CẢM ƠN', 'Heading 1')
    p(doc, thanks)
    p(doc, '1. Giới thiệu bản thân và lý do chọn đề tài', 'Heading 1')
    if identity is not None:
        body.insert(len(body) - 1, identity)
    else:
        p(doc, f'Em là {name}, mã số sinh viên {student_id}, thành viên Nhóm 10. '
          + ('Em học khóa K22, lớp DCT1226, chuyên ngành Công nghệ Thông tin.' if student_id == '3122410469' else 'Em thực hiện đề tài trong học phần Các công nghệ lập trình hiện đại.'))
    p(doc, 'Đề tài “Tìm hiểu Framework LangGraph” được thực hiện thông qua ứng dụng chatbot hỗ trợ trò chuyện về tâm lý bằng tiếng Việt. Một chatbot nhiều lượt cần quản lý ngữ cảnh, chọn công cụ và sử dụng kết quả tra cứu để tạo phản hồi. Vì vậy, em lựa chọn nghiên cứu cách tổ chức các bước này thành đồ thị trạng thái có luồng điều khiển rõ ràng.')
    p(doc, 'Mục tiêu của em là hiểu state, node, edge, nhánh điều kiện và checkpoint; đồng thời vận dụng phần việc được phân công vào chương trình chung. LangGraph phụ trách điều phối, còn các gói LangChain hỗ trợ giao tiếp mô hình, biểu diễn tin nhắn và công cụ. Kiến thức này giúp em rèn luyện lập trình Python, đọc mã nguồn và thiết kế ứng dụng AI.')

    doc.add_page_break()
    p(doc, '2. Tổng quan LangGraph và chương trình hiện tại', 'Heading 1')
    p(doc, '2.1. Vai trò của các thành phần', 'Heading 2')
    p(doc, 'LangGraph tổ chức xử lý bằng state dùng chung, node thực hiện tác vụ và edge quy định bước tiếp theo. Trong đồ án, StateGraph(MessagesState) quản lý tin nhắn; ToolNode thực thi công cụ; nhánh điều kiện đưa luồng về trợ lý hoặc kết thúc. Groq cung cấp dịch vụ mô hình qua ChatGroq; Tavily phục vụ tìm kiếm web; Hugging Face và FAISS hỗ trợ truy xuất tài liệu.')
    p(doc, '2.2. Luồng hội thoại và bộ nhớ', 'Heading 2')
    p(doc, 'Luồng chính: START → assistant → tools → assistant → END. Nhánh tools chỉ được thực hiện khi mô hình tạo tool_calls; các lượt trò chuyện thông thường có thể đi từ assistant đến END. END kết thúc lượt chạy hiện tại, không xóa lịch sử hội thoại. Hệ thống có một Agent hội thoại với hai công cụ, chưa phải kiến trúc nhiều Agent chuyên biệt.')
    p(doc, 'Agent Server quản lý checkpoint và state theo thread; graph triển khai không gắn checkpointer riêng. Frontend lưu mã thread trong sessionStorage, đọc lịch sử từ máy chủ và tạo thread khác khi chọn “Cuộc trò chuyện mới”. Cơ chế này duy trì ngữ cảnh trong cùng hội thoại; chưa triển khai bộ nhớ dài hạn chia sẻ giữa nhiều thread hoặc tài khoản người dùng.')
    p(doc, '2.3. RAG, API và giao diện', 'Heading 2')
    p(doc, 'rag_tool gọi đồ thị START → retrieve → answer → END để tra cứu Stress.pdf và tạo câu trả lời có hướng dẫn dẫn nguồn, số trang. search_web lấy kết quả từ Tavily. main.py dùng FastAPI để phục vụ HTML/CSS/JavaScript, còn các endpoint /threads và /runs/wait do Agent Server cung cấp. LangServe.py được giữ tương thích tên cũ; luồng hiện tại không dùng endpoint /chatbot của LangServe.')
    p(doc, '2.4. Giá trị học tập và định hướng nghề nghiệp', 'Heading 2')
    p(doc, 'Qua đề tài, em rèn luyện cách thiết kế trợ lý AI có trạng thái, tích hợp dữ liệu và dịch vụ bên ngoài, xử lý lỗi và kiểm tra hành vi. Đây là nhóm kỹ năng phù hợp với định hướng phát triển ứng dụng LLM, chatbot và backend. Báo cáo tập trung vào năng lực đã thực hành, không sử dụng số liệu cộng đồng hay thông tin tuyển dụng chưa được kiểm chứng.')

    doc.add_page_break()
    p(doc, '3. Nhiệm vụ và đóng góp cá nhân', 'Heading 1')
    p(doc, f'Trọng tâm công việc: {role}.')
    for i, (title, text) in enumerate(contributions, 1):
        p(doc, f'3.{i}. {title}', 'Heading 2')
        p(doc, text)

    doc.add_page_break()
    p(doc, '4. Khó khăn, cách khắc phục và kiểm tra', 'Heading 1')
    p(doc, 'Khó khăn chung là phân biệt ví dụ LangChain cũ với kiến trúc ứng dụng đã chuyển sang LangGraph, cùng các lỗi import và cấu hình dịch vụ. Cách xử lý là đối chiếu luồng chạy từ start_langgraph.py, langgraph.json đến graph.py và agent.py, dùng đúng Python trong .venv và cài các gói theo requirements.txt. Các script chain.py, btap1.py và notebook được giữ làm bài tập tham khảo.')
    if student_id == '3122410129':
        specific = 'Với RAG, cần theo dõi riêng từng bước đọc PDF, chia đoạn, tạo embedding và truy xuất trước khi xem câu trả lời của LLM. Lần sử dụng đầu có thể chậm do tải mô hình embedding. Câu trả lời có chỉ dẫn nguồn vẫn cần kiểm tra với trang tài liệu gốc; không xem RAG là cơ chế loại bỏ hoàn toàn thông tin sai.'
    elif student_id == '3122410269':
        specific = 'Với tìm kiếm web, cần phân biệt lỗi thiếu TAVILY_API_KEY, lỗi kết nối và trường hợp không có kết quả. Với bộ nhớ, cần thử hai thread khác nhau để tránh nhầm lịch sử giữa hội thoại. Mô hình chỉ sử dụng thông tin được cung cấp trong ngữ cảnh; không tự lưu mọi cuộc trò chuyện.'
    elif student_id == '3122410459':
        specific = 'Với môi trường, cần chọn đúng interpreter của .venv trong IDE và khởi động bằng script dự án. Chạy Live Server hoặc uvicorn main:app chỉ phục vụ giao diện sẽ không cung cấp đủ API threads/runs. Khi so sánh mô hình, cần giữ rõ danh sách tin nhắn đầu vào và phân biệt cấu hình bài tập với cấu hình Agent.'
    else:
        specific = 'Với Agent và API, cần phân biệt lỗi ở công cụ với lỗi gọi mô hình chính. Công cụ trả thông báo khi không tra cứu được; lỗi kết nối hoặc timeout của mô hình chính làm lượt chạy thất bại. Frontend hiển thị thông báo phù hợp và đọc lại state, không tự tạo câu trả lời giả hoặc tự gửi lại yêu cầu.'
    p(doc, specific)
    p(doc, 'Bộ kiểm thử hiện có trong tests dùng mô hình và công cụ giả để kiểm tra vòng gọi công cụ, phân tách bộ nhớ theo thread, truyền nội dung và số trang RAG, phục vụ giao diện, cùng lỗi kết nối/timeout. Các kiểm tra này xác minh hành vi kỹ thuật, không đo độ chính xác của mô hình thật hay hiệu quả hỗ trợ tâm lý. Lệnh chạy: .venv\\Scripts\\python.exe -m unittest discover -s tests -v.')
    p(doc, '5. Kết luận và hướng phát triển', 'Heading 1')
    p(doc, '5.1. Kết quả và giới hạn', 'Heading 2')
    p(doc, f'Qua phần việc {role.lower()}, em hiểu rõ hơn cách kết hợp mô hình ngôn ngữ với trạng thái, công cụ và API. Sản phẩm hiện tại là bản demo chatbot tiếng Việt trên LangGraph, có khả năng gọi công cụ tài liệu và tìm kiếm web. Chất lượng phản hồi phụ thuộc mô hình, dữ liệu và dịch vụ bên ngoài; chưa có số liệu đánh giá để khẳng định mức độ chính xác định lượng.')
    p(doc, 'Chatbot hỗ trợ trò chuyện, không thay thế chuyên gia, không chẩn đoán hoặc kê đơn. Ứng dụng cần Internet để gọi Groq và Tavily; không phải hệ thống hoàn toàn ngoại tuyến. Chế độ langgraph dev phục vụ phát triển cục bộ, chưa thể hiện một dịch vụ công khai có xác thực, phân quyền và quản trị dữ liệu đầy đủ.')
    p(doc, '5.2. Hướng phát triển', 'Heading 2')
    p(doc, 'Các bước tiếp theo gồm xây dựng bộ câu hỏi đánh giá và tracing/evaluation bằng LangSmith; cải thiện truy xuất, kiểm tra nguồn và quản lý lịch sử dài; bổ sung xác thực, chính sách lưu/xóa hội thoại và môi trường triển khai phù hợp. Streaming, Docker, bộ nhớ dài hạn và nhiều Agent chuyên biệt là các hướng mở rộng cần thiết kế, kiểm thử riêng, chưa được xem là chức năng đã hoàn thành.')
    p(doc, 'Tài liệu đối chiếu', 'Heading 1')
    for text in [
        'Mã nguồn dự án: agent.py, graph.py, Rag_tool.py, searchweb_tool.py, main.py, langgraph.json, frontend/app.js, start_langgraph.py, requirements.txt, README.md và tests/.',
        'Bài tập nền tảng: btap1.py, chain.py và các notebook trong dự án.',
        'LangGraph overview: https://docs.langchain.com/oss/python/langgraph/overview',
        'Persistence: https://docs.langchain.com/oss/python/langgraph/persistence',
        'Custom routes: https://docs.langchain.com/langsmith/custom-routes',
    ]:
        para = p(doc, text)
        for run in para.runs:
            run.font.size = Pt(11)
    target = OUT / f'{source.stem}_LangGraph.docx'
    doc.save(target)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None
    reopened = Document(target)
    text = '\n'.join(x.text for x in reopened.paragraphs)
    assert 'FRAMEWORK LANGGRAPH' in text and student_id in text and name in text
    assert 'FRAMEWORK LANGCHAIN' not in text
    return {'student_id': student_id, 'name': name, 'source': str(source), 'source_sha256': before,
            'output': str(target), 'paragraphs': len(reopened.paragraphs), 'words': len(text.split())}


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    records = [build(sid, *values) for sid, values in PEOPLE.items()]
    (OUT / 'kiem_tra.json').write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(records, ensure_ascii=False, indent=2))
