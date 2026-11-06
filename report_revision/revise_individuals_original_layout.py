"""Edit each original in place structurally, retaining its cover, styles and body."""
from pathlib import Path
from copy import deepcopy
import hashlib
import json
import re
import sys
import zipfile

from docx import Document
from docx.shared import Cm, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph

from individual_figures import ASSETS, create

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(r'C:\Users\Admin\Downloads\Các báo cáo cần nôp')
OUT = ROOT / 'Bao_cao_ca_nhan_LangGraph_Giu_mau_goc'
OUT.mkdir(exist_ok=True)


def set_text(para, value):
    """Retain paragraph properties and all run formatting, including cover styles."""
    ts=para._p.xpath('.//w:t')
    if not ts:
        para.add_run(value)
        return
    # Main prose run carries the original body typeface; avoid a prefix-only run.
    chosen=max(ts,key=lambda x: len(x.text or ''))
    for node in ts:
        node.text=value if node is chosen else ''
        node.set('{http://www.w3.org/XML/1998/namespace}space','preserve')


def common(text):
    new=re.sub(r'LangChain|Langchain|LANGCHAIN',lambda m:'LANGGRAPH' if m[0].isupper() else 'LangGraph',text)
    if any(s in text for s in ['– một framework mã nguồn mở phổ biến','– Một framework mã nguồn mở phổ biến','LangChain ra đời']):
        new='\t- LangGraph là framework điều phối ứng dụng AI theo đồ thị có trạng thái, thuộc hệ sinh thái LangChain. Trong đồ án, LangGraph quản lý luồng hội thoại, nhánh gọi công cụ và cập nhật state; các gói LangChain cung cấp giao diện mô hình, tin nhắn, công cụ và truy xuất dữ liệu. Cách kết hợp này giúp xây dựng chatbot có luồng xử lý rõ ràng mà không cần huấn luyện lại mô hình.'
    elif 'Harrison Chase' in text:
        new='\t- LangGraph thuộc hệ sinh thái LangChain và tập trung vào điều phối các workflow, Agent có trạng thái. Thay vì chỉ nối các bước xử lý tuyến tính, người phát triển khai báo state, node và edge, cho phép mô hình gọi công cụ, nhận kết quả và tiếp tục tạo câu trả lời. Báo cáo tìm hiểu công nghệ này thông qua ứng dụng chatbot hỗ trợ trò chuyện về tâm lý.'
    elif 'là một framework mã nguồn mở' in text and 'LangChain' in text:
        new='\t- LangGraph tổ chức ứng dụng bằng StateGraph: State lưu dữ liệu dùng chung, node thực hiện tác vụ và edge xác định bước tiếp theo. Chương trình sử dụng MessagesState để giữ danh sách tin nhắn, node assistant để gọi ChatGroq và ToolNode để thực thi rag_tool hoặc search_web. Các tích hợp mô hình và dữ liệu vẫn sử dụng thư viện trong hệ sinh thái LangChain.'
    elif any(s in text for s in ['không đánh số phiên bản','không sử dụng hệ thống phiên bản','không sử dụng hệ thống đánh số phiên bản']):
        new='\t- LangGraph và các gói tích hợp có phiên bản phát hành cụ thể, vì vậy cần kiểm tra tính tương thích khi cài đặt. Dự án sử dụng requirements.txt; trong đó langgraph-cli[inmem] được ghim ở phiên bản 0.4.33. Môi trường chạy theo README.md yêu cầu Python 3.11 trở lên và nên sử dụng .venv để tránh xung đột với dự án khác.'
    elif 'GitHub' in text and ('stars' in text or '90k' in text):
        new='+ Mã nguồn mở: có thể đối chiếu mã nguồn LangGraph tại kho langchain-ai/langgraph để tìm hiểu cách xây dựng đồ thị và các ví dụ thực hành.'
    elif 'Discord/Slack' in text:
        new='+ Trao đổi kỹ thuật: tham khảo các thảo luận và báo lỗi của dự án, đồng thời kiểm tra phiên bản thư viện trước khi áp dụng lời giải vào chương trình.'
    elif 'nhiều công ty' in text.lower() or 'nhiều tập đoàn' in text.lower():
        new='Kỹ năng thiết kế workflow AI có trạng thái, tích hợp RAG và API là nền tảng để em phát triển theo hướng AI Developer, LLM Engineer hoặc Backend Developer. Việc học LangGraph trong đồ án giúp em kết nối kiến thức mô hình ngôn ngữ với kỹ năng xây dựng và kiểm tra một ứng dụng cụ thể.'
    elif 'Prompt Engineer:' in text:
        new='+ Prompt Engineer: thiết kế lời nhắc hệ thống, quy định cách dùng công cụ, sử dụng dữ liệu tham khảo và giới hạn đầu ra. Các mẫu prompt có thể dùng ChatPromptTemplate của LangChain; trong Agent hiện tại, SYSTEM_PROMPT được ghép với lịch sử messages trước khi gọi mô hình.'
    elif 'AI Engineer / Machine Learning Engineer:' in text:
        new='+ AI Engineer / Machine Learning Engineer: tích hợp mô hình ngôn ngữ và công cụ vào ứng dụng; thiết kế workflow, quản lý trạng thái và kiểm tra hành vi. Đồ án thực hành gọi mô hình qua dịch vụ, không tự huấn luyện mô hình mới.'
    elif any(s in text for s in ['Lỗi cài đặt thư viện LangChain','Thách thức về Môi trường Phát triển']):
        new='\t- Môi trường và thư viện: các gói như langgraph, langchain-core, langchain-community và langchain-groq cần được cài trong cùng môi trường ảo. Em khắc phục bằng cách chọn đúng interpreter .venv trong IDE, cài theo requirements.txt và kiểm tra import trước khi chạy ứng dụng.'
    elif ('model miễn phí' in text.lower() or 'model miễn phí ' in text.lower()) and ('khó' in text.lower() or 'ít tham số' in text):
        new='\t- Lựa chọn và cấu hình mô hình: chất lượng phản hồi phụ thuộc mô hình, prompt và dữ liệu đầu vào. Chương trình dùng ChatGroq với GROQ_API_KEY; model đọc từ GROQ_MODEL, mặc định openai/gpt-oss-20b. Em khắc phục lỗi bằng cách kiểm tra tên model, quyền truy cập, hạn mức và kết nối; không mặc định dịch vụ luôn miễn phí hoặc luôn sẵn sàng.'
    elif ('FastAPI' in text and ('Chatbot' in text or 'chatbot' in text or 'frontend' in text)):
        new='\t- Chatbot tích hợp giao diện HTML/CSS/JavaScript với LangGraph Agent Server. FastAPI trong main.py phục vụ trang và tài nguyên tĩnh qua http.app; frontend sử dụng trực tiếp API threads/runs của Agent Server để gửi tin và khôi phục lịch sử.'
    elif 'Đã vận dụng thành công nhiều thành phần' in text or 'đã vận dụng thành công nhiều thành phần' in text:
        new='\t- Các thành phần đã áp dụng gồm StateGraph, MessagesState, node, cạnh điều kiện, ToolNode, checkpoint theo thread và đồ thị RAG. Phần truy xuất dùng PyPDFLoader, chia đoạn, HuggingFaceEmbeddings và FAISS; phần mô hình và tìm kiếm dùng Groq cùng Tavily.'
    elif ('Áp dụng LangGraph' in text and ('multi-agent' in text.lower() or 'đa tác tử' in text.lower())):
        new='\t+ Mở rộng đồ thị LangGraph hiện có thành nhiều Agent chuyên biệt nếu bài toán cần, đồng thời bổ sung cơ chế phối hợp và đánh giá riêng. Phiên bản hiện tại có một Agent hội thoại và hai công cụ.'
    elif 'Nâng cao kiến thức về LLM và LangChain' in text:
        new='\t+ Tiếp tục nghiên cứu LLM và LangGraph: quản lý lịch sử dài, tóm tắt ngữ cảnh, streaming và tối ưu số lần gọi mô hình; giữ các tích hợp LangChain phù hợp với phiên bản dự án.'
    elif 'đảm bảo câu trả lời' in text and ('chính xác' in text or 'minh bạch' in text):
        new='\t- RAG bổ sung các đoạn dữ liệu liên quan vào câu hỏi để mô hình có căn cứ tham khảo. Công cụ hiện tại tra cứu Stress.pdf và yêu cầu dẫn tên tài liệu cùng số trang. Kết quả vẫn cần được kiểm chứng; RAG không tự bảo đảm câu trả lời luôn chính xác hoặc thông tin luôn mới.'
    elif 'tư vấn tâm lý' in text:
        new=new.replace('tư vấn tâm lý','hỗ trợ trò chuyện về tâm lý, không thay thế chuyên gia')
    return new


REWRITES={
'3122410469': {
    66:'\t- Em tìm hiểu LangGraph và các thành phần tích hợp, kết hợp lý thuyết với thực hành các nội dung:',
    67:'\t\t+ StateGraph, State, node và edge trong LangGraph.',
    68:'\t\t+ LangSmith: tìm hiểu tracing và đánh giá; là hướng tiếp tục hoàn thiện.',
    69:'\t\t+ ChatModel qua ChatGroq, cấu hình GROQ_API_KEY và GROQ_MODEL.',
    70:'\t\t+ SYSTEM_PROMPT và tin nhắn SystemMessage trong node assistant.',
    71:'\t\t+ Cạnh điều kiện tools_condition và vòng lặp assistant → tools → assistant.',
    72:'\t\t+ BaseTool, tool schema và ToolNode.',
    73:'\t\t+ HuggingFaceEmbeddings và FAISS.',
    74:'\t\t+ Chunking và đồ thị RAG retrieve → answer.',
    75:'\t\t+ MessagesState, checkpoint và lịch sử theo thread.',
    76:'\t\t+ Khởi tạo retriever khi cần, giữ lại trong đối tượng công cụ để tái sử dụng.',
    77:'\t\t+ Agent chatbot điều phối hai công cụ rag_tool và search_web.',
    78:'\t\t+ LangGraph Agent Server, API threads/runs và giao diện web.',
    79:'\t- Em tìm hiểu cách LangGraph tổ chức luồng START → assistant; khi có tool_calls thì chuyển sang ToolNode, nhận ToolMessage rồi quay về assistant. Khi không cần công cụ, luồng đi tới END. Mô hình quyết định việc yêu cầu công cụ; tools_condition kiểm tra tool_calls trong phản hồi.',
    80:'\t- Từ các kiến thức trên, em đề xuất kiến trúc chatbot có giao diện web, máy chủ quản lý hội thoại và đồ thị điều phối mô hình cùng các công cụ như các sơ đồ dưới đây:',
    83:'\t- Trong đồ án, em thực hiện phần Agent và kết nối API với giao diện. agent.py xây StateGraph(MessagesState); graph.py xuất graph và langgraph.json đăng ký assistant_id là chatbot. API hội thoại do Agent Server cung cấp, không còn triển khai endpoint /chatbot riêng bằng LangServe.',
    85:'\t\t+ Chatbot có thể trả lời trực tiếp, gọi rag_tool cho Stress.pdf hoặc search_web cho thông tin bên ngoài. Công cụ trả kết quả về assistant để mô hình tạo phản hồi cuối; không phải câu hỏi nào cũng bắt buộc tra cứu.',
    86:'\t\t+ Giao diện gửi một tin nhắn mới qua POST /threads/{id}/runs/wait. Runtime nạp và lưu lịch sử theo thread; frontend chỉ giữ thread_id trong sessionStorage. Chất lượng phản hồi còn phụ thuộc mô hình, nội dung truy xuất và dịch vụ.',
    87:'\t\t+ Agent và API giúp kết nối backend với giao diện web như hình dưới. main.py phục vụ giao diện; frontend tạo hội thoại bằng POST /threads và đọc lại lịch sử bằng GET /threads/{id}/state. Tạo thread mới không xóa thread cũ.',
    111:'\t- Hệ thống đã áp dụng StateGraph, MessagesState, node assistant, ToolNode, cạnh điều kiện và checkpoint theo thread. Các tích hợp gồm Groq, RAG trên Stress.pdf bằng Hugging Face/FAISS và tìm kiếm Tavily.',
},
'3122410269': {
    82:'\t- Em phụ trách tìm hiểu và triển khai SearchWebTool trong searchweb_tool.py. Công cụ tên search_web nhận query, dùng TAVILY_API_KEY để tìm kiếm qua Tavily và trả tối đa 3 kết quả gồm tiêu đề, đoạn mô tả và URL. Công cụ này được gắn vào mô hình trong Agent như đồ thị phía trên.',
    83:'Ví dụ: khi người dùng cần thông tin mới về phim truyền cảm hứng, mô hình có thể gọi search_web. ToolNode thực thi công cụ, sau đó chuyển kết quả trở lại assistant. Việc chọn công cụ phụ thuộc tool_calls của mô hình; nếu thiếu khóa hoặc gặp lỗi, công cụ trả thông báo chưa thể tìm kiếm. Hình dưới minh họa giao diện của chương trình hiện tại.',
    86:'\t- Em còn nghiên cứu cơ chế Memory: btap1.py và notebook minh họa việc truyền lịch sử thủ công; trong chatbot hiện tại, MessagesState và checkpoint của Agent Server quản lý ngữ cảnh theo thread. Frontend chỉ lưu mã thread trong sessionStorage; đọc lịch sử từ máy chủ khi tải lại cùng tab. Sơ đồ dưới mô tả cơ chế này.',
    87:'\t- Bài tập Agent tính cộng và nhân bằng @tool giúp em hiểu schema và cách mô hình yêu cầu công cụ. Đây là nội dung thực hành nền tảng; chatbot hiện tại chỉ đăng ký rag_tool và search_web, không tích hợp các công cụ tính toán của bài tập.',
    93:'\t- Về bộ nhớ, ban đầu em dễ nhầm ChatModel tự lưu thông tin giữa các lần gọi. Em khắc phục bằng cách so sánh lời gọi độc lập với lời gọi có truyền danh sách tin nhắn, sau đó đối chiếu MessagesState và thread_id. Lịch sử chỉ được tái sử dụng khi ứng dụng cung cấp đúng ngữ cảnh của hội thoại.',
},
'3122410129': {
    41:'+ (1) State lưu dữ liệu dùng chung, trong chatbot là danh sách messages.\n+ (2) Node thực hiện tác vụ: assistant gọi mô hình, tools thực thi công cụ.\n+ (3) Edge và cạnh điều kiện quyết định bước tiếp theo, cho phép lặp lại việc gọi công cụ hoặc kết thúc lượt chạy. Checkpoint theo thread giúp duy trì ngữ cảnh giữa các lượt.',
    61:'\t- Trong đề tài LangGraph, em tập trung nghiên cứu Agent, công cụ và truy xuất tài liệu, kết hợp tìm hiểu các tích hợp mô hình và dữ liệu trong hệ sinh thái LangChain. Những nội dung chính gồm:',
    62:'+ Kiến trúc Agent: tìm hiểu StateGraph(MessagesState), node assistant và ToolNode, cùng nhánh tools_condition. Luồng công cụ quay lại assistant để xử lý kết quả trước khi kết thúc; đây là một Agent với hai công cụ, chưa phải hệ thống multi-agent.',
    63:'+ Giám sát bằng LangSmith: tìm hiểu tracing và đánh giá nhằm định hướng kiểm tra ứng dụng. Việc nghiên cứu này không đồng nghĩa bản demo đã có bộ đánh giá chất lượng tự động hoàn chỉnh.',
    64:'+ Kết nối mô hình: đối chiếu ChatGroq trong agent.py, sử dụng GROQ_API_KEY và model theo GROQ_MODEL, mặc định openai/gpt-oss-20b. OpenAI và Gemini là các lựa chọn tham khảo, không phải tích hợp đang chạy trong luồng chatbot.',
    65:'+ Thiết kế lời nhắc: tìm hiểu SYSTEM_PROMPT được ghép với lịch sử hội thoại; quy định sử dụng công cụ, trả lời tiếng Việt và không tự nhận là bác sĩ hoặc chẩn đoán.',
    66:'+ Công cụ: tìm hiểu cách rag_tool và search_web nhận query theo schema, được bind_tools vào mô hình và thực thi bởi ToolNode.',
    68:'\t- Sau phần nền tảng, em nghiên cứu và đề xuất kiến trúc RAG cho tài liệu Stress.pdf, tổ chức phần xử lý bên trong công cụ bằng đồ thị LangGraph.',
    69:'\t- RAG giúp bổ sung dữ liệu riêng vào câu hỏi trước khi gọi mô hình. Trong chương trình, công cụ rag_tool lấy các đoạn liên quan từ Stress.pdf rồi tạo câu trả lời có hướng dẫn dẫn nguồn và trang. Cơ chế này hỗ trợ kiểm chứng thông tin, nhưng không bảo đảm mọi câu trả lời đều chính xác.',
    70:'\t- Kiến trúc gồm phần chuẩn bị dữ liệu và phần đồ thị xử lý câu hỏi, được minh họa như sau:',
    72:'\t- Hai giai đoạn chính là chuẩn bị dữ liệu (đọc PDF, chia đoạn, embedding, FAISS) và xử lý truy vấn bằng đồ thị START → retrieve → answer → END.',
    73:'\t\t- (1) Chuẩn bị dữ liệu: retriever được khởi tạo khi công cụ được sử dụng lần đầu và giữ lại trong đối tượng để dùng cho các truy vấn tiếp theo.',
    74:'+ Đọc và chia nhỏ: PyPDFLoader tải Stress.pdf; RecursiveCharacterTextSplitter chia đoạn 500 ký tự, chồng lấn 50 ký tự, giữ metadata trang.',
    75:'+ Embedding: HuggingFaceEmbeddings đọc EMBEDDING_MODEL; mặc định là VoVanPhuc/sup-SimCSE-VietNamese-phobert-base. Các đoạn được chuyển thành vector để hỗ trợ tìm kiếm tương đồng.',
    76:'+ Lập chỉ mục: FAISS.from_documents tạo vector store, truy xuất k = 2 theo mặc định. Phiên bản hiện tại không dùng Chroma và chưa ghi chỉ mục FAISS ra tệp để nạp lại sau khi khởi động.',
    77:'\t\t- (2) Xử lý truy vấn: RAGState gồm query, context, answer. Node retrieve lấy dữ liệu; node answer dùng ngữ cảnh để tạo câu trả lời.',
    78:'+ Truy xuất: node retrieve nhận query, gọi retriever và ghép nội dung hai đoạn tìm được với nhãn Stress.pdf, trang tương ứng; metadata page được cộng 1 để hiển thị số trang.',
    79:'+ Bổ sung ngữ cảnh: câu hỏi và context được đưa vào ChatGroq. SystemMessage yêu cầu chỉ dựa vào tài liệu, dẫn nguồn/trang và thừa nhận thiếu thông tin khi cần.',
    80:'+ Tạo câu trả lời: node answer trả answer; _run của rag_tool gọi đồ thị đã biên dịch và trả kết quả cho Agent. Context rỗng hoặc lỗi công cụ có thông báo tương ứng. Luồng hiện tại không dùng RetrievalQA; sơ đồ Agent và giao diện dưới đây thể hiện cách tích hợp RAG vào chương trình.',
    100:'\t- Chatbot hiện tại dùng LangGraph điều phối assistant và công cụ; MessagesState cùng checkpoint duy trì lịch sử theo thread. RAG trên Stress.pdf sử dụng PyPDFLoader, chia đoạn, Hugging Face và FAISS; search_web dùng Tavily. Các phản hồi vẫn cần được đánh giá về nội dung và trích dẫn.',
},
'3122410459': {
    83:'\t- Em thực hiện và hướng dẫn cài đặt môi trường LangGraph bằng .venv, sử dụng đúng interpreter và cài thư viện theo requirements.txt. Dự án cần Python 3.11 trở lên, GROQ_API_KEY và TAVILY_API_KEY nếu dùng tìm kiếm web. Các bước cài đặt, khởi động được minh họa dưới đây.',
    85:'\t- Em so sánh lời gọi không truyền lịch sử và lời gọi có truyền lịch sử trong btap1.py. Cả hai đều dùng ChatGroq; sự khác biệt nằm ở danh sách tin nhắn đầu vào, không phải hai loại mô hình tự có hoặc không có bộ nhớ. Chatbot hiện tại dùng MessagesState và checkpoint theo thread để lưu ngữ cảnh.',
    86:'\t- Em thực hành Prompt Template và khởi tạo mô hình qua chain.py: ChatPromptTemplate → ChatGroq → StrOutputParser, dùng llama-3.1-8b-instant. Sơ đồ dưới là ví dụ nền tảng này, được giữ để đối chiếu. Trong ứng dụng chính, agent.py dùng SYSTEM_PROMPT + messages và model theo GROQ_MODEL, mặc định openai/gpt-oss-20b, theo đồ thị LangGraph bổ sung phía dưới.',
},
}


def after(anchor, text='', caption=False):
    el=OxmlElement('w:p')
    anchor._p.addnext(el)
    para=Paragraph(el,anchor._parent)
    if not caption:
        if anchor._p.pPr is not None:
            para._p.insert(0,deepcopy(anchor._p.pPr))
        para.paragraph_format.page_break_before=False
        para.paragraph_format.keep_with_next=False
    run=para.add_run(text)
    run.font.name='Times New Roman'
    run.font.size=Pt(11 if caption else 13)
    if caption:
        run.italic=True
        para.alignment=WD_ALIGN_PARAGRAPH.CENTER
        para.paragraph_format.space_before=Pt(3)
        para.paragraph_format.space_after=Pt(8)
        para.paragraph_format.keep_together=True
    return para


def picture(para,path,width):
    for el in list(para._p):
        if el.tag!=qn('w:pPr'):
            para._p.remove(el)
    para.alignment=WD_ALIGN_PARAGRAPH.CENTER
    para.paragraph_format.keep_with_next=True
    para.paragraph_format.keep_together=True
    shape=para.add_run().add_picture(str(path),width=Cm(width))
    shape._inline.docPr.set('descr',path.stem)


def process(source):
    original_hash=hashlib.sha256(source.read_bytes()).hexdigest()
    doc=Document(source)
    paras=list(doc.paragraphs)
    sid=source.stem.split('_')[1]
    original_cover=paras[0]._p.xml
    original_logo=paras[6]._p.xml
    original_section=doc.sections[0]._sectPr.xml
    changed=[]
    for i,para in enumerate(paras):
        if not para.text:
            continue
        new=REWRITES[sid].get(i,common(para.text))
        if new!=para.text:
            changed.append(i)
            set_text(para,new)
        if para.style.name.startswith('Heading') and para.text.strip() and not re.match(r'^(?:[1-5]\.|Giới thiệu|LỜI CẢM ƠN)',para.text.strip()):
            # Several originals mark a career bullet as a heading accidentally.
            para.style=doc.styles['Normal']
    ui=ASSETS/'web_current.png'
    if not ui.exists():
        ui=ROOT/'report_revision'/'assets'/'ui.png'
    figures=[]
    def replace(index,name,caption,width=14):
        picture(paras[index],ASSETS/name if name!='UI' else ui,width)
        figures.append((index,caption))
        after(paras[index],f'Hình {len(figures)}. {caption}',True)
    def insert(anchor,name,caption,width=14):
        para=after(anchor)
        picture(para,ASSETS/name if name!='UI' else ui,width)
        figures.append(('added',caption))
        return after(para,f'Hình {len(figures)}. {caption}',True)
    if sid=='3122410469':
        replace(81,'architecture_grid.png','Pipeline chatbot hiện tại với LangGraph Agent Server.',14.5)
        replace(82,'agent_grid.png','Đồ thị assistant, ToolNode và các nhánh điều kiện trong agent.py.',12.8)
        insert(paras[87],'UI','Giao diện web chatbot của chương trình hiện tại.',14.5)
    elif sid=='3122410269':
        replace(81,'agent_grid.png','Đồ thị Agent gọi rag_tool hoặc search_web qua ToolNode.',12.8)
        replace(85,'UI','Giao diện web chatbot của chương trình hiện tại.',14.5)
        insert(paras[86],'memory_grid.png','Quản lý bộ nhớ hội thoại theo thread của LangGraph.',14.5)
    elif sid=='3122410129':
        replace(71,'rag_grid.png','Chuẩn bị dữ liệu và đồ thị RAG cho Stress.pdf.',12.2)
        tail=insert(paras[80],'agent_grid.png','Đồ thị Agent tích hợp công cụ RAG và tìm kiếm web.',12.8)
        insert(tail,'UI','Giao diện web chatbot của chương trình hiện tại.',14.5)
    else:
        replace(82,'UI','Giao diện web chatbot của chương trình hiện tại.',14.5)
        replace(84,'install_current.png','Các bước cài đặt và chạy dự án LangGraph trên Windows.',14.5)
        # Retain the original, still-valid chain.py diagram as a foundation exercise.
        figures.append((87,'Sơ đồ bài tập chain.py: Prompt Template, ChatGroq và Output Parser.'))
        tail=after(paras[87],f'Hình {len(figures)}. {figures[-1][1]}',True)
        insert(tail,'agent_grid.png','Đồ thị LangGraph của chatbot chính để đối chiếu với bài tập Chain.',12.8)
    # Original trailing empty paragraphs must not generate an empty final page.
    for para in reversed(doc.paragraphs):
        if para.text.strip() or para._p.xpath('.//w:drawing'):
            break
        para._p.getparent().remove(para._p)
    assert paras[0]._p.xml==original_cover
    assert paras[6]._p.xml==original_logo
    assert doc.sections[0]._sectPr.xml==original_section
    assert all(x._p.getparent() is not None for x in paras if x.text.strip() or x._p.xpath('.//w:drawing'))
    output=OUT/(source.stem+'_LangGraph_Giu_mau_goc.docx')
    doc.save(output)
    check=Document(output)
    assert len(check.tables)==len(Document(source).tables)
    assert 'LANGGRAPH' in check.paragraphs[9].text
    assert check.paragraphs[14].text==paras[14].text
    assert hashlib.sha256(source.read_bytes()).hexdigest()==original_hash
    with zipfile.ZipFile(output) as z:
        assert z.testzip() is None
    return {'source':str(source),'source_sha256':original_hash,'output':str(output),
            'original_paragraphs':len(paras),'output_paragraphs':len(check.paragraphs),
            'rewritten_paragraphs':changed,'figures':figures,'inline_images':len(check.inline_shapes),
            'preserved_cover':True,'preserved_logo':True,'preserved_page_setup':True}


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    create()
    results=[process(f) for f in sorted(SOURCE.glob('BÁO CÁO CÁ NHÂN*.docx'))]
    (OUT/'kiem_tra_ban_giu_mau_goc.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    with zipfile.ZipFile(OUT/'4_bao_cao_LangGraph_giu_mau_goc.zip','w',zipfile.ZIP_DEFLATED) as z:
        for f in sorted(OUT.glob('*.docx')):
            z.write(f,f.name)
    for r in results:
        print(Path(r['output']).name, '| figures:',len(r['figures']),'| retained:',r['original_paragraphs'],'paragraphs')
