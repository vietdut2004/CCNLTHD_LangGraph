"""Bản đầy đủ: giữ nội dung giáo trình gốc, sửa sai và bổ sung đối chiếu source."""
from __future__ import annotations

import copy
import hashlib
import json
import re
import subprocess
import sys
from io import BytesIO
from pathlib import Path

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
HERE=Path(__file__).parent
ASSETS=HERE/'full_assets'; ASSETS.mkdir(exist_ok=True)
SOURCE=next(ROOT.parent.glob('*15*LangGraph.docx'))
CORRECTED=ROOT/'Bao_cao_nhom_15_LangGraph_da_chinh_sua.docx'
OUT=ROOT/'Bao_cao_nhom_15_LangGraph_day_du.docx'
doc=Document(SOURCE)
corrected=Document(CORRECTED)
original=list(doc._element.body)
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main'}

def get_text(e): return ''.join(x.text or '' for x in e.findall('.//w:t',NS))
original_word_count=sum(len(p.text.split()) for p in doc.paragraphs)

def rewrite(i,text):
    e=original[i]
    if e.tag!=qn('w:p'): raise ValueError(i)
    ts=e.findall('.//w:t',NS)
    if ts:
        ts[0].text=text
        for x in ts[1:]: x.text=''


# Sửa theo từng đoạn; giữ nguyên các chủ đề và ví dụ nền tảng thay vì thay tên hàng loạt.
REWRITES={
  43:'LangGraph giúp chúng em chuyển kiến thức về LLM và xử lý ngôn ngữ thành ứng dụng có luồng thực thi rõ ràng. Các thành phần cốt lõi là State, node, edge, reducer, checkpoint và cơ chế thực thi; prompt, mô hình và tool là các tích hợp được gọi trong node.',
  50:'Hiểu công nghệ LangGraph: nắm StateGraph, MessagesState, node, cạnh điều kiện, vòng gọi công cụ và lưu trạng thái theo thread. Đồng thời phân biệt những phần này với LLM, prompt, embedding và vector store thuộc các tích hợp bên ngoài.',
  51:'Phân tích các thành phần: đồ thị điều khiển đường đi của dữ liệu; node thực hiện công việc; cạnh quyết định bước tiếp theo; State giữ dữ liệu dùng chung. Agent của chương trình kết hợp các thành phần này với model và tool.',
  53:'Xây dựng RAG cho Stress.pdf bằng hai node retrieve và answer; nghiên cứu thêm việc mở rộng sang nguồn khác. Bản chương trình hiện tại chưa có chức năng nhận file DOCX hoặc tải tài liệu mới từ giao diện.',
  54:'Sử dụng embedding Hugging Face và FAISS để truy xuất các đoạn liên quan. ChromaDB và các vector database khác chỉ được xem là lựa chọn tham khảo, không phải thành phần đang chạy trong đồ án.',
  58:'Xây dựng chatbot mẫu có thể trò chuyện, dùng lịch sử theo thread, gọi rag_tool và search_web. Độ đúng của câu trả lời cần được đánh giá bằng dữ liệu thực nghiệm, không được suy ra chỉ từ việc sử dụng LangGraph hoặc RAG.',
  59:'Đánh giá logic bằng bộ kiểm thử hiện có; thiết kế quy trình đo tốc độ, token, nguồn trích dẫn và mức hữu ích trên bộ dữ liệu có đáp án. Chỉ công bố số đo của phiên bản có bằng chứng tương ứng.',
  75:'Quản lý hội thoại bằng MessagesState và checkpoint do LangGraph Agent Server cung cấp; ví dụ InMemorySaver được dùng trong kiểm thử cục bộ. MySQL là hướng nghiên cứu mở rộng, chưa có trong luồng chạy hiện tại.',
  76:'Xây dựng giao diện HTML/CSS/JavaScript. FastAPI phục vụ trang và tài nguyên tĩnh trong Agent Server; frontend dùng trực tiếp API threads/runs để chạy đồ thị.',
  137:'LangServe phục vụ LangChain Runnable qua HTTP và là công cụ tham khảo. Chương trình hiện tại dùng LangGraph Agent Server với API threads/runs; main.py chỉ cung cấp giao diện qua cấu hình http.app.',
  217:'Để dùng LangGraph cần môi trường Python và các phụ thuộc tương thích. LangGraph điều phối đồ thị có trạng thái; các gói tích hợp như langchain-groq, langchain-huggingface và langchain-community cung cấp model, embedding, loader và vector store bên trong node.',
  220:'Với chương trình này, chuẩn bị Python 3.11 trở lên theo README. Các bài ví dụ dùng dịch vụ ngoài cần khóa và model phù hợp; bài kiểm thử với mô hình giả không cần gọi nhà cung cấp.',
  225:'Tạo môi trường ảo thống nhất tên .venv: python -m venv .venv. Khi chạy có thể gọi trực tiếp .venv\\Scripts\\python.exe để tránh nhầm interpreter.',
  233:'Với dự án có sẵn, cài bằng python -m pip install -r requirements.txt. Tệp hiện chỉ khóa phiên bản langgraph-cli[inmem], vì vậy cần lưu thêm pip freeze nếu muốn tái lập đầy đủ môi trường.',
  240:'Khả năng kiểm soát: người phát triển có thể thêm node kiểm duyệt hoặc bước chờ con người, thiết kế checkpoint và điều kiện dừng. Đây là các khả năng của framework; chatbot hiện tại chưa triển khai node kiểm duyệt hoặc quy trình phê duyệt riêng.',
  241:'Mức trừu tượng thấp: StateGraph cho phép tự thiết kế State, node và cạnh để kiểm soát workflow. Multi-agent là một hướng có thể xây dựng thêm; ứng dụng hiện chỉ có một agent hội thoại với hai tool.',
  242:'Streaming: LangGraph có các chế độ phát dữ liệu trong khi chạy. Khả năng này phải được gọi và xử lý phù hợp ở client. Frontend hiện dùng runs/wait, đợi kết quả hoàn tất; chưa hiển thị token từng phần hay toàn bộ suy luận nội bộ của mô hình.',
  336:'Mục tiêu: hiểu sự khác nhau giữa lời gọi chỉ có câu hỏi hiện tại và lời gọi được truyền lại lịch sử. Đây là khác biệt về dữ liệu ứng dụng cung cấp, không phải hai loại mô hình có/không tự lưu bộ nhớ.',
  340:'Stateful ở cấp ứng dụng: chương trình lưu lại lịch sử rồi đưa phần liên quan vào các yêu cầu tiếp theo. Chat Model nhận danh sách tin nhắn nhưng không tự bảo đảm lưu trữ qua nhiều lần gọi API.',
  342:'Trong ví dụ sau, llm.invoke gọi trực tiếp ChatGroq với chuỗi hiện tại. Đây là API của đối tượng chat model, không phải graph.invoke của LangGraph; hai yêu cầu không được truyền lịch sử chung.',
  355:'Câu hỏi tiếp nối “Tên tôi là gì?”',
  356:'Kết quả minh họa trong ảnh cho thấy mô hình sử dụng thông tin “An” từ danh sách được truyền. Đây là ảnh của ví dụ học tập, không phải phép đo bộ nhớ của bản chatbot đang triển khai.',
  358:'Kết luận: việc nhận được lịch sử giúp model có thông tin để trả lời. Ứng dụng vẫn chịu trách nhiệm lưu lịch sử, chọn phần đưa vào context và kiểm tra câu trả lời.',
  371:'ChatPromptTemplate tạo ChatPromptValue khi invoke; có thể gọi to_messages() hoặc format_messages() để lấy danh sách message. Các lớp này thuộc langchain_core.prompts, không phải langgraph.prompts.',
  464:'Phần này giữ ví dụ LLMChain/SequentialChain để so sánh với cách tổ chức đồ thị. Chúng là API LangChain đời cũ, không nằm trong chatbot hiện tại và có thể cần môi trường phụ thuộc riêng. Dùng StateGraph giúp biểu đạt nhánh/vòng lặp; chưa có phép đo để kết luận luôn nhanh hơn chain.',
  473:'temperature=0.7 điều chỉnh lấy mẫu theo khả năng của nhà cung cấp. Giá trị thấp thường giảm tính ngẫu nhiên nhưng không bảo đảm đáp án đúng hay đầu ra giống hệt ở mọi lần chạy.',
  574:'Ảnh này minh họa initialize_agent/AgentExecutor của LangChain đời cũ và được giữ để đối chiếu kiến thức ban đầu. Đây không phải code chatbot đang triển khai. Ví dụ StateGraph và ToolNode tương ứng được trình bày bổ sung ở cuối chương và Chương 10; kết quả 100 là đáp án toán học kỳ vọng, không thay thế trace thực thi.',
  588:'Trong ví dụ OpenAIEmbeddings, chiều vector phụ thuộc model và tùy chọn dimensions. Ảnh ghi lại kết quả 1536 chiều của cấu hình ví dụ đó. Ứng dụng hiện tại dùng HuggingFaceEmbeddings, vì vậy không áp chiều 1536 cho FAISS của chương trình.',
  593:'CSDL quan hệ tổ chức truy vấn theo trường, điều kiện và chỉ mục; vector store hỗ trợ tìm lân cận theo vector. Hai cách có thể kết hợp; không nên hiểu rằng CSDL truyền thống chỉ có tìm khớp chuỗi hoặc vector search luôn chính xác về ngữ nghĩa.',
  595:'Các chỉ mục vector có thể tìm vét cạn hoặc gần đúng. ANN giúp cân bằng tốc độ, bộ nhớ và độ đầy đủ trên tập lớn; không phải mọi cấu hình FAISS đều là ANN.',
  600:'FAISS là thư viện tìm kiếm tương đồng vector. Tích hợp FAISS của LangChain kết hợp index, docstore và metadata để dùng như vector store. Nó không tự cung cấp toàn bộ chức năng máy chủ, phân quyền và giao dịch của một hệ quản trị cơ sở dữ liệu.',
  630:'normalize_embeddings=True chuẩn hóa vector về độ dài 1 để dùng với thước đo phù hợp. Đây là cấu hình bài học; nó không tự bảo đảm truy xuất chính xác hơn và không được truyền trong HuggingFaceEmbeddings của Rag_tool.py hiện tại.',
  634:'Vector hóa: mỗi câu được ánh xạ thành vector có số chiều do mô hình đã chọn xác định. Ví dụ bài học dùng model đa ngôn ngữ riêng; ứng dụng dùng model mặc định khác. Nên kiểm tra len(embeddings.embed_query(...)) thay vì suy đoán số chiều từ tên thư viện.',
  683:'Chuẩn bị dữ liệu cho RAG gồm đọc văn bản từ nguồn, chia đoạn, tạo embedding và lưu cùng metadata. Model sinh câu trả lời nhận các đoạn văn bản truy xuất được; không nhận trực tiếp chỉ mục FAISS như một prompt.',
  684:'Các bước nạp PDF, chia đoạn và embedding do các tích hợp LangChain/Hugging Face/FAISS thực hiện. LangGraph tổ chức chúng thành node và cạnh; không có các lớp langgraph.text_splitters hoặc langgraph.vectorstores trong code dự án.',
  687:'Bước nạp tài liệu có thể hỗ trợ nhiều định dạng nếu cài và cấu hình loader tương ứng. Trong ứng dụng này, nguồn được cố định ở Stress.pdf; giao diện chưa có nút tải file lên.',
  689:'Embedding: các đoạn được ánh xạ thành vector bởi mô hình embedding chuyên dụng. Cần phân biệt mô hình này với ChatGroq dùng để sinh câu trả lời.',
  696:'Ảnh trên là ví dụ dùng OpenAIEmbeddings. Với chương trình hiện tại, thay tích hợp này bằng HuggingFaceEmbeddings như mã thật của Rag_tool.py; phần thực hành bên dưới trình bày cấu hình tương ứng.',
  706:'RAG là một phương án bổ sung dữ liệu tham khảo vào context mà không cần huấn luyện lại model cho mỗi thay đổi tài liệu. Nó không loại bỏ hoàn toàn hallucination và không bảo đảm luôn là phương án tối ưu cho mọi ứng dụng.',
  710:'Câu hỏi được embedding, sau đó vector store tìm các đoạn gần nhất và lấy top-k. Reranking là bước có thể bổ sung riêng; mã FAISS của đề tài hiện không có reranker độc lập.',
  721:'Thực hành RAG trên tệp Stress.pdf có sẵn trong thư mục dự án. Mục tiêu là tái hiện các bước loader → splitter → embedding/FAISS → retrieve → answer, không giả định số trang hay số đoạn luôn cố định giữa các tài liệu.',
  727:'Đọc Stress.pdf cục bộ bằng đường dẫn tương đối theo thư mục dự án. Với Google Colab có thể mount Drive như bài học riêng; bản chạy Windows không cần Google Drive.',
  740:'Dùng GROQ_API_KEY cho bước gọi ChatGroq. Mô hình embedding mặc định được tải bằng tích hợp Hugging Face; mã chương trình không yêu cầu một HUGGINGFACEHUB_API_TOKEN cố định.',
  741:'Đọc khóa từ .env hoặc biến môi trường. Chỉ dùng getpass trong ví dụ nhập tương tác; không viết khóa trực tiếp vào code hoặc ảnh minh họa.',
  742:'Không dùng lại khóa xuất hiện trong ảnh minh họa cũ. Ảnh trong bản này đã được thay bằng đoạn cấu hình chỉ đọc tên biến môi trường, không chứa giá trị khóa.',
  743:'Bước 4: Định vị Stress.pdf và nạp các trang PDF',
  751:'RecursiveCharacterTextSplitter dùng danh sách dấu phân cách theo cấu hình; mặc định ưu tiên ngắt đoạn/dòng/khoảng trắng rồi ký tự. Nó không mặc nhiên hiểu mọi ranh giới câu tiếng Việt hoặc mọi cấu trúc mục của tài liệu.',
  754:'Ứng dụng chọn HuggingFaceEmbeddings với EMBEDDING_MODEL hoặc VoVanPhuc/sup-SimCSE-VietNamese-phobert-base. Số chiều cần được xác nhận từ vector thực tế/model card; FAISS.from_documents dựng index phù hợp từ embedding đầu vào.',
  757:'Mỗi chunk được chuyển thành vector; các con số trong bảng sau chỉ là minh họa biểu diễn, không phải vector được trích xuất thật từ lần chạy chương trình.',
  762:'FAISS lưu một vector cho mỗi chunk cùng liên kết tới văn bản và metadata. Số chunk phụ thuộc nội dung PDF, loader và cấu hình chia đoạn; con số 22 ở bảng minh họa không phải giá trị kiểm chứng cố định của bản hiện tại.',
  767:'Trong ví dụ học tập có thể dùng LLM chạy cục bộ; chatbot đang triển khai dùng ChatGroq. Đoạn đồ thị minh họa giữ tham số llm để phân biệt điều phối với nhà cung cấp model. Với chương trình thật, node có tên answer và lấy GROQ_MODEL từ môi trường.',
  768:'Các tùy chọn max_new_tokens hoặc device của Transformers thuộc ví dụ LLM cục bộ, không phải cấu hình của Rag_tool.py hiện tại. Node answer đang gọi ChatGroq với temperature=0, timeout=60 và max_retries=1.',
  773:'Ảnh sau được thay bằng ca kiểm thử RAG đang có trong tests/test_chatbot.py. Retriever và model được giả lập để kiểm tra việc đưa nội dung và số trang vào prompt; không coi đầu ra giả lập là câu trả lời model thật trên Stress.pdf.',
  783:'Ứng dụng hiện dùng MessagesState và persistence của Agent Server theo thread. Frontend gửi message mới vào thread hiện tại; assistant nhận lịch sử state đang có, không có mã cắt chỉ còn 5 tin. Unit test dùng InMemorySaver để kiểm tra lịch sử cùng thread và tách thread khác.',
  784:'Ví dụ InMemorySaver cục bộ mất dữ liệu khi tiến trình kết thúc. Runtime dev của Agent Server có cơ chế lưu cục bộ riêng; không đồng nhất hai môi trường. Các ảnh ConversationBufferWindowMemory dưới đây là bài học LangChain đời cũ, được giữ để so sánh và không chứng minh cấu hình memory của chatbot hiện tại.',
  812:'Chương này giữ lý thuyết cache và bài thực hành MySQL/FAISS để mở rộng kiến thức. Trong code chatbot hiện tại không có exact answer cache TTL 300 giây, không có giới hạn 128 đáp án và không có MySQL. Phần triển khai thực có tái sử dụng retriever/graph và cache tệp mô hình; phân tích chi tiết ở cuối chương.',
  816:'Cache đáp án có thể lưu RAM hoặc kho bền vững tùy thiết kế. Đây là mô tả kiến trúc tham khảo; không khẳng định ứng dụng hiện đã cache câu trả lời hoặc có số đo hit/miss.',
  866:'Ứng dụng hiện đăng ký RAGTOOL và SearchWebTool vào model bằng bind_tools. Mô hình quyết định tạo tool_calls; tools_condition chỉ kiểm tra sự hiện diện của yêu cầu công cụ. Không có node classify, không có trường mode định tuyến theo từ khóa trong graph hiện tại.',
  867:'Node assistant gọi ChatGroq với system prompt và lịch sử; nếu có tool_calls thì ToolNode chạy công cụ rồi quay lại assistant. Không có node grounded/refuse riêng và không đăng ký một tool tên LLMTool trong ứng dụng cuối.',
  872:'Ảnh trên trích Agent.create_agent() từ code hiện tại. Builder khai báo MessagesState, node assistant, ToolNode, cạnh điều kiện và cạnh lặp; chương trình không gọi create_react_agent hay initialize_agent trong graph này.',
  873:'Hai công cụ mặc định là RAGTOOL và SearchWebTool. Những ví dụ LLMTool/RetrieverTool ở tài liệu học khác không phải danh sách công cụ của ứng dụng đang chạy.',
  874:'Ảnh phía trên đã được thay bằng code Agent hiện tại. Mô hình mặc định là openai/gpt-oss-20b qua Groq, có thể đổi bởi GROQ_MODEL. Không gán kết quả hoặc model của các ảnh ví dụ cũ cho cấu hình này.',
  885:'Ví dụ toán học minh họa StateGraph và tool calling, không phải chức năng đã gắn vào chatbot. Bản hiện tại chỉ có rag_tool và search_web. Phần kiểm chứng ở Chương 13 chỉ liệt kê năm test có thật; không ghi nhận thêm executor toán nếu chưa chạy và lưu bằng chứng riêng.',
  888:'Các ví dụ add/multiply dưới đây giữ mục tiêu học tập về lược đồ tool, kết quả và lỗi. Ảnh lỗi AgentExecutor được thay bằng mã gọi tool trực tiếp; đó là bài test công cụ độc lập, chưa xác nhận Groq tự chọn tool.',
  889:'Thực hành 1: gọi add với a=5, b=6. Đáp án kỳ vọng là 11; không cần API model khi gọi tool trực tiếp.',
  890:'Chạy add.invoke với arguments hợp lệ. Muốn xác nhận đường đi trong agent cần thêm AIMessage chứa tool_calls, ToolMessage và phản hồi assistant; việc thấy số 11 trong văn bản chưa đủ chứng minh tool đã chạy.',
  891:'',
  892:'Kết quả kiểm thử cần phân biệt lỗi parse văn bản với lỗi lược đồ tool. Với typed tool, tham số sai kiểu được kiểm tra qua lược đồ Pydantic trước khi hàm số học chạy.',
  893:'Thực hành 2: gọi multiply với a=5, b=6. Đáp án kỳ vọng là 30. Đây là phép gọi công cụ trực tiếp, chưa phải lượt chạy LLM tự chọn công cụ.',
  894:'Cần lưu cả đầu vào, tên tool và kết quả thực thi khi nghiệm thu. Không sử dụng traceback parser của AgentExecutor cũ làm kết quả cho StateGraph mới.',
  895:'',
  896:'Với biểu thức nhiều bước, chương trình hoặc mô hình phải xác định thứ tự và truyền đầu ra bước trước làm đầu vào bước sau. Số cuối đúng chưa tự xác nhận rằng mọi bước công cụ đã được thực thi.',
  897:'Thực hành 3: tính (2 + 3) × 4 bằng hai lời gọi tool: add(2, 3), sau đó multiply(5, 4). Kết quả kỳ vọng là 20.',
  898:'Có thể ghép quy trình xác định này bằng StateGraph với hai node cộng và nhân; hoặc để LLM tạo tool_calls trong vòng assistant/tools. Hai thiết kế có mức kiểm soát khác nhau và cần bộ kiểm thử khác nhau.',
  899:'',
  900:'Phân biệt kiểm thử hàm, kiểm thử graph bằng model giả và đánh giá model thật. Chỉ lớp cuối mới trả lời được câu hỏi mô hình có tự lập kế hoạch và chọn công cụ đúng hay không.',
  1063:'Bản source hiện tại có năm unit test về vòng gọi tool, lịch sử thread, truyền context/trang, phục vụ giao diện và ẩn chi tiết lỗi RAG; cả năm đã đạt trong lần kiểm tra được lưu kèm. Chưa có điểm chấm nội dung hoặc benchmark model thật mới. Các kết quả 57 test, điểm RAG/web và nhánh bàn giao của bản evidence-v1.3 không được gán cho phiên bản này.',
  1065:'Frontend giao tiếp trực tiếp với API threads/runs của LangGraph Agent Server ở cổng 2024. FastAPI tùy chỉnh phục vụ trang và static. Các con số latency, token và mã lỗi tùy chỉnh của endpoint /chatbot cũ không còn được báo cáo như kết quả của mã nguồn hiện tại; cần chạy phép đo mới theo phương pháp Chương 13.',
  1080:'Bản hiện tại đã có năm unit test về đồ thị, context RAG, lịch sử và giao diện. Chưa có bộ chấm nội dung model thật hoặc đánh giá độc lập nhiều người cho phiên bản này; cần xây dựng tập câu hỏi và rubric trước khi công bố điểm chất lượng.',
  1082:'Cần đo riêng lượt hội thoại, RAG và web theo cấu hình hiện tại. Chưa có dữ liệu về tải đồng thời, p50/p95 hoặc phân rã thời gian để kết luận điểm nghẽn của phiên bản đang bàn giao.',
  1128:'FAISS và các loại chỉ mục: https://github.com/facebookresearch/faiss/wiki',
  1129:'Mô hình embedding mặc định của chương trình: https://huggingface.co/VoVanPhuc/sup-SimCSE-VietNamese-phobert-base',
  1135:'Lab cốt lõi sau dùng hàm Python theo luật, không gọi LLM hay cần API key: khai báo State, node/cạnh, compile, kiểm tra thread_id và ghi latency/lỗi. Người học tạo các file lab_graph.py, metrics.py và lab_run.py theo mã in trong phụ lục; không giả định dự án hiện có các thư mục labs/starter hoặc labs/solution.',
  1141:'python -m pip install langgraph==1.2.14 langchain-core==1.6.9',
  1143:'Trên macOS/Linux, kích hoạt bằng source .venv/bin/activate. Ghi python --version và pip freeze để tái lập. Ví dụ dùng các API hiện có trong môi trường dự án đối chiếu (langgraph 1.2.14, langchain-core 1.6.9). Lab không phụ thuộc khóa nhà cung cấp; người học cần chạy lại để ghi kết quả trên máy của mình.',
}
for i,t in REWRITES.items():
    if original[i].tag==qn('w:p'): rewrite(i,t)

# Xác định và cập nhật style cho nội dung mới; không làm mất định dạng bìa gốc.
for key in ['Heading 1','Heading 2','Heading 3']:
    try: style=doc.styles[key]
    except KeyError: style=doc.styles.add_style(key,WD_STYLE_TYPE.PARAGRAPH)
    style.font.name='Times New Roman'; style.font.size=Pt(16 if key=='Heading 1' else 14)
    style.font.color.rgb=RGBColor.from_string('17365D')
    style.paragraph_format.keep_with_next=True
    style.paragraph_format.page_break_before=False
    style.paragraph_format.space_before=Pt(12); style.paragraph_format.space_after=Pt(8)
doc.styles['Heading 1'].paragraph_format.page_break_before=True
try: normal=doc.styles['Normal']
except KeyError: normal=doc.styles.add_style('Normal',WD_STYLE_TYPE.PARAGRAPH)
normal.font.name='Times New Roman'; normal.font.size=Pt(13)
normal.paragraph_format.line_spacing=1.15;normal.paragraph_format.space_after=Pt(6)
for s in doc.sections:
    s.page_width=Cm(21);s.page_height=Cm(29.7)
    s.left_margin=Cm(3);s.right_margin=Cm(2);s.top_margin=Cm(2);s.bottom_margin=Cm(2)
    for p in s.footer.paragraphs:p.clear()
    p=s.footer.paragraphs[0];p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');p._p.append(field)

def para(text,style=None):
    p=doc.add_paragraph(text,style=style)
    if not style:p.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
    return p._p

def heading(text,level=2):return para(text,'Heading '+str(level))

def codeblock(text):
    out=[]
    for line in text.strip('\n').splitlines():
        p=doc.add_paragraph()
        p.paragraph_format.space_after=Pt(0);p.paragraph_format.line_spacing=1
        r=p.add_run(line or ' ');r.font.name='Consolas';r.font.size=Pt(9)
        out.append(p._p)
    return out

def table(headers,rows):
    t=doc.add_table(rows=1,cols=len(headers))
    for c,x in zip(t.rows[0].cells,headers):c.text=x
    for row in rows:
        for c,x in zip(t.add_row().cells,row):c.text=str(x)
    pr=t._tbl.tblPr;borders=OxmlElement('w:tblBorders')
    for edge in ['top','left','bottom','right','insideH','insideV']:
        node=OxmlElement('w:'+edge);node.set(qn('w:val'),'single');node.set(qn('w:sz'),'4');node.set(qn('w:color'),'AAB9CC');borders.append(node)
    pr.append(borders)
    repeat=OxmlElement('w:tblHeader');t.rows[0]._tr.get_or_add_trPr().append(repeat)
    for row in t.rows:
        nosplit=OxmlElement('w:cantSplit');row._tr.get_or_add_trPr().append(nosplit)
        for c in row.cells:
            for p in c.paragraphs:
                p.paragraph_format.space_after=Pt(4)
                for r in p.runs:r.font.name='Times New Roman';r.font.size=Pt(11)
    return t._tbl

def card(name,title,code):
    lines=[]
    for line in code.strip().splitlines():
        lines.append(line)
    font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',25)
    test=ImageDraw.Draw(Image.new('RGB',(1,1)))
    width=max(1200,int(max(test.textlength(l,font=font) for l in lines))+100)
    im=Image.new('RGB',(width,115+len(lines)*36),'#f6f8fc');d=ImageDraw.Draw(im)
    d.text((35,25),title,font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',28),fill='#214b82')
    for i,line in enumerate(lines):d.text((35,95+i*36),line,font=font,fill='#182e4c')
    path=ASSETS/(name+'.png');im.save(path);return path

def source_card(name,filename,start=1,end=None):
    lines=(ROOT/filename).read_text(encoding='utf-8').splitlines()
    end=end or len(lines)
    return card(name,f'{filename} | dòng {start}–{end}', '\n'.join(f'{i:3}  {lines[i-1]}' for i in range(start,min(end,len(lines))+1)))

def picture(path,caption,width=15.3):
    p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.keep_with_next=True
    p.add_run().add_picture(str(path),width=Cm(width))
    c=doc.add_paragraph(caption);c.alignment=WD_ALIGN_PARAGRAPH.CENTER
    for r in c.runs:r.font.size=Pt(10);r.italic=True
    return [p._p,c._p]

def replace_picture(i,path,caption):
    # Dựng lại ảnh và kích thước theo tỷ lệ mới; không kéo méo vào khung ảnh cũ.
    replacement=picture(path,caption)
    return replacement

def clone_from_corrected(element):
    e=copy.deepcopy(element)
    for node in e.iter():
        for key,value in list(node.attrib.items()):
            if not key.startswith('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'):
                continue
            if value not in corrected.part.rels:continue
            rel=corrected.part.rels[value]
            if rel.reltype.endswith('/image'):
                rid,_=doc.part.get_or_add_image(BytesIO(rel.target_part.blob))
                node.set(key,rid)
            elif rel.is_external:
                node.set(key,doc.part.rels.get_or_add_ext_rel(rel.reltype,rel.target_ref))
    return e

# Các đoạn trong bản ngắn là phần đối chiếu đúng; ghép thêm vào đúng chương gốc.
chapter_content={}
current=None
for e in corrected._element.body:
    text=get_text(e).strip()
    match=re.match(r'Chương (\d+)\.',text)
    if match:
        current=int(match.group(1));chapter_content[current]=[];continue
    if text.startswith(('Phần ','Tài liệu tham khảo','Phụ lục ','Danh mục hình')):current=None
    if current is not None and e.tag!=qn('w:sectPr'):chapter_content[current].append(e)

def current_section(number):
    blocks=[heading(f'{number}. Đối chiếu với mã nguồn chương trình hiện tại',2)]
    for e in chapter_content[number]:
        new=clone_from_corrected(e)
        if new.tag==qn('w:p'):
            st=new.find('w:pPr/w:pStyle',NS)
            if st is not None and st.get(qn('w:val'))=='Heading2':st.set(qn('w:val'),doc.styles['Heading 3'].style_id)
        blocks.append(new)
    return blocks


# Thay các ảnh sai luồng, chứa cấu hình cũ hoặc kết quả không tương ứng bằng ảnh mới.
replaced={
  99:picture(HERE/'assets/conversation.png','Sơ đồ điều phối hiện tại: assistant → tools → assistant; kết thúc khi không còn tool_calls.'),
  227:picture(card('install','Môi trường của dự án trên Windows',r'''
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -c "import sys; print(sys.executable)"
.\run_langgraph.bat
# Giao diện: http://127.0.0.1:2024
'''),'Khởi tạo môi trường và chạy đúng Agent Server; không bắt buộc activate nếu gọi Python theo đường dẫn.'),
  576:picture(HERE/'assets/ui.png','Giao diện hiện tại chụp từ http://127.0.0.1:2024; chưa có hội thoại model thật trong ảnh.'),
  686:picture(HERE/'assets/rag.png','RAG hiện tại gồm retrieve và answer; không có grade context hoặc validate.'),
  735:picture(card('rag_install','Cài các phụ thuộc theo chương trình',r'''
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
# PDF: pypdf, langchain-community
# Chunking: langchain-text-splitters
# Embedding: langchain-huggingface, sentence-transformers
# Vector: faiss-cpu
# Model: langchain-groq
# Điều phối: langgraph
'''),'Các gói RAG đang dùng trong requirements.txt; không cài RetrievalQA cho luồng hiện tại.'),
  737:picture(card('rag_imports','Import tương ứng các bước RAG', '''
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
# Rag_tool.py dùng các import nặng trong hàm khi cần.
'''),'Lớp loader, embedding và vector store đến từ các tích hợp, còn StateGraph/START/END đến từ LangGraph.'),
  739:picture(card('env_safe','Cấu hình khóa qua môi trường — không chứa khóa thật', '''
import os
from dotenv import load_dotenv

load_dotenv()
groq_key = os.getenv("GROQ_API_KEY")
model_name = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
# Không print(groq_key); không đưa giá trị khóa vào ảnh/báo cáo.
if not groq_key:
    raise ValueError("Hãy cấu hình GROQ_API_KEY trong .env")
'''),'Thay ảnh cấu hình cũ bằng mã chỉ đọc biến môi trường, không chứa giá trị API key.'),
  744:picture(card('pdf_local','Đọc PDF cục bộ — ví dụ chạy tại thư mục dự án', '''
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader

pdf_path = Path("Stress.pdf").resolve()
if not pdf_path.exists():
    raise FileNotFoundError(pdf_path)
docs = PyPDFLoader(str(pdf_path)).load()
print("Số trang được nạp:", len(docs))
# Trong RAGTOOL, đường dẫn tương đối được quy về PROJECT_DIR.
'''),'Không cần mount Google Drive để chạy chatbot trên Windows.'),
  774:picture(source_card('rag_test','tests/test_chatbot.py',61,86),'Ca kiểm thử RAG với retriever và model giả; kiểm tra context và số trang, không phải đầu ra Groq thật.'),
  871:picture(HERE/'assets/agent_code.png','Agent.create_agent() hiện tại: StateGraph(MessagesState), ToolNode và tools_condition.'),
}

for i,expr in [(889,'add.invoke({"a": 5, "b": 6})'),(893,'multiply.invoke({"a": 5, "b": 6})'),(897,'multiply.invoke({"a": add.invoke({"a": 2, "b": 3}), "b": 4})')]:
    replaced[i]=[para(REWRITES[i])]+picture(card(f'math_{i}','Bài thực hành công cụ độc lập — không dùng API model',f'from langchain_core.tools import tool\n\n@tool\ndef add(a: float, b: float) -> float:\n    """Cộng hai số."""\n    return a + b\n\n@tool\ndef multiply(a: float, b: float) -> float:\n    """Nhân hai số."""\n    return a * b\n\nprint({expr})'), 'Mã bài tập minh họa, không phải danh sách tool của chatbot. Chạy mã để thu kết quả trên môi trường của người học.')
for i in [891,895,899]:replaced[i]=[]


# Phân tích bổ sung giúp giữ độ sâu lý thuyết và kết nối từng chủ đề với chương trình.
ADDITIONS={
1:[
('1.3. Ba lớp cần phân biệt khi đọc kiến trúc',[
'Lớp điều phối xác định bước nào được chạy và dữ liệu nào được cập nhật; trong đồ án đó là StateGraph. Lớp năng lực thực hiện công việc cụ thể: ChatGroq gọi LLM, FAISS tìm vector, Tavily tìm kiếm web. Lớp phục vụ ứng dụng tiếp nhận HTTP và quản lý các lần chạy: Agent Server cung cấp thread/run, còn FastAPI app tùy chỉnh phục vụ giao diện. Nhầm ba lớp này thường dẫn đến phát biểu sai như “LangGraph là model”, “FAISS tự sinh đáp án” hoặc “main.py có toàn bộ API hội thoại”.',
'Một lợi ích của đồ thị là có thể xác định đầu vào và đầu ra của từng bước. Tuy nhiên khả năng quan sát không thay thế việc đánh giá chất lượng. Một run đi đúng START–assistant–END vẫn có thể trả lời thiếu ý; một run gọi đúng rag_tool vẫn có thể truy xuất đoạn không đủ thông tin. Vì vậy báo cáo tách tính đúng của luồng khỏi độ đúng của nội dung.',
'Các tính năng chung như streaming, human-in-the-loop, time travel, store và nhiều agent là những khả năng của hệ sinh thái. Chỉ ghi chúng là tính năng của sản phẩm khi đã có node/cấu hình/API và bằng chứng kiểm tra. Trong phiên bản này, trọng tâm triển khai là message state, tool loop, RAG hai bước và thread persistence.']),
('1.4. Đọc một lượt chạy theo dữ liệu',[
'Có thể theo dõi bốn câu hỏi khi đọc chương trình: dữ liệu nào đi vào, node nào đọc dữ liệu, node trả những khóa gì và cạnh nào chọn bước tiếp theo. Với assistant, dữ liệu là messages; với retrieve, dữ liệu là query; với answer của RAG, dữ liệu là query và context. Đầu ra không phải lúc nào cũng là chuỗi: lời gọi graph trả state, còn tool rag_tool rút trường answer thành chuỗi để gửi về ToolNode.',
'State không nên được vẽ như một tác vụ tuần tự nằm giữa mọi node. Nó là dữ liệu chung được node đọc và cập nhật. Checkpointer cũng không phải một node bắt buộc sau mỗi tool; đó là cơ chế runtime lưu trạng thái theo điểm kiểm tra. Các hình mới trong báo cáo được bố trí theo đúng hai vai trò này.'])],
3:[('3.4. Kiểm tra interpreter, thư viện và cấu hình',[
'Lỗi thường gặp trên Windows là terminal trỏ tới Python toàn cục còn trình chạy trỏ tới .venv, hoặc di chuyển thư mục khiến launcher cũ không còn hợp lệ. Cần kiểm tra sys.executable bằng đúng interpreter dùng khởi chạy. start_langgraph.py gọi python -m langgraph_cli để tránh phụ thuộc trực tiếp vào launcher exe đã bị đổi đường dẫn.',
'Nếu máy chủ không mở được giao diện, kiểm tra theo thứ tự: có import được langgraph_cli hay không, langgraph.json có đọc được không, GROQ_API_KEY có tồn tại không, graph có đăng ký được không và /ok có phản hồi không. Đây là kiểm tra khởi chạy, chưa phải kiểm tra model trả lời. Một API key có mặt nhưng sai giá trị có thể không làm lỗi ở bước dựng model mà chỉ lỗi khi gửi câu hỏi.',
'Khi chỉ dùng lời chào thì có thể chưa tạo embedding hay dựng FAISS vì RAG khởi tạo trễ. Vì vậy “server khởi động được” không đồng nghĩa “PDF đã truy xuất được”. Nên dành một ca nghiệm thu riêng cho lần đầu gọi RAG, nhất là trên máy chưa có mô hình trong cache.',
'README, requirements.txt và langgraph.json là ba tệp cần đọc cùng nhau: README mô tả cách chạy; requirements mô tả phụ thuộc; langgraph.json mô tả graph và ứng dụng HTTP được nạp. Tên run_api.bat được giữ để thuận tiện khởi chạy nhưng không có nghĩa máy chủ đang là endpoint /chatbot cũ.'])],
4:[('4. Bổ sung: reducer, cập nhật State và lời gọi bất đồng bộ',[
'Với một TypedDict thông thường, trả về cùng một khóa thường thay giá trị của khóa đó theo cơ chế mặc định. Với MessagesState, khóa messages có reducer cho message nên node có thể chỉ trả reply mới. Đó là lý do assistant không trả lại toàn bộ lịch sử đã nhận: nếu tự nối lại không đúng chính sách có thể làm lặp hoặc cập nhật sai message.',
'Reducer không phải bộ nhớ dài hạn. Nó quy định cách gộp cập nhật trong quá trình thực thi. Checkpointer mới giữ state để lần chạy kế tiếp với cùng thread tiếp tục từ dữ liệu đã có. Store phục vụ dữ liệu ứng dụng cần dùng ngoài phạm vi một thread. Ba khái niệm này giải quyết ba vấn đề khác nhau và không thể thay thế bằng một biến list cục bộ khi triển khai nhiều phiên.',
'Hàm assistant được khai báo async và dùng ainvoke để nhường thời gian chờ I/O cho event loop. Điều này không làm bản thân LLM tính toán nhanh hơn và cũng không chứng minh máy chủ chịu được số lượng người dùng cụ thể. Trong RAG, các hàm retrieve/answer là hàm đồng bộ; ToolNode và runtime đảm nhiệm cách thực thi phù hợp. Muốn kết luận năng lực xử lý đồng thời cần đo tải thực tế.',
'System prompt được ghép trước messages mỗi khi assistant gọi model. Đồ thị lưu các message được trao đổi và kết quả tool; prompt hệ thống trong code được thêm vào lời gọi, không tự động trở thành một message mới trong state sau mỗi lượt. Việc phân biệt giúp tránh tưởng rằng lịch sử có hàng chục bản sao system prompt.',
'Khi có tool_calls, phản hồi AI thường chưa phải câu trả lời cuối cho người dùng. ToolMessage ghi kết quả ứng với tool_call_id để model biết kết quả nào trả cho yêu cầu nào. Frontend hiện ẩn message AI đang yêu cầu tool và message tool, chỉ giữ tin người dùng cùng phản hồi trợ lý cuối để giao diện không lộ các dữ liệu trung gian không cần thiết.']),
('4. Bổ sung: đối chiếu chain với graph bằng cùng tác vụ',[
'Với tác vụ tóm tắt rồi dịch, chain tuyến tính biểu diễn tốt thứ tự cố định. StateGraph cũng biểu diễn được bằng các khóa text, summary, translation và hai node nối nhau. Lợi ích của graph xuất hiện rõ hơn khi cần kiểm tra đầu vào, rẽ nhánh khi thiếu văn bản, thử lại hoặc gọi công cụ rồi quay về model. Không cần phủ nhận chain mới giải thích được ưu điểm của graph.',
'Ví dụ LLMChain và SequentialChain trong phần đầu chương được giữ làm đối chiếu lịch sử. Muốn tái hiện đúng các import cũ phải dùng môi trường phù hợp; không cài chồng chúng vào môi trường chatbot chỉ để chạy lại ảnh cũ. Cách học hữu ích là chuyển cùng nhiệm vụ sang hai node StateGraph và giải thích khóa nào được cập nhật ở mỗi node.',
'Một lỗi trình bày thường gặp là đổi mọi từ Chain thành Graph nhưng vẫn giữ lớp LLMChain và tham số chains trong hình. Bản báo cáo này giữ đúng tên API và nêu rõ phạm vi. Các đoạn thực thi chatbot chỉ dùng những tên có thật trong source hiện tại.'])],
5:[('5.3. Khoảng cách vector, chuẩn hóa và cách đọc score',[
'Khoảng cách L2, tích vô hướng và cosine similarity có cách diễn giải khác nhau. Với L2, khoảng cách nhỏ hơn thường gần hơn; với similarity, giá trị lớn hơn thường gần hơn. Một con số score từ wrapper không nên được gọi là xác suất đáp án đúng. Phải đọc cấu hình index và hàm trả score trước khi so sánh.',
'Nếu chuẩn hóa các vector về độ dài một, một số thước đo có quan hệ toán học thuận tiện; tuy nhiên không nên tự bật chuẩn hóa rồi coi kết quả cũ còn tương đương. Trong Rag_tool.py hiện tại, HuggingFaceEmbeddings không nhận encode_kwargs normalize_embeddings từ code. Hình thực hành semantic search riêng có cấu hình này thì chỉ áp dụng cho bài thực hành đó.',
'Embedding tốt cho ngữ nghĩa chung vẫn có thể nhầm các câu chỉ khác phủ định, con số hoặc điều kiện áp dụng. Chẳng hạn câu hỏi “không nên làm gì” có thể gần một đoạn nêu “nên làm gì” vì chia sẻ nhiều từ. Cần có câu thử về phủ định và thông số để đánh giá truy xuất, thay vì chỉ chọn các câu gần nguyên văn tài liệu.',
'Khi thay EMBEDDING_MODEL, cần tạo lại index và dùng cùng model cho query lẫn documents. Một index tạo bằng không gian embedding cũ không thể mặc nhiên nhận query từ model mới dù cùng số chiều. Sự tương thích ở cấp kích thước không bảo đảm vector biểu diễn cùng ý nghĩa.']),
('5.4. Metadata và vòng đời chỉ mục trong chương trình',[
'FAISS index chỉ giữ vector và ánh xạ; text và metadata được quản lý cùng docstore trong wrapper. Metadata page từ PDF được dùng để đưa tên tài liệu/trang vào context. Nếu tách metadata khỏi text khi sửa pipeline, câu trả lời có thể mất nguồn dù truy xuất vẫn lấy được nội dung.',
'Trong bản hiện tại, retriever được dựng từ PDF trong bộ nhớ khi tool cần dùng lần đầu. Không có thao tác lưu index lên đĩa bằng save_local; thư mục cache Hugging Face chỉ giữ tệp mô hình. Khi sửa Stress.pdf trong lúc tiến trình đang giữ retriever, mã không tự theo dõi thay đổi để xây index mới. Nghiệm thu với tài liệu mới cần bảo đảm tiến trình/tài nguyên được khởi tạo lại đúng cách.'])],
6:[('6.1. Lựa chọn kích thước đoạn và cách đánh giá',[
'Đoạn quá ngắn có thể tách tên kỹ thuật khỏi các bước thực hiện; đoạn quá dài có thể lẫn nhiều chủ đề và tiêu tốn context. Overlap giúp giữ mạch ở ranh giới nhưng cũng tạo trùng lặp. Vì vậy không có một cặp chunk_size/chunk_overlap tối ưu chung cho mọi PDF; 500/50 là cấu hình được chọn trong code, cần được đánh giá theo nội dung cụ thể.',
'Một phương pháp đánh giá là chuẩn bị câu hỏi có đáp án và đánh dấu trước những trang/đoạn chứa bằng chứng. Sau đó so sánh các cấu hình chunk bằng tỷ lệ truy xuất lấy được bằng chứng trong top-k. Chỉ sau khi truy xuất đủ mới đánh giá mô hình có diễn đạt đầy đủ và dẫn đúng trang hay không. Cách này giúp tránh sửa prompt khi nguyên nhân thật nằm ở việc chia đoạn.',
'PDF có thể chứa dòng ngắt bất thường, đầu/chân trang hoặc văn bản được trích xuất không đúng thứ tự. Kiểm tra một vài trang đầu chưa đủ xác nhận toàn tài liệu. Cần kiểm tra các trang có đáp án được dùng trong bộ câu hỏi, đặc biệt với bảng, gạch đầu dòng và ký hiệu. Mã hiện không có OCR hoặc bước chuẩn hóa bảng riêng.',
'Đơn vị ký tự khác token. Một chuỗi tiếng Việt có thể thành nhiều token theo tokenizer của model sinh câu trả lời, trong khi splitter mặc định tính chiều dài văn bản. Việc ghi đúng đơn vị giúp người đọc không hiểu nhầm rằng chunk 500 ký tự chắc chắn tương ứng một số token cố định.'])],
7:[('7.4. Phân tích hợp đồng dữ liệu giữa retrieve và answer',[
'Query là chuỗi yêu cầu đã được tool nhận từ model, có thể được mô hình viết lại so với câu hỏi gốc của người dùng. Retrieve dùng query để tìm Document rồi ghép context. Answer dùng lại chính query đó cùng context. Code chưa truyền toàn bộ lịch sử hội thoại vào RAGState, vì vậy một câu hỏi rút gọn phụ thuộc lượt trước chỉ có thể truy xuất tốt nếu model đã đưa đủ ý vào arguments query.',
'Context được ghép với tiền tố [Stress.pdf, trang N]. Điều này giúp model có thông tin nguồn nhưng không buộc đầu ra phải tuân thủ một lược đồ citation. Nếu cần kiểm tra tự động, có thể thêm source ID, schema trả lời và bước xác thực ID trong tập truy xuất. Các bước này chưa tồn tại trong bản hiện tại, nên báo cáo không vẽ chúng như node đang chạy.',
'Điều kiện “context không rỗng” chỉ chứng minh có văn bản được lấy về. FAISS top-k thường vẫn trả các đoạn gần nhất kể cả khi câu hỏi ngoài tài liệu. Không có ngưỡng score nghĩa là answer vẫn có thể nhận context không đủ ý. System prompt yêu cầu nói rõ khi thiếu thông tin nhưng hiệu quả phải được kiểm tra bằng các ca ngoài nguồn.',
'Ngoài lỗi đọc PDF hay thiếu API key, RAG có thể thất bại âm thầm: lấy nhầm đoạn, bỏ sót một phần đáp án, dẫn trang không hỗ trợ nội dung hoặc suy diễn từ kiến thức nền. Đây là các lỗi chất lượng khác với exception. Bắt exception và trả thông báo chung không thay thế bộ chấm nội dung.']),
('7.5. Phân rã chi phí và thiết kế thí nghiệm',[
'Một lượt RAG của chatbot có thể gồm nhiều lần gọi model: assistant quyết định gọi tool; answer trong RAG tạo câu trả lời từ tài liệu; assistant nhận ToolMessage rồi tổng hợp. Nếu model gọi thêm tool, số lần tăng tiếp. Vì vậy đo riêng node answer sẽ không phản ánh latency và token của cả lượt người dùng.',
'Lần gọi RAG đầu có thể phải tải embedding, đọc PDF và xây index. Những lần sau tái sử dụng retriever trong cùng đối tượng. Để đánh giá công bằng, cần ghi rõ phép đo bao gồm hay loại giai đoạn chuẩn bị này; không trộn kết nối lạnh với các lần đã sẵn sàng rồi công bố một con số đại diện mà không giải thích.',
'Cần tách ba lớp chỉ số: truy xuất lấy đúng bằng chứng, sinh đáp án đúng với bằng chứng và trải nghiệm end-to-end gồm thời gian/lỗi. Một cải tiến về tốc độ không tự làm câu trả lời chính xác hơn. Ngược lại, thêm bước kiểm chứng có thể tăng thời gian nhưng giảm trích dẫn sai; đó là đánh đổi cần đo.'])],
8:[('8.4. Thực hành MessagesState và InMemorySaver',[
'Để chuyển từ ví dụ buffer cũ sang LangGraph, trước hết dùng MessagesState cho schema, trả một AIMessage mới từ node và compile với InMemorySaver trong bài thực hành cục bộ. Mỗi lần gọi truyền configurable.thread_id. Cùng ID thì tiếp nối state; ID khác thì tạo lịch sử riêng. Không truyền lại toàn bộ lịch sử đã có cùng một message mới nếu mục tiêu là tránh lặp nội dung.',
'Bộ test hiện có dùng FakeModel: khi không có tool, model giả nối các HumanMessage đã nhận. Nhờ vậy kiểm tra được lịch sử có thật sự truyền tới model mà không cần dựa vào một LLM đôi lúc trả lời khác nhau. Nhưng test này không đánh giá mức hiểu tên, cảm xúc hoặc quan hệ giữa các phát ngôn của người dùng.',
'Muốn kiểm tra model thật nhớ đúng, cần thiết kế các cặp lượt: giới thiệu tên; cung cấp thông tin khác; hỏi lại tên; sửa tên; hỏi lại tên sau sửa. Đáp án kỳ vọng cần ghi trước. Thử cùng thread và thread mới để phân biệt dùng đúng lịch sử với đoán theo nội dung câu hỏi. Khi ghi log phải tránh dùng dữ liệu nhạy cảm của người thật.',
'Trong frontend, sessionStorage lưu mã thread trong phạm vi tab. Nội dung messages thuộc server. Việc tạo thread mới không xóa thread cũ trên server, nên không nên gọi nút này là “xóa dữ liệu”. Nếu cần chức năng xóa, phải bổ sung API và chính sách xóa rõ ràng, sau đó kiểm tra lại trên persistence backend.']),
('8.5. Quản lý context và bộ nhớ dài hạn',[
'MessagesState có thể tăng dần qua nhiều lượt, bao gồm cả message công cụ. Model chỉ có cửa sổ context hữu hạn. Một chính sách sản xuất có thể giữ phần gần nhất, tóm tắt phần cũ hoặc truy xuất thông tin quan trọng. Mỗi chính sách cần được kiểm tra với thông tin đã sửa, phủ định và dữ kiện có thời điểm để tránh nhớ nhầm.',
'Tóm tắt không phải sao chép nguyên lịch sử sang chuỗi ngắn hơn một cách chắc chắn không mất ý. Model tóm tắt có thể bỏ thông tin quan trọng hoặc suy diễn. Cần lưu vai trò và nguồn của thông tin; không để một câu cũ của người dùng bị biến thành chỉ dẫn hệ thống. Bản hiện tại chưa có node tóm tắt, nên đây là hướng phát triển.',
'Store và checkpoint có phạm vi khác nhau. Checkpoint phục vụ trạng thái một thread; store có thể giữ thông tin có chủ đích dùng qua nhiều thread. Trước khi thêm store cho sở thích cá nhân, cần xác định người dùng nào có quyền đọc/ghi và khi nào thông tin được xóa. Chỉ có thread_id do client nắm giữ chưa phải hệ thống định danh tài khoản.'])],
9:[('9.3. Phân biệt bốn kiểu tái sử dụng',[
'Cache tệp model giữ trọng số đã tải để không tải lại. Cache tài nguyên trong đối tượng giữ retriever hoặc graph để không dựng lại. Cache câu trả lời giữ kết quả theo khóa đầu vào. Checkpoint giữ trạng thái thực thi để tiếp tục thread. Cả bốn có thể tiết kiệm một số công việc nhưng có dữ liệu, khóa và vòng đời khác nhau.',
'Trong chatbot hiện tại, _retriever được giữ sau lần tạo đầu và _graph được giữ sau compile. Lock bao quanh phần dựng retriever giúp giảm việc hai lời gọi cùng đối tượng cùng tạo index. Không có bảng câu hỏi–câu trả lời, không có TTL và không có phép so ngữ nghĩa để trả đáp án cũ thay cho LLM.',
'Một cache đáp án được bổ sung trong tương lai phải tính đến model, prompt, phiên bản PDF, ngữ cảnh thread và giới hạn riêng tư. Hai người hỏi cùng chuỗi nhưng có lịch sử khác nhau có thể cần đáp án khác nhau. Dùng mỗi câu hỏi làm khóa cho chatbot có ngữ cảnh dễ trả lời sai hoặc làm lộ thông tin giữa phiên.',
'Bài MySQL/FAISS ở trên chỉ minh họa đọc hàng dữ liệu và truy xuất gần nhất. Để thành semantic answer cache còn phải có câu trả lời tương ứng, ngưỡng chấp nhận, kiểm tra hiệu lực, cơ chế ghi khi miss và ca thử phủ định. Không thể coi top-1 gần nhất là cache hit hợp lệ cho mọi câu hỏi.'])],
10:[('10.4. Phân tích lời gọi công cụ của ứng dụng',[
'Cả hai tool đều có tên và lược đồ arguments. Mô hình không trực tiếp thực thi Python; nó tạo yêu cầu có cấu trúc. ToolNode tìm tool tương ứng, kiểm tra arguments theo giao diện và tạo ToolMessage. Assistant nhận kết quả rồi quyết định trả lời hay yêu cầu bước khác. Đây là điểm khác biệt giữa phát biểu “tôi sẽ tra cứu” trong văn bản và một tool_call thật.',
'RAGTOOL nhận query để chạy retrieve/answer. SearchWebTool cũng nhận query nhưng gọi Tavily và cắt phần mô tả mỗi nguồn. Hai tool trả về chuỗi, vì vậy assistant phải đọc và tổng hợp từ văn bản kết quả; code chưa dùng một schema thống nhất gồm status, sources và answer để client kiểm tra tự động.',
'Khi công cụ trả câu thông báo lỗi thay vì exception, ToolNode vẫn có thể hoàn tất bước và đưa message đó về assistant. Model cần diễn đạt giới hạn cho người dùng. HTTP của run không nhất thiết là lỗi chỉ vì Tavily không hoạt động, nên không dùng HTTP 200 như bằng chứng mọi tool đều thành công.',
'Recursion limit giới hạn bước đồ thị nhằm tránh vòng lặp kéo dài. Giá trị 16 do frontend đặt không bảo đảm số lần gọi tool tối đa đúng bằng 16 vì assistant và tools là các bước khác nhau. Nó cũng không đặt trần thời gian tổng thể: mỗi lời gọi model có timeout và có thể retry theo cấu hình riêng.']),
('10.5. Thiết kế kiểm tra khả năng chọn tool',[
'Tập kiểm tra lựa chọn nên có lời chào, câu hỏi thật sự thuộc PDF, câu hỏi chỉ cần web, câu hỏi có thể trả lời trực tiếp và câu hỏi nhập nhằng. Với từng ca, ghi rõ công cụ kỳ vọng và liệu có nhiều lựa chọn chấp nhận được. Không nên chỉ dùng những câu chứa nguyên tên tool vì sẽ làm bài kiểm tra dễ hơn tình huống thực tế.',
'Sau khi chạy model thật, lưu toàn bộ thứ tự message gồm AIMessage tool_calls, ToolMessage và phản hồi cuối. Chấm riêng việc chọn công cụ, chất lượng arguments query, chất lượng dữ liệu tool và chất lượng câu trả lời. Cách này giúp xác định lỗi nằm ở model định tuyến hay ở retriever, thay vì gộp mọi lỗi vào “LangGraph trả lời sai”.'])],
11:[('11.4. Ví dụ HTTP để đọc đúng hợp đồng API',[
'Một thread là nơi giữ hội thoại; một run là lần thực thi graph trên thread. Tạo thread không gọi model trả lời. Gửi run với assistant_id chatbot mới thực thi graph đã đăng ký. Kết quả runs/wait là state sau run, không phải chuỗi JSON chỉ có trường response như API /chatbot trước đây.',
'Frontend gửi messages chứa tin người dùng mới. Runtime tải checkpoint cũ và gộp tin mới vào state. Nếu client gửi toàn bộ lịch sử đã có mà không hiểu ID/reducer, có thể phát sinh trùng lặp. Để khôi phục trang, dùng endpoint state thay vì tự giữ một bản lịch sử khác trong browser.',
'Cách gọi HTTP cũng phải tôn trọng bất đồng bộ của giao diện. setBusy chặn bấm Gửi nhiều lần trong cùng tab, còn multitask_strategy reject yêu cầu server không nhận run trùng khi thread đang bận. Đây chưa phải giới hạn tốc độ theo tài khoản hoặc cơ chế chống lạm dụng cho triển khai công khai.',
'Các lỗi HTTP từ Agent Server phụ thuộc hợp đồng native của phiên bản đang cài. main.py không ánh xạ riêng quota→429 hoặc provider timeout→504 như báo cáo phiên bản cũ. Khi viết hướng dẫn client phải dựa vào response thật của Agent Server và kiểm tra __error__ mà frontend hiện đang xử lý.']),
('11.5. Giao diện, an toàn hiển thị và trạng thái chờ',[
'Mã addMessage tạo text node cho nội dung thay vì gán innerHTML. Cách này giữ ký tự đặc biệt ở dạng văn bản và hạn chế việc đầu ra model biến thành mã HTML. Các chuỗi http/https được tạo thẻ liên kết với noopener noreferrer; điều đó giúp cách ly cửa sổ mở mới nhưng không chứng minh nội dung đích đáng tin cậy.',
'Trong khi đợi run, frontend hiển thị dấu chờ và khóa các thao tác đang có thể gây tranh chấp. Sau khi nhận state, renderHistory dựng lại danh sách. Khi lỗi, frontend thử đọc state đã commit một lần; không tự gửi lại câu hỏi vì gửi lại có thể tạo run trùng hoặc nhân đôi message.',
'Giao diện hiện không cho người dùng chọn mode RAG/web hay cấu hình model. Quyết định công cụ thuộc assistant. Nếu thêm nút mode trong tương lai, cần thay schema/luồng rõ ràng và sửa lại mô tả. Đừng ghi rằng API đang nhận question, user_id, session_id chỉ vì các trường đó từng có ở một bản code khác.'])],
12:[('12.4. Yêu cầu chức năng và giới hạn nghiệp vụ',[
'Người dùng cần gửi lời chia sẻ bằng tiếng Việt, xem trạng thái xử lý, đọc phản hồi và bắt đầu cuộc trò chuyện mới. Ứng dụng nên tiếp tục được mạch hội thoại trong cùng thread và có thể cung cấp thông tin tham khảo từ PDF hoặc web khi model chọn công cụ. Đây là phạm vi demo; không bao gồm đăng ký tài khoản, hồ sơ sức khỏe hay lịch hẹn chuyên gia.',
'Yêu cầu phi chức năng gồm khởi chạy rõ ràng trên Windows, không đặt API key ở client, trả lỗi dễ hiểu và tách module đủ để kiểm thử. Một số yêu cầu quan trọng như bảo mật nhiều người dùng, lưu trữ theo quy định và hiệu năng đồng thời vẫn chưa được kiểm chứng. Báo cáo chỉ ghi chúng là yêu cầu cho bước triển khai tiếp theo.',
'Thông tin được ghi trong system prompt như “không chẩn đoán” hoặc “không bịa nguồn” là chính sách mong muốn ở cấp lời nhắc. Chưa có bằng chứng để gọi đó là bộ bảo đảm an toàn độc lập. Thiết kế cần thể hiện rõ nơi kiểm soát nằm ở prompt, nơi kiểm soát bằng code và nơi còn thiếu đánh giá.',
'Tài liệu Stress.pdf được xem là nguồn demo đầu vào. Việc có tên tài liệu/trang giúp truy vết nhưng không tự xác nhận tác giả, độ cập nhật hoặc tính phù hợp y khoa. Bộ câu hỏi kiểm thử nên hướng đến việc trả lời đúng theo nguồn và thể hiện giới hạn; không suy rộng thành hiệu quả điều trị.']),
('12.5. Kịch bản tuần tự từ nút Gửi đến phản hồi',[
'Bước thứ nhất, frontend kiểm tra nội dung rỗng và trạng thái busy. Nếu chưa có thread, initialize tạo thread. Bước thứ hai, frontend thêm bubble người dùng và dấu chờ rồi gửi runs/wait. Bước thứ ba, Agent Server khôi phục state và chạy assistant theo graph ID chatbot.',
'Bước thứ tư có hai trường hợp: assistant không tạo tool_calls thì đi END; hoặc ToolNode chạy một hay nhiều yêu cầu tool rồi quay lại assistant. Nếu rag_tool được gọi, bên trong nó tạo/đọc retriever và chạy đồ thị RAG riêng. Bước thứ năm, state hoàn tất quay về client; frontend kiểm tra message cuối là phản hồi AI có nội dung rồi dựng lại lịch sử.',
'Trong cùng kịch bản, lỗi có thể xảy ra trước khi có run, trong lúc model trả lời, trong tool hoặc khi client mất kết nối sau server đã commit. Vì vậy việc khôi phục state sau lỗi giúp tránh suy đoán sai rằng mọi yêu cầu thất bại đều chưa ghi gì. Cần lưu thread/run ID khi điều tra để ghép đúng sự kiện.']),
('12.6. Cấu trúc mở rộng và ranh giới phụ thuộc',[
'Các tham số model/tools có thể được truyền vào Agent để dùng model giả trong test. RAG có các hàm retrieve và answer riêng để có thể thay retriever hoặc model bằng mock. Đây là cấu trúc hỗ trợ kiểm tra không tốn API, đồng thời giúp tìm lỗi dữ liệu đầu vào từng bước.',
'Việc thêm công cụ mới nên bắt đầu từ lược đồ đầu vào, mô tả và kiểm thử độc lập, sau đó mới đăng ký vào Agent. Nếu tool có tác dụng ghi/xóa dữ liệu ngoài hệ thống, cần thêm quyền và cơ chế xác nhận phù hợp; bản hiện tại chỉ có công cụ đọc/truy xuất. Không nên gắn trực tiếp một tool thực thi tùy ý vào chatbot chỉ để minh họa agent mạnh hơn.'])],
13:[('13.5. Phương pháp đánh giá đầy đủ cho phiên bản hiện tại',[
'Kết quả năm unit test là dữ liệu thực có thể tái hiện; các benchmark phiên bản cũ được thay bằng phương pháp đánh giá và bảng cần thu thập mới. Cách trình bày này giữ đầy đủ nội dung học thuật về đo lường nhưng tránh gán một bộ số liệu cho mã nguồn không tạo ra nó.',
'Với hội thoại trực tiếp, chuẩn bị câu hỏi theo nhóm: chào hỏi, chia sẻ cảm xúc, hỏi tiếp nối và yêu cầu ngoài phạm vi. Mỗi ca cần ghi đầu vào, đầu ra, thread ID, model, thời gian, tool_calls và nhận xét theo tiêu chí cố định. Hoàn tất HTTP chỉ là điều kiện kỹ thuật, chưa phải điểm chất lượng.',
'Với RAG, chuẩn bị trước câu hỏi, trang/đoạn tham chiếu và các ý bắt buộc. Cần có cả câu có đáp án lẫn câu ngoài tài liệu. Ghi context lấy về và câu trả lời cuối. Nếu câu trả lời thiếu ý, xác định bằng chứng có trong context hay không để phân biệt lỗi retrieval với lỗi generation.',
'Với web, lưu query gửi Tavily, URL, nội dung rút gọn trả cho model và thời điểm truy xuất. Chấm xem câu trả lời có dựa đúng nguồn, nguồn có phù hợp câu hỏi và URL có truy cập được hay không. Không lấy việc tool trả ba kết quả làm điểm đúng cho cả câu trả lời.',
'Với memory, dùng các thread có chuỗi lượt đã định trước và đáp án kỳ vọng. Kiểm tra thông tin được nhắc lại, thông tin được sửa và thread mới không thừa hưởng dữ kiện riêng. Ca dùng InMemorySaver trong unit test chỉ kiểm tra luồng dữ liệu cục bộ; cần ca HTTP qua Agent Server nếu muốn kết luận về toàn ứng dụng.',
'Với lỗi, tách lỗi giả lập có chủ đích khỏi lỗi tự phát trong baseline. Ví dụ mock retriever ném exception giúp xác nhận thông báo không chứa dữ liệu bí mật; nó không cho biết tần suất lỗi Groq trên mạng thật. Không trộn số lần lỗi chủ động vào error rate vận hành rồi công bố như độ tin cậy dịch vụ.']),
('13.6. Đo thời gian, token và thống kê',[
'Latency end-to-end được tính từ khi client gửi yêu cầu tới khi nhận đủ kết quả. Latency node hoặc model được đo riêng nếu có instrumentation. Hai loại số đo trả lời hai câu hỏi khác nhau; không so sánh trực tiếp thời gian graph.invoke cục bộ với HTTP runs/wait mà không nêu khác biệt.',
'p50 là phân vị trung vị, p95 mô tả vùng đuôi theo phương pháp tính đã chọn. Với mẫu quá nhỏ, p95 dễ trùng hoặc gần giá trị lớn nhất. Cần ghi số mẫu, cách tính, số lần warm-up, trạng thái tải embedding và liệu retry có xảy ra. Một bảng trung bình không đủ cho kết luận trải nghiệm ổn định.',
'Token nên lấy từ metadata thật của từng lời gọi model. Nếu một run gồm nhiều lần gọi assistant và RAG answer thì cần cộng có chủ đích theo run, tránh bỏ sót hoặc đếm lặp. Khi không có metadata, ghi thiếu dữ liệu; không điền 0. Chi phí tiền còn phụ thuộc giá của model theo thời điểm, vì vậy không tự quy đổi khi chưa kiểm tra bảng giá và cấu hình sử dụng.',
'Nên lưu dữ liệu thô cùng phiên bản thư viện, hash tệp nguồn và cấu hình không chứa bí mật. Điều này cho phép lần sau xác định phép đo thuộc graph nào. Mã nguồn thay đổi có thể làm hành vi khác ngay cả khi model name không đổi; ảnh chụp log thiếu phiên bản không đủ cho tái lập.']),
('13.7. Rubric chấm nội dung và giới hạn suy luận',[
'Có thể chấm bốn tiêu chí: được nguồn hỗ trợ, đủ ý cho câu hỏi, phù hợp phạm vi và nguồn/trang đúng. Mỗi tiêu chí dùng mức 0–2 với mô tả cụ thể. Điểm tổng là thước đo của bộ câu hỏi và rubric đó, không phải tỷ lệ chính xác toàn ứng dụng hay chứng nhận chuyên môn.',
'Người chấm nên xem câu hỏi, đáp án tham chiếu, nguồn gốc và phản hồi nhưng tránh bị dẫn dắt bởi tên cấu hình đang so sánh. Nếu có nhiều người chấm, lưu điểm từng người và cách giải quyết bất đồng. Nếu có AI hỗ trợ chấm, phải ghi rõ vai trò và vẫn giữ phân biệt với đánh giá độc lập của con người.',
'Bộ câu hỏi được dùng để chỉnh prompt nhiều lần sẽ trở thành bộ hồi quy. Muốn đánh giá tổng quát cần giữ một nhóm câu chưa dùng trong chỉnh sửa. Mẫu lấy chỉ từ một PDF vẫn có phạm vi hạn chế; không suy ra khả năng trả lời mọi câu hỏi tâm lý hoặc thông tin mới trên web.']),
('13.8. Tiêu chí nghiệm thu bản bàn giao',[
'Bản bàn giao đạt bước kỹ thuật khi có thể cài theo hướng dẫn, khởi chạy Agent Server, mở frontend, tạo thread, thực thi các test hiện có và giải thích đúng đường đi assistant/tools. Các chức năng gọi dịch vụ thật cần nghiệm thu riêng bằng tài khoản hợp lệ; khóa không được đi kèm gói báo cáo.',
'Khi gặp lỗi, người nhận cần có tên lệnh đã chạy, phiên bản Python, nhật ký khởi động và thông báo đã loại bí mật. Chưa có phép đo mới thì ghi chưa đo. Một báo cáo đầy đủ có thể chứa kế hoạch, phương pháp và giới hạn rõ ràng mà không cần tạo ra các con số để lấp bảng.'])],
14:[('14.3. Bài học về tính nhất quán của tài liệu',[
'Mã nguồn, hình, tên endpoint và kết quả thử nghiệm phải mô tả cùng một phiên bản. Khi đổi router từ classify theo luật sang LLM tool calling, cần sửa cả pipeline, giải thích và phương pháp đánh giá. Khi đổi BM25 sang FAISS, phải sửa loader/index/embedding và không giữ nguyên số đo cũ như thể không có thay đổi.',
'Một bản báo cáo dài không nên chỉ là tập hợp ảnh. Ảnh cần có vai trò: minh họa cấu trúc, giải thích code hay chứng minh một lần chạy. Bản này giữ các ví dụ nền tảng với chú thích đúng phạm vi và thêm đối chiếu code hiện tại sau mỗi chương, để người đọc hiểu kiến thức đã dẫn tới thiết kế sản phẩm như thế nào.'])],
15:[('15.3. Thứ tự triển khai cải tiến',[
'Trước hết khóa môi trường và bổ sung ca HTTP native để bảo đảm mọi lần cài mới chạy cùng hợp đồng API. Tiếp theo xây bộ dữ liệu đánh giá retrieval/generation rồi mới tối ưu chunking, model hoặc prompt. Chỉ nên đưa ra lựa chọn tối ưu khi có phép so sánh trên cùng điều kiện.',
'Sau khi có chất lượng cơ bản được đo, bổ sung xác thực, phân quyền thread, xóa dữ liệu và persistence phù hợp môi trường đích. Cuối cùng mới đo tải, tối ưu lịch sử và cân nhắc cache đáp án. Thứ tự này giúp tránh tối ưu tốc độ trên một hệ thống chưa xác định rõ quyền truy cập hoặc tiêu chí đúng.',
'Multi-agent, human-in-the-loop và streaming có thể mở rộng trải nghiệm nhưng không phải mục tiêu tự thân. Mỗi tính năng nên gắn với một yêu cầu cụ thể và một ca kiểm tra chứng minh ích lợi. Nếu luồng hiện tại đã đáp ứng câu hỏi một cách rõ ràng, không cần tăng số agent chỉ để làm kiến trúc phức tạp hơn.'])],
}

def added_sections(n):
    out=[]
    for title,paragraphs in ADDITIONS.get(n,[]):
        out.append(heading(title,2))
        out.extend(para(x) for x in paragraphs)
    return out

def api_chapter():
    out=[heading('Chương 11: Tích hợp API và triển khai',1)]
    out+=current_section(11)
    out.append(heading('11. Ví dụ giao tiếp HTTP từng bước',2))
    out.append(para('Đoạn Python dưới đây dùng urllib có sẵn để minh họa tạo thread và đọc state. Hai thao tác này không chạy model. Thực hiện sau khi server đã sẵn sàng tại cổng 2024. Đây là mã thực hành client, không thêm endpoint mới vào main.py.'))
    out+=codeblock('''import json
from urllib.request import Request, urlopen

base = "http://127.0.0.1:2024"
req = Request(base + "/threads", data=b"{}",
              headers={"Content-Type": "application/json"}, method="POST")
with urlopen(req, timeout=10) as response:
    thread = json.load(response)
thread_id = thread["thread_id"]
print("Thread:", thread_id)
with urlopen(base + f"/threads/{thread_id}/state", timeout=10) as response:
    state = json.load(response)
print(state)
''')
    out.append(para('Để chạy một câu hỏi với model thật, body gửi tới /threads/{thread_id}/runs/wait có dạng sau. Lệnh này có gọi nhà cung cấp nên chỉ thực hiện khi đã có cấu hình và quota; không coi ví dụ body là log đã chạy.'))
    out+=codeblock('''{
  "assistant_id": "chatbot",
  "input": {"messages": [{"type": "human", "content": "Xin chào"}]},
  "config": {"recursion_limit": 16},
  "multitask_strategy": "reject"
}''')
    out.append(heading('11. Đối chiếu các cách triển khai API',2))
    out.append(table(['Cách triển khai','Vai trò','Trong ứng dụng hiện tại'],[
        ('LangServe add_routes','Bọc Runnable qua HTTP và playground.','Tham khảo; không được dùng để phục vụ graph hiện tại.'),
        ('FastAPI endpoint tự viết','Tự thiết kế schema và hợp đồng lỗi cho lời gọi graph.','main.py chỉ phục vụ frontend, không có /chatbot hoặc /ask_document.'),
        ('LangGraph Agent Server','Quản lý graph, thread, run và persistence.','Luồng đang chạy qua langgraph dev và cấu hình langgraph.json.')]))
    out.append(para('Ví dụ /ask_document và /chat/playground của bản cũ được thay bằng các thao tác native tương ứng. Nội dung học về HTTP, request/response và tách frontend–backend vẫn được giữ, đồng thời tên đường dẫn và payload được cập nhật đúng với code đang có.'))
    out+=added_sections(11)
    return out


def application_chapter(n):
    titles={12:'Chương 12: Mô tả và phân tích thiết kế đồ án',13:'Chương 13: Triển khai, kiểm thử và phương pháp đánh giá'}
    out=[heading(titles[n],1)]
    out+=current_section(n)
    if n==12:
        out+=picture(HERE/'assets/architecture.png','Kiến trúc triển khai hiện tại: frontend → Agent Server → graph; main.py phục vụ giao diện.')
        out+=picture(HERE/'assets/conversation.png','Pipeline agent hiện tại; không có các node classify/grounded/refuse của phiên bản cũ.')
        out+=picture(HERE/'assets/rag.png','Pipeline rag_tool hiện tại: retrieve → answer, dùng FAISS/Hugging Face và ChatGroq.')
    if n==13:
        out.append(heading('13. Bảng ghi kết quả thực nghiệm cần thu thập',2))
        out.append(table(['Nhóm kiểm tra','Tình trạng bằng chứng hiện có','Không được suy ra'],[
            ('Logic graph','5 unit test; mô hình và retriever giả.','Độ chính xác Groq, RAG hoặc Tavily trên dữ liệu thật.'),
            ('Giao diện','Ảnh frontend, test trang/tài nguyên tĩnh.','Model nhớ đúng hoặc tool chọn đúng.'),
            ('Hiệu năng','Chưa có benchmark mới cho phiên bản này.','p50/p95 hoặc tiết kiệm cache theo số đo cũ.'),
            ('Nội dung','Chưa có phiếu chấm độc lập cho bản hiện tại.','Điểm 7,38/8 của một phiên bản khác.'),
            ('An toàn','Có chỉ dẫn trong prompt và test không lộ exception bí mật.','An toàn lâm sàng hoặc phát hiện khủng hoảng đã kiểm chứng.')]))
    out+=added_sections(n)
    return out


# Ghép lại toàn bộ nội dung theo các khoảng gốc; không rút gọn lý thuyết và bài tập.
final=[]
chapter_ranges=[(1,83,151),(2,151,215),(3,215,236),(4,236,578),(5,578,666),(6,666,680),(7,680,775),(8,775,811),(9,811,841),(10,841,901)]

def append_original(start,end):
    for i in range(start,end):
        if i in replaced:final.extend(replaced[i]);continue
        e=original[i]
        if e.tag!=qn('w:sectPr'):final.append(e)
        if i==645:
            final.append(para('Bảng trên là kết quả ghi lại của ví dụ semantic search ban đầu, không phải benchmark trên Stress.pdf của bản chatbot hiện tại. Score là khoảng cách theo index, không phải xác suất trả lời đúng.'))

append_original(0,29)
final.append(heading('MỤC LỤC',1))
p=doc.add_paragraph();field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'TOC \\o "1-2" \\h \\z \\u')
r=OxmlElement('w:r');t=OxmlElement('w:t');t.text='Mục lục sẽ được cập nhật theo các đề mục.';r.append(t);field.append(r);p._p.append(field);final.append(p._p)
append_original(31,83)
final.insert(len(final),para('Cách đọc báo cáo: các ví dụ PromptTemplate, chain, memory buffer và MySQL được giữ để trình bày nền tảng và quá trình học tập. Sau từng chương có phần đối chiếu code hiện tại. Các ảnh ví dụ riêng không được dùng làm bằng chứng tính năng của chatbot; ảnh cấu hình/luồng sai đã được thay. Phần triển khai và kết quả chỉ mô tả phiên bản đang có trong thư mục dự án.'))
for n,start,end in chapter_ranges:
    append_original(start,end)
    final+=current_section(n)
    final+=added_sections(n)
    if n==4:
        final.append(heading('4. Ví dụ chuyển tác vụ tuần tự sang StateGraph',2))
        final.append(para('Ví dụ dưới đây chỉ minh họa dữ liệu và thứ tự node bằng hàm Python theo luật; chưa gọi model tóm tắt/dịch. Khi thay bằng LLM, giữ nguyên hợp đồng cập nhật State để so sánh hai cách tổ chức.'))
        final+=codeblock('''from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    text: str
    summary: str
    translation: str

def summarize(state: State):
    return {"summary": state["text"][:80]}

def translate(state: State):
    return {"translation": "Ví dụ dữ liệu: " + state["summary"]}

builder = StateGraph(State)
builder.add_node("summarize", summarize)
builder.add_node("translate", translate)
builder.add_edge(START, "summarize")
builder.add_edge("summarize", "translate")
builder.add_edge("translate", END)
graph = builder.compile()
print(graph.invoke({"text": "Artificial intelligence..."}))
''')
    if n==8:
        final+=picture(source_card('memory_test','tests/test_chatbot.py',43,57),'Code test hiện tại về lịch sử cùng thread và tách thread; dùng FakeModel và InMemorySaver.')
    if n==9:
        final.append(table(['Đối tượng được tái sử dụng','Khóa/vòng đời','Điều chưa có'],[
            ('_retriever','Đối tượng RAGTOOL trong tiến trình.','Không theo dõi tự động PDF thay đổi, không TTL đáp án.'),
            ('_graph','Đối tượng RAGTOOL trong tiến trình.','Không cache kết quả answer theo query.'),
            ('Tệp embedding','HF_HOME/HF_HUB_CACHE.','Không phải lịch sử hội thoại.'),
            ('Checkpoint','Thread do runtime quản lý.','Không thay cơ chế cache câu trả lời.')]))

final+=api_chapter()
final.append(heading('Phần 3: Phân tích thiết kế và ứng dụng thực tế',1))
final+=application_chapter(12)
final+=application_chapter(13)
append_original(1059,1089);final+=current_section(14);final+=added_sections(14)
append_original(1089,1115);final+=current_section(15);final+=added_sections(15)
append_original(1115,1133)
final.append(para('Tài liệu đối chiếu bổ sung (truy cập 05/11/2026): Graph API — https://docs.langchain.com/oss/python/langgraph/graph-api; Persistence — https://docs.langchain.com/oss/python/langgraph/persistence; Local development — https://docs.langchain.com/langsmith/local-dev-testing. Các trang này hỗ trợ khái niệm nền tảng; thông số và tính năng sản phẩm được lấy từ source chương trình.'))
append_original(1133,1283)

final.append(heading('Phụ lục B: Hướng dẫn đọc mã nguồn chương trình',1))
final.append(para('Phụ lục này trình bày các đoạn mã đang có và giải thích vai trò ở mức tệp. Đây là phần bổ sung để nối nội dung giáo trình với ứng dụng thực tế; không sao chép .env hoặc bất kỳ giá trị khóa nào. Số dòng tương ứng với mã nguồn tại lần đối chiếu.'))
SOURCE_EXCERPTS=[
    ('B.1. System prompt và mô hình','agent.py',29,65,'System prompt đặt vai trò và hướng dẫn công cụ. Constructor cho phép truyền model/tools để kiểm thử. Mô hình mặc định dùng Groq; bind_tools khai báo khả năng gọi hai tool.'),
    ('B.2. Đồ thị hội thoại','agent.py',67,86,'Node assistant gọi model bất đồng bộ, đọc messages và trả reply mới. Cạnh tools→assistant là vòng lặp quan sát kết quả; tools_condition dẫn tới END khi không có tool_calls.'),
    ('B.3. Lược đồ và tài nguyên RAG','Rag_tool.py',27,63,'RAGInput định nghĩa query; RAGState có query/context/answer. Các PrivateAttr giữ PDF, retriever, graph và Lock trong đối tượng tool, không phải các trường người dùng gửi qua API.'),
    ('B.4. Dựng retriever','Rag_tool.py',64,86,'Các import nặng được thực hiện khi cần dùng. Double check dưới Lock hạn chế việc cùng đối tượng dựng lại index. Chunk 500/50 và top-k mặc định 2 là cấu hình thực.'),
    ('B.5. Ghép nguồn vào context','Rag_tool.py',87,95,'Metadata page từ loader được cộng 1 trước khi hiển thị. Context là chuỗi gắn nhãn nguồn; mã không tạo danh sách citation có lược đồ để validator kiểm tra.'),
    ('B.6. Node sinh câu trả lời RAG','Rag_tool.py',96,124,'Node answer không tự truy xuất thêm khi thiếu ngữ cảnh. Nó dùng cùng biến GROQ_MODEL nhưng prompt khác assistant. Exception được xử lý ở lớp _run của tool.'),
    ('B.7. Graph RAG và kết quả tool','Rag_tool.py',125,146,'Đồ thị được compile một lần trên đối tượng, invoke nhận query và trả answer cho ToolNode. Graph này không tự chuyển qua search_web nếu lỗi.'),
    ('B.8. Tavily và định dạng kết quả','searchweb_tool.py',31,86,'Công cụ kiểm tra khóa khi tạo Tavily tool, hỗ trợ hai tích hợp theo gói cài. Mỗi kết quả lấy title, nội dung rút gọn và URL; chưa có bước xác minh nguồn độc lập.'),
    ('B.9. Đăng ký graph','graph.py',1,4,'Agent Server đọc graph.py:graph qua cấu hình chatbot. Không truyền checkpointer riêng trong graph triển khai; runtime cấp persistence theo thread.'),
    ('B.10. Phục vụ giao diện','main.py',1,22,'App tùy chỉnh chỉ có trang gốc và static. Việc main.py dùng FastAPI không có nghĩa nó định nghĩa các endpoint threads/runs.'),
]
for title,filename,start,end,explain in SOURCE_EXCERPTS:
    final.append(heading(title,2));final.append(para(explain))
    lines=(ROOT/filename).read_text(encoding='utf-8').splitlines()
    # Chia ảnh quá dài để không tạo ảnh cao vượt một trang.
    for pos in range(start,min(end,len(lines))+1,23):
        stop=min(pos+22,end,len(lines))
        final+=picture(source_card(f'src_{filename.replace(".","_")}_{pos}',filename,pos,stop),f'Trích nguyên văn {filename}, dòng {pos}–{stop}.')

final.append(heading('Phụ lục C: Bảng đối chiếu nội dung và phạm vi bằng chứng',1))
final.append(table(['Nội dung','Cách xử lý trong bản đầy đủ'],[
    ('Lời mở đầu, tổng quan, nghề nghiệp, cài đặt','Giữ cấu trúc gốc; sửa mục tiêu và hướng dẫn theo dự án.'),
    ('LLM, prompt, chain, tool, embedding, chunking','Giữ lý thuyết và bài tập; phân biệt API LangChain với LangGraph.'),
    ('RAG và memory','Giữ phần nền tảng; bổ sung graph thật, thread và checkpoint.'),
    ('Cache/MySQL','Giữ lý thuyết tham khảo; bỏ khẳng định ứng dụng đã có TTL cache.'),
    ('Agents, API, thiết kế','Cập nhật LLM tool calling, Agent Server và native threads/runs.'),
    ('Đánh giá và kết quả','Giữ phương pháp đo/chấm; thay số liệu không có bằng chứng bằng phạm vi kiểm chứng thật.'),
    ('Hands-on lab','Giữ toàn bộ quy trình State/node/edge/memory/log; sửa đường dẫn và phiên bản ví dụ.'),
    ('Hình minh họa','Giữ hình nền tảng đúng phạm vi; thay sơ đồ sai, ảnh cấu hình và ảnh app cũ; thêm code thật.')]))
final.append(para('Năm test được báo cáo là năm bài trong tests/test_chatbot.py và đã được ghi ở test_results.txt từ lần kiểm tra bản source hiện tại. Không có công cụ tính toán add/multiply trong graph chatbot; phần số học là bài thực hành độc lập. Không có benchmark provider thật mới được thực hiện trong quá trình biên tập báo cáo này.'))


# Lắp body sau khi mọi block đã được dựng, giữ section properties cuối gốc.
body=doc._element.body
section=copy.deepcopy(body.sectPr)
for e in list(body):body.remove(e)
for e in final:body.append(e)
body.append(section)

# Chuẩn hóa cấp đề mục và loại ngắt trang thừa, không thay chữ bên trong ảnh giữ lại.
position_map={id(e):i for i,e in enumerate(original)}
part_pending=False
for e in body:
    if e.tag!=qn('w:p'):continue
    text=get_text(e).strip()
    original_index=position_map.get(id(e))
    is_part=text.startswith('Phần ') and (original_index in [33,81,1059] or original_index is None)
    is_top=bool(re.match(r'^(Chương\s+\d+|Phụ lục [ABC])',text)) or is_part
    if is_top:
        pr=e.get_or_add_pPr();st=pr.find(qn('w:pStyle'))
        if st is None:st=OxmlElement('w:pStyle');pr.insert(0,st)
        st.set(qn('w:val'),doc.styles['Heading 1'].style_id)
        # Không giữ numPr/break do định dạng cũ khi đã có tên chương bằng chữ.
        for node in list(pr):
            if node.tag in [qn('w:numPr')]:pr.remove(node)
        if text.startswith('Chương') and part_pending:
            node=OxmlElement('w:pageBreakBefore');node.set(qn('w:val'),'false');pr.append(node)
            part_pending=False
        if is_part:part_pending=True
    elif original_index in [65,66,69,71,77,80]:
        pr=e.get_or_add_pPr();st=pr.find(qn('w:pStyle'))
        if st is None:st=OxmlElement('w:pStyle');pr.insert(0,st)
        st.set(qn('w:val'),normal.style_id)
        for node in list(pr):
            if node.tag==qn('w:pageBreakBefore'):pr.remove(node)
    # Các chương gốc có đề mục con đánh số, đưa chúng vào mục lục cấp 2 khi đủ rõ.
    elif text and len(text)<130 and (re.match(r'^\d+\.\d+(?:\.\d+)?\s',text) or text in ['1. Hệ sinh thái LangGraph','2. Hệ sinh thái LangSmith.','3. LLM/ Chat Model','4. Prompt Template','5. Graph và thành phần Chain dùng trong node','6. Tool & Tools','7. Giao diện cho chatbot.']):
        pr=e.get_or_add_pPr();st=pr.find(qn('w:pStyle'))
        if st is None:st=OxmlElement('w:pStyle');pr.insert(0,st)
        st.set(qn('w:val'),doc.styles['Heading 2'].style_id)
    elif original_index is not None:
        pr=e.find(qn('w:pPr'))
        st=pr.find(qn('w:pStyle')) if pr is not None else None
        if st is not None and st.get(qn('w:val'))==doc.styles['Heading 1'].style_id:
            st.set(qn('w:val'),doc.styles['Heading 2'].style_id)
            for node in list(pr):
                if node.tag==qn('w:pageBreakBefore'):pr.remove(node)

# Bỏ các dòng trống cuối bìa và mục lục cũ; bìa vẫn giữ hình, trường, giảng viên và thành viên.
for e in original[18:29]:
    if e.getparent() is body:body.remove(e)

# Đánh số và chú thích tất cả hình; ghi đúng phạm vi cho các ví dụ cũ giữ lại.
captions={
255:'Hệ sinh thái LangSmith: công cụ quan sát và đánh giá tham khảo; không phải bằng chứng đồ án đã chạy evaluator.',
262:'Ví dụ cấu hình tracing đọc khóa từ môi trường/getpass; chưa có trace dịch vụ được báo cáo từ ví dụ này.',
279:'So sánh giao diện text và message; bảng kiến thức nền tảng, không phân loại model theo khả năng tự nhớ.',
283:'Kiểu dữ liệu chuỗi cho lời gọi text trong ví dụ học tập.',
285:'Ví dụ ghép hướng dẫn và yêu cầu vào một prompt dạng chuỗi.',
289:'Danh sách BaseMessage và AIMessage trong giao diện chat model.',
291:'Vai trò System/Human/AI trong một ví dụ hội thoại.',
296:'Đồ thị ví dụ kiểm tra câu hỏi rỗng; khác đồ thị assistant/tools của ứng dụng cuối.',
303:'Cài gói cho bài thực hành StateGraph và ChatGroq độc lập.',
307:'Đọc khóa qua môi trường/getpass trong bài thực hành; model name thuộc ví dụ này.',
309:'Khai báo State và node của ví dụ kiểm tra câu hỏi rỗng.',
310:'Biên dịch và gọi graph của bài thực hành StateGraph độc lập.',
317:'Ví dụ ChatOpenAI được gọi trong một node; đây không phải model mặc định của chatbot.',
318:'Các cạnh và lời gọi MessagesState trong ví dụ ChatOpenAI độc lập.',
343:'Hai lời gọi model không truyền lịch sử: bài học stateless, chưa qua graph triển khai.',
346:'Đầu ra ghi lại của ví dụ không truyền lịch sử; không phải benchmark phiên bản hiện tại.',
350:'Truyền danh sách message để tiếp nối ngữ cảnh trong ví dụ độc lập.',
357:'Đầu ra ghi lại khi có lịch sử; chỉ minh họa ví dụ học tập.',
378:'Prompt template kết hợp dữ liệu để tạo đầu vào model; template không phải node điều phối.',
382:'PromptTemplate từ langchain_core.prompts: định dạng chuỗi topic.',
391:'ChatPromptTemplate: định dạng danh sách message theo vai trò.',
403:'MessagesPlaceholder: chèn danh sách message trong ví dụ prompt.',
421:'System template trong bài học chatbot theo cảm xúc, không thay SYSTEM_PROMPT của agent.py.',
423:'Human template với biến cảm xúc/chủ đề trong bài học riêng.',
449:'Kết quả định dạng prompt, không phải phản hồi LLM.',
462:'Luồng chain tuyến tính của bài học; StateGraph được đối chiếu ở phần bổ sung.',
466:'LLMChain đời cũ của LangChain, giữ để so sánh; không phải API LangGraph hay code chạy hiện tại.',
491:'SequentialChain đời cũ của LangChain; ví dụ tham khảo có thể cần môi trường riêng.',
523:'Chuẩn bị model và khóa cho bài thực hành graph theo chủ đề.',
528:'Hàm khởi tạo ChatGroq trong bài học riêng.',
530:'Tạo message từ cảm xúc/chủ đề của ví dụ, khác schema chatbot triển khai.',
534:'ChatState và node answer/clarify của ví dụ theo chủ đề.',
535:'Khai báo cạnh và input của ví dụ theo chủ đề.',
537:'Sơ đồ của bài thực hành theo chủ đề; không phải router của ứng dụng cuối.',
544:'Đầu ra kiểm tra nhánh thiếu chủ đề của bài học; không gọi model.',
565:'Ví dụ khái niệm agent sử dụng nhiều công cụ; calculator không có trong chatbot hiện tại.',
568:'Tool tính biểu thức bằng AST trong bài học độc lập; không dùng eval.',
572:'initialize_agent/AgentExecutor đời cũ của LangChain; giữ đối chiếu, không phải graph của sản phẩm.',
586:'Ví dụ embedding với OpenAIEmbeddings; ứng dụng thực tế dùng HuggingFaceEmbeddings.',
603:'Tạo FAISS index và docstore trong bài thực hành vector store riêng.',
625:'Danh sách câu tiếng Việt phục vụ thực hành semantic search.',
627:'Model đa ngôn ngữ và cấu hình chuẩn hóa của bài học; khác EMBEDDING_MODEL mặc định của sản phẩm.',
633:'Tạo FAISS từ các câu trong bài học semantic search.',
639:'Truy vấn top-3 của bài học semantic search; RAG hiện tại mặc định top-2.',
677:'Ví dụ splitter 100/0 để học chia đoạn; Rag_tool.py dùng 500/50.',
693:'Ví dụ chuẩn bị PDF/FAISS dùng OpenAIEmbeddings; đối chiếu Hugging Face ở phần triển khai.',
708:'Sơ đồ RAG khái niệm; query classification và reranking là lựa chọn mở rộng, chưa có trong code hiện tại.',
717:'Ví dụ retrieve/generate trước khi ghép cạnh StateGraph; các biến phụ thuộc cần được khai báo.',
746:'Chia PDF thành đoạn 500 ký tự, chồng 50 ký tự trong bài thực hành.',
753:'Embedding Hugging Face và tạo chỉ mục FAISS trong bài thực hành PDF.',
766:'Đồ thị RAG minh họa với node generate; code thật của tool đặt tên node answer.',
772:'Gọi đồ thị RAG minh họa; không phải log phản hồi model thật.',
786:'Lệnh môi trường của ví dụ memory LangChain đời cũ; không thay hướng dẫn cài chatbot.',
788:'ConversationChain/ConversationBufferWindowMemory đời cũ, giữ để so sánh khái niệm.',
793:'Dữ liệu hội thoại và prompt của bài học memory độc lập.',
797:'Vòng thử k=1/2/3 của bài học memory LangChain cũ.',
803:'Buffer ghi lại của ví dụ k=1; không chứng minh model của chatbot nhớ đúng.',
804:'Buffer ghi lại của ví dụ k=2; không phải checkpoint của ứng dụng hiện tại.',
805:'Buffer ghi lại của ví dụ k=3; chỉ minh họa dữ liệu trong cửa sổ lịch sử.',
834:'Ví dụ đọc MySQL rồi tạo FAISS, chưa phải semantic answer cache và chưa tích hợp vào chatbot.',
838:'Hàm similarity_search của bài học MySQL/FAISS; top-k không tự xác nhận cache hit.',
876:'Cài thư viện cho bài thực hành agent toán riêng.',
878:'Cấu hình ChatGroq của bài thực hành tool calling độc lập.',
881:'add/multiply là công cụ của bài tập, không có trong danh sách tool của chatbot.',
883:'Vòng StateGraph assistant/tools của ví dụ toán; chưa là kết quả model thật chọn tool.',
}
original_positions={id(e):i for i,e in enumerate(original)}
figure_index=0
for e in list(body):
    if e.tag!=qn('w:p') or not e.findall('.//a:blip',NS):continue
    i=original_positions.get(id(e))
    if i==5:continue
    figure_index+=1
    if i is not None:
        caption=captions.get(i,'Ví dụ kiến thức nền tảng được giữ từ báo cáo gốc; đối chiếu code hiện tại ở cuối chương.')
        c=para(f'Hình {figure_index}. {caption}')
        e.addnext(c)
        from docx.text.paragraph import Paragraph
        cp=Paragraph(c,doc._body);cp.alignment=WD_ALIGN_PARAGRAPH.CENTER
        for r in cp.runs:r.italic=True;r.font.size=Pt(10)
    else:
        nxt=e.getnext()
        if nxt is not None and nxt.tag==qn('w:p'):
            texts=nxt.findall('.//w:t',NS)
            if texts:
                texts[0].text=re.sub(r'^Hình \d+\.\s*','',texts[0].text or '')
                texts[0].text=f'Hình {figure_index}. '+texts[0].text

# Xóa quan hệ ảnh không còn sử dụng, bao gồm ảnh cũ có cấu hình khóa.
used={value for e in body.iter() for key,value in e.attrib.items() if key.startswith('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}')}
for rid,rel in list(doc.part.rels.items()):
    if rel.reltype.endswith('/image') and rid not in used:doc.part.drop_rel(rid)
field=OxmlElement('w:updateFields');field.set(qn('w:val'),'true');doc.settings.element.append(field)
doc.core_properties.title='Tìm hiểu và ứng dụng công nghệ LangGraph — Báo cáo đầy đủ nhóm 15'
doc.core_properties.author='Nhóm 15'
doc.core_properties.subject='Giữ nội dung nền tảng bản cũ, sửa kỹ thuật và đối chiếu mã nguồn hiện tại'
from professional_bullets import apply_bullet_style
apply_bullet_style(doc.part.numbering_part.element)
doc.save(OUT)

alltext='\n'.join(p.text for p in doc.paragraphs)
words=sum(len(p.text.split()) for p in doc.paragraphs)
origwords=original_word_count
manifest={
    'source':str(SOURCE),'output':str(OUT),'original_paragraph_words':origwords,
    'full_paragraph_words':words,'paragraphs':len(doc.paragraphs),'inline_images':len(doc.inline_shapes),'tables':len(doc.tables),
    'rewritten_original_paragraph_indices':sorted(REWRITES),
    'replaced_image_paragraph_indices':sorted(replaced),
    'retained_original_ranges':[[0,29],[31,901],[1059,1283]],
    'source_hashes':{x:hashlib.sha256((ROOT/x).read_bytes()).hexdigest() for x in ['agent.py','Rag_tool.py','searchweb_tool.py','main.py','graph.py','frontend/app.js','langgraph.json','tests/test_chatbot.py']},
}
(HERE/'full_revision_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(OUT)
print(json.dumps({k:manifest[k] for k in ['original_paragraph_words','full_paragraph_words','paragraphs','inline_images','tables']},ensure_ascii=False))
