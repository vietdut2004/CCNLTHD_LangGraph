from __future__ import annotations

import copy
import hashlib
import json
import math
import re
import subprocess
import sys
import textwrap
from datetime import datetime
from importlib.metadata import version
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
ASSETS = HERE / 'assets'
SOURCE = next((ROOT.parent).glob('*15*LangGraph.docx'))
OUTPUT = ROOT / 'Bao_cao_nhom_15_LangGraph_da_chinh_sua.docx'
ASSETS.mkdir(exist_ok=True)
FONT = 'C:/Windows/Fonts/arial.ttf'
BOLD = 'C:/Windows/Fonts/arialbd.ttf'
MONO = 'C:/Windows/Fonts/consola.ttf'
INK = '#172b4d'
BLUE = '#2255a4'


def diagram(name, title, boxes, edges, note, size=(1600, 1050)):
    im = Image.new('RGB', size, 'white')
    draw = ImageDraw.Draw(im)
    draw.text((60, 35), title, font=ImageFont.truetype(BOLD, 40), fill=INK)
    for start, end, label, bends in edges:
        points = [start, *bends, end]
        draw.line(points, fill=BLUE, width=5)
        angle = math.atan2(end[1]-points[-2][1], end[0]-points[-2][0])
        arrow = [end, (end[0]-20*math.cos(angle-.45), end[1]-20*math.sin(angle-.45)),
                 (end[0]-20*math.cos(angle+.45), end[1]-20*math.sin(angle+.45))]
        draw.polygon(arrow, fill=BLUE)
        if label:
            a,b=points[max(0,len(points)//2-1):len(points)//2+1]
            x,y=(a[0]+b[0])/2,(a[1]+b[1])/2
            ft=ImageFont.truetype(FONT,25)
            bound=draw.textbbox((x,y),label,font=ft)
            draw.rectangle((bound[0]-8,bound[1]-5,bound[2]+8,bound[3]+5),fill='white')
            draw.text((x,y),label,font=ft,fill=INK)
    for rect, text in boxes:
        draw.rounded_rectangle(rect, radius=18, fill='#edf3fc', outline=BLUE, width=3)
        ft=ImageFont.truetype(FONT,29)
        lines=text.split('\n')
        top=(rect[1]+rect[3]-len(lines)*40)/2
        for j,line in enumerate(lines):
            w=draw.textlength(line,font=ft)
            draw.text(((rect[0]+rect[2]-w)/2,top+j*40),line,font=ft,fill=INK)
    ft=ImageFont.truetype(FONT,24)
    for j,line in enumerate(note.split('\n')):
        draw.text((60,size[1]-100+j*32),line,font=ft,fill='#4f6075')
    im.save(ASSETS / f'{name}.png')


def source_image(name, filename, start, end):
    lines=(ROOT/filename).read_text(encoding='utf-8').splitlines()
    selected=lines[start-1:end]
    ft=ImageFont.truetype(MONO,23)
    width=max(1200,int(max(ImageDraw.Draw(Image.new('RGB',(1,1))).textlength(s,font=ft) for s in selected))+180)
    im=Image.new('RGB',(width,110+34*len(selected)),'#f7f9fc')
    d=ImageDraw.Draw(im)
    d.text((35,22),f'{filename}  |  dòng {start}–{end}',font=ImageFont.truetype(BOLD,27),fill=BLUE)
    for i,s in enumerate(selected):
        d.text((20,85+i*34),str(start+i).rjust(3),font=ft,fill='#778398')
        d.text((100,85+i*34),s,font=ft,fill=INK)
    im.save(ASSETS/f'{name}.png')


def find_line(filename, text):
    return next(i for i,l in enumerate((ROOT/filename).read_text(encoding='utf-8').splitlines(),1) if text in l)


diagram('conversation','Đồ thị hội thoại — agent.py',[
    ((580,130,1000,230),'START'),
    ((520,340,1060,480),'assistant\nSystemMessage + messages → LLM'),
    ((120,650,650,800),'tools — ToolNode\nrag_tool hoặc search_web'),
    ((1050,650,1450,800),'END\nkết thúc lượt chạy'),
], [((790,230),(790,340),'',[]),((620,480),(380,650),'có tool_calls',[]),
    ((980,480),(1250,650),'không có tool_calls',[]),
    ((120,700),(520,410),'ToolMessage',[ (70,700),(70,410)])],
    'tools_condition chỉ kiểm tra tool_calls; mô hình quyết định có yêu cầu công cụ hay không.\nMỗi lượt chạy từ frontend đặt recursion_limit = 16; END không xóa thread.')

diagram('rag','RAG trong rag_tool — Rag_tool.py',[
    ((60,150,410,290),'Stress.pdf\nPyPDFLoader'),
    ((620,150,1030,290),'Chia đoạn\n500 ký tự / chồng 50'),
    ((1220,150,1550,290),'Embedding\nHugging Face'),
    ((1120,430,1550,580),'FAISS\ntruy xuất top-2'),
    ((560,430,970,580),'retrieve\ncontext kèm trang PDF'),
    ((60,430,410,580),'query\nSTART'),
    ((560,720,970,860),'answer\nChatGroq → answer'),
    ((1150,720,1500,860),'END'),
], [((410,220),(620,220),'',[]),((1030,220),(1220,220),'',[]),
    ((1380,290),(1380,430),'',[]),((1120,505),(970,505),'',[]),
    ((410,505),(560,505),'',[]),((765,580),(765,720),'context',[]),
    ((970,790),(1150,790),'',[])],
    'Đồ thị thực thi: START → retrieve → answer → END. Khởi tạo retriever khi dùng lần đầu.\nKhông có node grade, rewrite, validate; không tự chuyển sang web khi RAG lỗi.')

diagram('architecture','Kiến trúc ứng dụng hiện tại',[
    ((60,180,470,340),'frontend/\nHTML + CSS + JavaScript'),
    ((630,180,1100,340),'LangGraph Agent Server\n127.0.0.1:2024'),
    ((630,530,1100,690),'chatbot\ngraph.py → Agent'),
    ((50,530,440,690),'main.py:app\n/ và /static'),
    ((1210,500,1550,660),'ChatGroq\nGroq API'),
    ((180,780,650,910),'rag_tool\nStress.pdf + FAISS + Groq'),
    ((1040,780,1510,910),'search_web\nTavily API'),
], [((470,260),(630,260),'threads / runs',[]),((860,340),(860,530),'state + checkpoint',[]),
    ((630,570),(440,570),'http.app',[]),((1100,580),(1210,580),'',[]),
    ((730,690),(500,780),'tool_calls',[]),((1000,690),(1200,780),'tool_calls',[])],
    'main.py phục vụ tài nguyên giao diện; API threads/runs do Agent Server cung cấp.', size=(1600,1060))

diagram('memory','Bộ nhớ hội thoại và vòng đời thread',[
    ((70,180,510,340),'sessionStorage của tab\nchỉ lưu thread_id'),
    ((760,180,1500,340),'LangGraph Agent Server\nthread → checkpoint → messages'),
    ((70,550,510,730),'Mở lại cùng tab\nGET state của thread đã lưu'),
    ((760,550,1500,730),'Cuộc trò chuyện mới\nPOST /threads → ID mới'),
], [((510,250),(760,250),'GET /state',[]),((290,340),(290,550),'tải lại trang',[]),
    ((1120,550),(1120,340),'thread độc lập',[]),((510,650),(760,650),'chọn nút mới',[])],
    'Lịch sử nằm ở server; frontend không lưu nội dung tin nhắn trong sessionStorage.\nTạo thread mới không xóa thread cũ. Chưa có đăng nhập hay phân quyền người dùng.')

for name, filename, marker, count in [
    ('agent_code','agent.py','    def create_agent',21),
    ('rag_graph_code','Rag_tool.py','    def _build_graph',12),
    ('retriever_code','Rag_tool.py','                docs = PyPDFLoader',12),
    ('model_code','agent.py','            model = ChatGroq',6),
    ('frontend_code','frontend/app.js','    const result = await api',7),
    ('server_code','main.py','app = FastAPI',10),
    ('tavily_code','searchweb_tool.py','    def _create_tavily_tool',13),
]:
    start=find_line(filename,marker)
    source_image(name,filename,start,min(start+count-1,len((ROOT/filename).read_text(encoding='utf-8').splitlines())))

doc=Document(SOURCE)
body=doc._element.body
old=list(body)
# Giữ nguyên bìa gốc, tên trường, giảng viên, nhóm và các thành viên.
for element in old[18:]:
    if element.tag != qn('w:sectPr'):
        body.remove(element)
# Loại quan hệ ảnh cũ không còn được tham chiếu để không giữ ảnh bản khác trong gói Word.
used_ids={value for e in body.iter() for key,value in e.attrib.items()
          if key.startswith('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}')}
for rid,rel in list(doc.part.rels.items()):
    if rel.reltype.endswith('/image') and rid not in used_ids:
        doc.part.drop_rel(rid)
if 'Table Grid' not in doc.styles:
    sty=doc.styles.add_style('Table Grid',WD_STYLE_TYPE.TABLE)
    props=OxmlElement('w:tblPr'); borders=OxmlElement('w:tblBorders')
    for edge in ['top','left','bottom','right','insideH','insideV']:
        node=OxmlElement('w:'+edge)
        for key,val in [('val','single'),('sz','4'),('color','B6C2D4')]: node.set(qn('w:'+key),val)
        borders.append(node)
    props.append(borders); sty.element.append(props)
for sec in doc.sections:
    sec.page_width=Cm(21); sec.page_height=Cm(29.7)
    sec.top_margin=Cm(2); sec.bottom_margin=Cm(2)
    sec.left_margin=Cm(3); sec.right_margin=Cm(2)
    sec.header_distance=Cm(1); sec.footer_distance=Cm(1)
normal=doc.styles['Normal']
normal.font.name='Times New Roman'; normal.font.size=Pt(13)
normal.paragraph_format.line_spacing=1.1
normal.paragraph_format.space_after=Pt(6)
for sty,sz in [('Heading 1',17),('Heading 2',14),('Heading 3',13)]:
    doc.styles[sty].font.name='Times New Roman'
    doc.styles[sty].font.size=Pt(sz)
    doc.styles[sty].font.color.rgb=RGBColor.from_string('17365D')
    doc.styles[sty].paragraph_format.keep_with_next=True
    doc.styles[sty].paragraph_format.space_before=Pt(14)
    doc.styles[sty].paragraph_format.space_after=Pt(8)
doc.styles['Heading 1'].paragraph_format.page_break_before=True
for sec in doc.sections:
    # Thay số trang/đầu trang cũ có thể chứa tên phiên bản trước.
    for container in [sec.header,sec.footer]:
        for p in container.paragraphs:
            p.clear()
    p=sec.footer.paragraphs[0]; p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    fld=OxmlElement('w:fldSimple'); fld.set(qn('w:instr'),'PAGE'); p._p.append(fld)

figures=[]
previous_part=False
def h(text,level=1):
    global previous_part
    para=doc.add_heading(text,level=level)
    if previous_part and level==1:
        para.paragraph_format.page_break_before=False
    previous_part=text.startswith('Phần ')
def p(text):
    para=doc.add_paragraph(text)
    para.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
    return para
def code(text):
    for line in text.strip('\n').splitlines():
        para=doc.add_paragraph()
        para.paragraph_format.space_after=Pt(0)
        para.paragraph_format.line_spacing=1
        r=para.add_run(line or ' '); r.font.name='Consolas'; r.font.size=Pt(9)
def table(headers,rows):
    t=doc.add_table(rows=1,cols=len(headers)); t.style='Table Grid'
    for c,text in zip(t.rows[0].cells,headers): c.text=text
    for row in rows:
        for c,text in zip(t.add_row().cells,row): c.text=str(text)
    for row in t.rows:
        cant_split=OxmlElement('w:cantSplit'); row._tr.get_or_add_trPr().append(cant_split)
        for c in row.cells:
            for para in c.paragraphs:
                para.paragraph_format.space_after=Pt(4)
                for r in para.runs: r.font.size=Pt(11)
    for c in t.rows[0].cells:
        for r in c.paragraphs[0].runs: r.bold=True
    p('')
def fig(name,caption,source):
    path=ASSETS/f'{name}.png'
    if not path.exists(): raise FileNotFoundError(path)
    para=doc.add_paragraph(); para.alignment=WD_ALIGN_PARAGRAPH.CENTER
    para.paragraph_format.keep_with_next=True
    width=13 if name=='memory' else 15.5
    para.add_run().add_picture(str(path),width=Cm(width))
    para=doc.add_paragraph(f'Hình {len(figures)+1}. {caption}')
    para.alignment=WD_ALIGN_PARAGRAPH.CENTER
    for r in para.runs: r.italic=True; r.font.size=Pt(11)
    s=doc.add_paragraph('Nguồn: '+source)
    s.paragraph_format.space_after=Pt(10)
    for r in s.runs: r.font.size=Pt(10)
    figures.append((name,caption,source))

h('LỜI CẢM ƠN')
p('Chúng em xin chân thành cảm ơn Thầy Phạm Thi Vương đã hướng dẫn và truyền đạt kiến thức trong học phần Các công nghệ lập trình hiện đại. Những góp ý của Thầy giúp nhóm hoàn thiện cách nghiên cứu công nghệ, tổ chức mã nguồn và trình bày kết quả đồ án. Báo cáo trình bày việc tìm hiểu LangGraph và ứng dụng vào chatbot hỗ trợ tâm lý bằng tiếng Việt.')
h('MỤC LỤC')
toc=doc.add_paragraph()
field=OxmlElement('w:fldSimple'); field.set(qn('w:instr'),'TOC \\o "1-2" \\h \\z \\u')
run=OxmlElement('w:r'); text=OxmlElement('w:t'); text.text='Mục lục được cập nhật theo các đề mục của báo cáo.'; run.append(text); field.append(run); toc._p.append(field)

h('Phần 1. Lời mở đầu')
h('1. Lý do chọn đề tài',2)
p('Một chatbot có tích hợp công cụ cần thực hiện nhiều bước: nhận câu hỏi, đọc lịch sử, chọn cách xử lý, gọi công cụ khi cần và tổng hợp kết quả. Luồng này có thể rẽ nhánh và lặp lại. LangGraph cho phép nhóm biểu diễn các bước bằng đồ thị có trạng thái, qua đó làm rõ dữ liệu được truyền và điều kiện kết thúc của một lượt xử lý.')
p('Đề tài xây dựng chatbot hỗ trợ tâm lý bằng tiếng Việt với hai công cụ: tra cứu tài liệu Stress.pdf và tìm kiếm web. Nội dung hỗ trợ mang tính tham khảo. Ứng dụng không phải dịch vụ chẩn đoán, điều trị hoặc kê đơn và chưa có nghiên cứu đánh giá hiệu quả lâm sàng.')
h('2. Mục tiêu và phạm vi',2)
p('Mục tiêu là giải thích đúng StateGraph, MessagesState, node, edge, tool calling và checkpoint; đồng thời mô tả được mối liên hệ giữa lý thuyết với chương trình đang có. Phần triển khai tập trung vào Agent Server, API threads/runs, giao diện web và đồ thị RAG hai bước.')
p('Phạm vi nguồn dữ liệu cục bộ hiện tại là Stress.pdf; chương trình chưa có chức năng tải thêm PDF/DOCX từ giao diện. Nhóm sử dụng mô hình qua Groq, không huấn luyện LLM. Báo cáo lấy mã nguồn trong thư mục dự án làm căn cứ về tính năng; các notebook và script bài tập được tách khỏi luồng chạy của chatbot.')
h('3. Căn cứ đối chiếu',2)
p('Bản chỉnh sửa ngày 05/11/2026 được đối chiếu trực tiếp với agent.py, Rag_tool.py, searchweb_tool.py, graph.py, main.py, frontend/app.js, langgraph.json và bộ tests/test_chatbot.py. Hình sơ đồ được dựng lại từ những tệp này; ảnh mã nguồn giữ tên tệp và số dòng. Các số liệu benchmark, điểm chấm và định danh của phiên bản khác không được dùng làm kết quả của bản hiện tại.')

h('Phần 2. Cơ sở công nghệ và tổ chức chương trình')
h('Chương 1. Giới thiệu LangGraph')
h('1.1. Vai trò của LangGraph',2)
p('Trong đồ án, LangGraph chịu trách nhiệm điều phối luồng chạy có trạng thái. StateGraph khai báo kiểu trạng thái, các node và các cạnh. Sau khi compile, đồ thị nhận đầu vào bằng invoke/ainvoke. Một node có thể gọi mô hình, thực thi công cụ hoặc xử lý dữ liệu bằng Python. [1]')
p('Cần phân biệt thư viện điều phối với các tích hợp. ChatGroq thuộc langchain-groq; BaseTool và các kiểu message thuộc langchain-core; PyPDFLoader và FAISS đến từ langchain-community. Việc dùng chúng bên trong một node không biến các API đó thành API của LangGraph.')
h('1.2. Đồ thị thực tế trong đề tài',2)
p('Chương trình có đồ thị hội thoại dùng MessagesState và đồ thị RAG dùng RAGState. Đồ thị hội thoại có vòng lặp công cụ; đồ thị RAG là luồng tuyến tính retrieve rồi answer. RAG được bọc dưới dạng tool và được ToolNode gọi, không được đăng ký trực tiếp như một node con trong graph hội thoại.')
fig('architecture','Kiến trúc giao diện, Agent Server, đồ thị và dịch vụ bên ngoài.','Sơ đồ dựng từ langgraph.json, main.py, agent.py, Rag_tool.py và searchweb_tool.py.')

h('Chương 2. Năng lực ứng dụng và định hướng nghề nghiệp')
p('Thông qua đề tài, nhóm rèn luyện khả năng thiết kế luồng AI có trạng thái, xây dựng API, xử lý bất đồng bộ, truy xuất tài liệu và kiểm thử thành phần có phụ thuộc dịch vụ ngoài. Đây là các năng lực có thể sử dụng trong công việc phát triển ứng dụng AI và backend tích hợp mô hình ngôn ngữ.')
p('Một ứng dụng vận hành thực tế còn cần xác thực, phân quyền, quản lý dữ liệu hội thoại, đo chất lượng đầu ra và theo dõi lỗi. Bản chạy cục bộ hiện tại giúp minh họa công nghệ nhưng chưa đáp ứng toàn bộ yêu cầu vận hành của một hệ thống nhiều người dùng.')
p('Báo cáo không đưa ra con số về mức lương, nhu cầu tuyển dụng hay quy mô cộng đồng khi chưa có dữ liệu khảo sát riêng. Kết quả học tập được thể hiện bằng khả năng giải thích và kiểm chứng chương trình.')

h('Chương 3. Cài đặt và khởi chạy')
h('3.1. Môi trường',2)
p('README yêu cầu Python 3.11 trở lên. Cần có kết nối mạng để cài thư viện, gọi Groq/Tavily và tải mô hình embedding nếu máy chưa có cache. Các câu lệnh dưới đây chạy trong PowerShell tại thư mục chứa requirements.txt.')
code('python -m venv .venv\n.\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt')
p('Nếu chưa có .env, sao chép .env.example thành .env và điền GROQ_API_KEY. TAVILY_API_KEY chỉ cần cho tìm kiếm web. Không chép khóa thật vào báo cáo hoặc mã frontend. Nếu .env đã có thì chỉnh các giá trị cần thiết, tránh ghi đè cấu hình đang sử dụng.')
code('GROQ_API_KEY=<nhap-khoa-cuc-bo>\nGROQ_MODEL=openai/gpt-oss-20b\nTAVILY_API_KEY=<nhap-khoa-neu-dung-web>\nEMBEDDING_MODEL=VoVanPhuc/sup-SimCSE-VietNamese-phobert-base')
h('3.2. Khởi chạy đúng máy chủ',2)
code('.\\run_api.bat\n# Hoac:\n.\\.venv\\Scripts\\python.exe start_langgraph.py --no-browser')
p('run_api.bat là điểm khởi chạy tương thích, chuyển đến máy chủ LangGraph như run_langgraph.bat. start_langgraph.py chọn Python của .venv, chạy langgraph_cli dev và đợi kiểm tra /ok cùng trang giao diện. Địa chỉ mặc định là http://127.0.0.1:2024. Giữ terminal mở trong khi sử dụng; Ctrl+C để dừng.')
p('Không chạy uvicorn main:app để thay cho luồng trên: main.py chỉ khai báo giao diện, còn API threads/runs đến từ Agent Server. Tệp .cache/last_startup.log lưu nhật ký khởi chạy. Máy chủ dev được dùng cho phát triển cục bộ. [2]')
h('3.3. Phiên bản đối chiếu',2)
packages=['langgraph','langgraph-api','langgraph-cli','langchain-core','langchain-groq','faiss-cpu']
table(['Thành phần','Phiên bản cài tại lần kiểm tra'],[(x,version(x)) for x in packages])
p('requirements.txt chỉ cố định langgraph-cli[inmem]==0.4.33; phần lớn gói còn lại không khóa phiên bản. Bảng trên là môi trường đã kiểm tra, không phải cam kết mọi lần cài mới sẽ thu được cùng bộ phiên bản. Khi bàn giao nên lưu pip freeze và kiểm tra tương thích.')

h('Chương 4. State, node, edge và mô hình ngôn ngữ')
h('4.1. State và MessagesState',2)
p('State là dữ liệu dùng chung giữa các bước của đồ thị. Đồ thị hội thoại dùng MessagesState với trường messages. Cơ chế cập nhật message hỗ trợ gộp các tin nhắn mới vào lịch sử và cập nhật theo định danh message; node không cần trả lại toàn bộ lịch sử trong mỗi bước. [1]')
p('Node assistant nhận state và trả {"messages": [reply]}. Trước khi gọi mô hình, node ghép SystemMessage từ SYSTEM_PROMPT với các message đang có. SystemMessage được thêm vào lời gọi mô hình; hàm assistant không tự thêm nó vào state đầu ra.')
h('4.2. Node và cạnh',2)
table(['Thành phần','Vị trí trong chương trình','Vai trò'],[
    ('START','agent.py','Bắt đầu lượt chạy, đi đến assistant.'),
    ('assistant','Hàm async trong create_agent','Gọi mô hình với system prompt và lịch sử.'),
    ('tools','ToolNode(self._tools)','Thực thi tool_calls và tạo kết quả công cụ.'),
    ('Cạnh điều kiện','tools_condition','Có tool_calls thì đến tools, ngược lại đến END.'),
    ('Cạnh lặp','tools → assistant','Đưa ToolMessage trở lại mô hình.'),
    ('END','langgraph.graph.END','Kết thúc lượt chạy hiện tại.')])
fig('conversation','Đồ thị hội thoại với nhánh có và không gọi công cụ.','agent.py, hàm Agent.create_agent().')
h('4.3. Cấu hình mô hình và prompt',2)
p('Agent mặc định khởi tạo ChatGroq với GROQ_MODEL hoặc openai/gpt-oss-20b, temperature=0, timeout=60 và max_retries=1. bind_tools cung cấp mô tả và lược đồ công cụ cho mô hình. Mã không chứa router phân loại bằng từ khóa; mô hình tạo tool_calls dựa trên đầu vào và lịch sử.')
fig('model_code','Cấu hình ChatGroq trong Agent.','Trích nguyên văn agent.py; tên mô hình có thể đổi bằng biến môi trường.')
p('SYSTEM_PROMPT hướng dẫn trả lời bằng tiếng Việt, dùng rag_tool khi cần nội dung Stress.pdf và search_web cho thông tin bên ngoài. Prompt còn đặt giới hạn vai trò, yêu cầu không bịa nguồn và coi tài liệu là dữ liệu tham khảo. Đây là ràng buộc bằng chỉ dẫn cho mô hình; mã chưa có bộ phân loại khủng hoảng hoặc bộ kiểm duyệt độc lập.')
p('Các lớp PromptTemplate, LLMChain, SequentialChain hoặc cú pháp LCEL là kiến thức tích hợp có thể học thêm. Chúng không nằm trong luồng assistant hiện tại. Đổi tên các lớp đó thành lớp LangGraph sẽ làm sai ý nghĩa kỹ thuật.')

h('Chương 5. Embedding và FAISS')
h('5.1. Embedding trong truy xuất',2)
p('Embedding ánh xạ đoạn văn bản và câu hỏi sang vector để tìm các đoạn gần nhau theo ngữ nghĩa. Mô hình embedding khác với mô hình sinh câu trả lời. Trong chương trình, HuggingFaceEmbeddings dùng EMBEDDING_MODEL; giá trị mặc định là VoVanPhuc/sup-SimCSE-VietNamese-phobert-base. ChatGroq thực hiện bước sinh câu trả lời sau truy xuất.')
p('Chương trình đặt HF_HOME và HF_HUB_CACHE dưới .cache/huggingface của dự án nếu môi trường chưa đặt các biến này. Lần truy vấn PDF đầu có thể cần tải mô hình. Cache mô hình trên đĩa không đồng nghĩa với cache đáp án của chatbot.')
h('5.2. Chỉ mục FAISS',2)
p('FAISS.from_documents tạo chỉ mục từ các đoạn và embedding. as_retriever(search_kwargs={"k": self._k}) đặt số đoạn lấy về; giá trị mặc định k=2. Mã hiện không lưu/đọc chỉ mục FAISS bằng save_local/load_local, vì vậy retriever được dựng lại khi tiến trình mới cần truy cập tài liệu.')
fig('retriever_code','Tải PDF, chia đoạn, embedding và tạo retriever FAISS.','Trích nguyên văn Rag_tool.py, hàm _get_retriever().')
p('Top-2 là số lượng đoạn tối đa cần lấy theo cấu hình, không phải mức tin cậy. Mã chưa đặt ngưỡng điểm tương đồng hoặc reranker. Kết quả gần nhất vẫn có thể thiếu nội dung trả lời, do đó cần kiểm tra chất lượng trên bộ câu hỏi có đáp án tham chiếu.')

h('Chương 6. Chunking và chuẩn bị dữ liệu')
p('Chunking chia tài liệu thành các đoạn nhỏ phục vụ embedding và đưa ngữ cảnh vào mô hình. RecursiveCharacterTextSplitter trong code dùng chunk_size=500 và chunk_overlap=50; các giá trị này tính theo độ dài văn bản của splitter mặc định, không nên trình bày là 500 token và 50 token.')
p('Overlap giữ lại một phần văn bản giữa các đoạn liền kề để hạn chế mất liên kết ở ranh giới. Tuy nhiên, đoạn chia vẫn có thể cắt giữa một hướng dẫn hoặc một mục. Các giá trị 500/50 là cấu hình hiện hành, chưa phải kết quả tối ưu được chứng minh bằng benchmark.')
p('PyPDFLoader đọc Stress.pdf theo trang và giữ metadata. Bước _retrieve lấy metadata page rồi cộng 1 để ghi số trang PDF cho người đọc. Đây là số thứ tự trang trong tệp PDF, có thể khác số trang in trên tài liệu.')
table(['Thông số','Giá trị hiện tại','Ý nghĩa'],[
    ('Nguồn','Stress.pdf','Đường dẫn tương đối được quy về thư mục dự án.'),
    ('chunk_size','500','Giới hạn kích thước đoạn theo splitter.'),
    ('chunk_overlap','50','Phần chồng giữa các đoạn.'),
    ('k','2','Mặc định lấy hai đoạn từ retriever.'),
    ('Nguồn trong context','[Stress.pdf, trang N]','Gắn tên tài liệu và trang trước nội dung đoạn.')])
p('Mã chưa có bước OCR cho PDF ảnh, chưa có giao diện nạp tài liệu mới và chưa có quản lý phiên bản tài liệu. Vì vậy không mở rộng phạm vi chức năng thành hệ thống hỏi đáp đa định dạng trong mô tả sản phẩm.')

h('Chương 7. RAG bằng StateGraph')
h('7.1. RAGState và luồng xử lý',2)
p('RAGTOOL là BaseTool tên rag_tool, nhận query theo lược đồ RAGInput. Bên trong công cụ, RAGState là TypedDict có query, context và answer. Đồ thị được dựng khi cần dùng và được giữ lại trong _graph của đối tượng tool.')
fig('rag','Chuẩn bị dữ liệu và đồ thị RAG hai node.','Sơ đồ dựng từ Rag_tool.py; đường đi đồ thị là START → retrieve → answer → END.')
p('Node retrieve gọi retriever bằng query, ghép nội dung các đoạn thành context kèm tên PDF và trang. Node answer kiểm tra context; nếu rỗng thì trả thông báo không có thông tin phù hợp. Nếu có context, node gọi ChatGroq với chỉ dẫn trả lời dựa vào tài liệu và dẫn nguồn/trang.')
fig('rag_graph_code','Khai báo và biên dịch đồ thị RAG.','Trích nguyên văn Rag_tool.py, hàm _build_graph().')
h('7.2. Quan hệ với đồ thị hội thoại',2)
p('ToolNode gọi rag_tool với arguments do mô hình tạo. _run gọi đồ thị RAG bằng invoke và trả answer như chuỗi kết quả công cụ. Chuỗi này đi vào ToolMessage rồi trở lại assistant. Vì vậy một lượt RAG thường có lời gọi mô hình để chọn công cụ, lời gọi mô hình bên trong RAG và lời gọi mô hình để tổng hợp; không nên mô tả mọi câu hỏi chỉ gọi LLM đúng một lần.')
h('7.3. Giới hạn hiện tại',2)
p('Trong đồ thị RAG chưa có các node chấm ngữ cảnh, viết lại truy vấn, kiểm chứng trích dẫn hoặc xác nhận đáp án. Yêu cầu dẫn nguồn hiện nằm trong prompt; mã không kiểm tra máy móc rằng câu trả lời khớp trang PDF. Đồ thị cũng chưa có cơ chế tự chuyển sang Tavily nếu truy xuất tài liệu không đủ.')
p('Khi có exception, _run ghi cảnh báo và trả thông báo chưa thể tra cứu Stress.pdf. Kết quả này vẫn là nội dung tool để assistant xử lý. Nó không mặc nhiên tạo một HTTP 503 hoặc một trường refused theo hợp đồng API riêng.')

h('Chương 8. Bộ nhớ hội thoại và checkpoint')
h('8.1. State trong một lượt và lịch sử nhiều lượt',2)
p('MessagesState cung cấp cấu trúc message; việc giữ trạng thái qua các lần chạy cần persistence theo thread. Khi triển khai, graph.py gọi Agent().create_agent() mà không truyền checkpointer riêng. Agent Server cung cấp cơ chế checkpoint và lịch sử cho các thread của ứng dụng.')
p('Trong unit test, nhóm truyền InMemorySaver vào create_agent để kiểm tra cùng thread dùng lại lịch sử và thread khác được tách biệt. Đây là cấu hình test trong cùng tiến trình, cần phân biệt với persistence của máy chủ dev.')
fig('memory','Cách giao diện dùng thread_id để khôi phục hội thoại.','frontend/app.js: savedThread(), saveThread(), initialize(); README và cấu hình Agent Server.')
h('8.2. Hành vi của giao diện',2)
p('POST /threads tạo hội thoại. Frontend chỉ lưu mã thread bằng khóa support-chat-thread trong sessionStorage. Khi tải lại cùng tab, frontend đọc GET /threads/{id}/state và lấy values.messages. Nếu thread đã mất và API trả 404, giao diện tạo thread mới. Nút Cuộc trò chuyện mới tạo ID khác và không xóa thread trước trên server.')
p('Mỗi lần gửi, frontend truyền một HumanMessage mới; Agent Server khôi phục state của thread để tiếp tục. assistant dùng lịch sử hiện có, không có giới hạn cửa sổ 5 tin trong mã hiện tại. Hội thoại quá dài có thể tăng token và chạm giới hạn context; mã chưa có bước tóm tắt hoặc cắt lịch sử.')
h('8.3. Giới hạn lưu trữ và riêng tư',2)
p('Runtime dev sử dụng bộ nhớ và dữ liệu cục bộ trong .langgraph_api/; không có MySQL trong luồng chạy hiện tại. Cấu hình này dành cho phát triển, chưa có đăng nhập, phân quyền theo tài khoản hoặc chính sách xóa dữ liệu trong giao diện. Không suy ra khả năng lưu bền hoặc cách ly người dùng ở mức sản xuất từ việc tách thread ID. [2]')

h('Chương 9. Tái sử dụng tài nguyên và cache')
p('Chương trình có cơ chế tái sử dụng đối tượng retriever và đồ thị RAG trong tiến trình. _get_retriever kiểm tra _retriever trước và sau Lock để tránh dựng lại chỉ mục nhiều lần khi cùng đối tượng nhận yêu cầu. _build_graph giữ kết quả compile trong _graph.')
table(['Cơ chế','Có trong bản hiện tại?','Phạm vi'],[
    ('Cache mô hình Hugging Face','Có cấu hình đường dẫn','Tệp mô hình trong .cache/huggingface nếu dùng giá trị mặc định.'),
    ('Tái sử dụng retriever','Có','Thuộc đối tượng RAGTOOL trong tiến trình.'),
    ('Tái sử dụng đồ thị RAG','Có','Thuộc đối tượng RAGTOOL trong tiến trình.'),
    ('Cache câu trả lời TTL 300 giây','Không thấy trong code','Không dùng số đo cache hit/miss của bản khác.'),
    ('Semantic answer cache / MySQL','Không','Chỉ có thể đề xuất cho hướng phát triển.')])
p('Tái sử dụng chỉ mục giúp tránh chi phí khởi tạo lặp trong cùng tiến trình nhưng không bỏ qua các lần gọi mô hình để trả lời câu hỏi. Muốn khẳng định tiết kiệm thời gian hoặc token cần thiết kế phép đo riêng; báo cáo này chưa có số liệu đo cache đáp án của bản hiện tại.')

h('Chương 10. Agent và các công cụ')
h('10.1. Cơ chế chọn công cụ',2)
p('Agent đăng ký hai tool RAGTOOL() và SearchWebTool(). ChatGroq được bind_tools với danh sách này. Sau khi mô hình phản hồi, tools_condition kiểm tra có tool_calls hay không; hàm này không đánh giá ngữ nghĩa câu hỏi để phân loại RAG/web. ToolNode thực thi tool_calls và đưa kết quả lại cho assistant.')
fig('agent_code','Code đồ thị hội thoại và vòng gọi công cụ.','Trích nguyên văn agent.py, hàm create_agent().')
p('Đối với lời chào hoặc hội thoại thông thường, system prompt cho phép assistant trả lời trực tiếp. Với thông tin trong PDF hoặc thông tin web, mô hình có thể yêu cầu công cụ. Prompt định hướng lựa chọn nhưng không bảo đảm mô hình luôn chọn đúng. Unit test về tool dùng mô hình giả để xác minh luồng, không phải phép đo tỷ lệ chọn đúng tool của Groq.')
h('10.2. Công cụ tìm kiếm web',2)
p('SearchWebTool có tên search_web và lược đồ đầu vào query. Nếu có langchain_tavily, công cụ dùng TavilySearch; nếu không, mã thử TavilySearchResults từ langchain-community. TAVILY_API_KEY được kiểm tra khi tạo công cụ tìm kiếm. Mỗi lần tìm lấy tối đa ba kết quả.')
fig('tavily_code','Tạo Tavily tool và đường lui tương thích thư viện.','Trích nguyên văn searchweb_tool.py.')
p('_format_results lấy title, content hoặc snippet và URL, rồi cắt phần nội dung mỗi kết quả còn 200 ký tự trước khi gửi về assistant. URL là dữ liệu nguồn trả về từ Tavily; mã chưa có bước duyệt và xác minh độc lập từng trang.')
p('Nếu thiếu khóa hoặc dịch vụ lỗi, _run trả thông báo chưa thể tìm kiếm và ghi cảnh báo chung. Mã tránh trả nguyên exception cho người dùng. Tuy nhiên, xử lý lỗi công cụ bằng chuỗi thông báo không tương đương một hợp đồng lỗi HTTP có các mã riêng cho quota, timeout và xác thực.')

h('Chương 11. API và giao diện')
h('11.1. Cấu hình Agent Server',2)
p('langgraph.json đăng ký graph ID chatbot tại ./graph.py:graph và http.app tại ./main.py:app. graph.py xuất đối tượng graph tạo bởi Agent. Main FastAPI phục vụ / bằng index.html và mount /static; các endpoint quản lý thread và run thuộc Agent Server.')
code((ROOT/'langgraph.json').read_text(encoding='utf-8'))
fig('server_code','FastAPI app phục vụ giao diện trong Agent Server.','Trích nguyên văn main.py; không có endpoint /chatbot trong file này.')
h('11.2. Giao tiếp frontend–backend',2)
table(['Thao tác','Endpoint','Dữ liệu hoặc mục đích'],[
    ('Tạo hội thoại','POST /threads','Body {}; nhận thread_id.'),
    ('Khôi phục lịch sử','GET /threads/{id}/state','Đọc values.messages.'),
    ('Gửi câu hỏi','POST /threads/{id}/runs/wait','assistant_id=chatbot; input.messages; config.'),
    ('Giao diện','GET / và /static/*','HTML, JavaScript, CSS và logo.')])
fig('frontend_code','Payload frontend gửi để chạy graph theo thread.','Trích nguyên văn frontend/app.js; recursion_limit=16 và multitask_strategy=reject.')
p('runs/wait đợi kết quả hoàn tất; giao diện hiện tại không hiển thị token theo luồng streaming. recursion_limit=16 giới hạn bước thực thi của đồ thị, không phải số lượt hội thoại hoặc một deadline tính bằng giây. multitask_strategy=reject yêu cầu từ chối run đồng thời khi thread bận.')
h('11.3. Hiển thị và xử lý lỗi',2)
p('Giao diện chỉ hiển thị tin người dùng và phản hồi cuối của trợ lý; các message công cụ và message AI có tool_calls được ẩn. Nội dung được thêm bằng text node và liên kết http/https, tránh diễn giải đầu ra mô hình thành HTML thực thi. Trong khi chờ, ô nhập và các nút được khóa bằng setBusy.')
p('Nếu request lỗi hoặc không có phản hồi cuối hợp lệ, giao diện hiện thông báo và thử đọc lại state đã commit. Nó không tự gửi lại run. Enter gửi tin, Shift+Enter xuống dòng; textarea đặt maxlength=8000 ở frontend, chưa có kiểm tra độ dài 8000 ký tự riêng trong main.py.')

h('Phần 3. Phân tích thiết kế và kết quả kiểm tra')
h('Chương 12. Thiết kế ứng dụng chatbot')
h('12.1. Chức năng và tình huống sử dụng',2)
table(['Tình huống','Luồng dự kiến theo thiết kế','Căn cứ trong code'],[
    ('Lời chào / chia sẻ cảm xúc','assistant → END','System prompt cho phép không gọi tool.'),
    ('Câu hỏi thuộc Stress.pdf','assistant → tools(rag_tool) → assistant','Tool description và đồ thị RAG.'),
    ('Thông tin bên ngoài / mới','assistant → tools(search_web) → assistant','Tool description và Tavily integration.'),
    ('Tiếp tục hội thoại','Run mới trên cùng thread','API threads/runs cùng MessagesState.'),
    ('Tạo hội thoại khác','POST /threads nhận ID mới','initialize(true) trên frontend.')])
p('Các luồng trên là hành vi dự kiến từ thiết kế và prompt; không xem đây là kết quả model thật chọn đúng nhánh ở mọi đầu vào. Bản hiện tại không có các node classify, grounded, refuse hoặc bộ kiểm tra citation/quote như phiên bản được mô tả ở một số phần của báo cáo cũ.')
h('12.2. Phân chia mô-đun',2)
table(['Tệp / thư mục','Trách nhiệm hiện tại'],[
    ('agent.py','Mô hình, system prompt, hai tool và StateGraph hội thoại.'),
    ('Rag_tool.py','Nạp Stress.pdf, embedding/FAISS, StateGraph RAG.'),
    ('searchweb_tool.py','Gọi Tavily, định dạng kết quả và xử lý lỗi tool.'),
    ('graph.py','Xuất graph cho Agent Server.'),
    ('langgraph.json','Đăng ký chatbot và http.app.'),
    ('main.py','Phục vụ frontend trong Agent Server.'),
    ('frontend/','Giao diện HTML/CSS/JS dùng threads/runs.'),
    ('start_langgraph.py, run_api.bat','Khởi chạy, kiểm tra sẵn sàng và mở trình duyệt.'),
    ('tests/test_chatbot.py','Năm bài kiểm thử tự động với mô hình/công cụ giả.')])
p('LangServe.py chỉ xuất app tương thích từ main.py; dù requirements.txt còn langserve, ứng dụng không dùng add_routes để tạo API LangServe riêng. LangSmith.py và các notebook/chain.py/promt.py là tài liệu học tập, không được graph.py hoặc main.py gọi trong luồng chatbot hiện tại.')
h('12.3. Lựa chọn đồ thị và giới hạn thiết kế',2)
p('Đồ thị hội thoại phù hợp khi cần lặp lại LLM–tool và giữ state theo thread. RAG hai bước có thể viết bằng hàm Python trực tiếp; đồ án dùng StateGraph để tách bước retrieve và answer rõ ràng. Không có phép đo cho thấy dùng đồ thị tự động nhanh hơn pipeline Python trong trường hợp tuyến tính này.')
p('Mã hiện tại chưa triển khai nhiều agent, chưa có bước phê duyệt của con người và chưa dùng store để nhớ thông tin qua nhiều thread. Các chức năng đó có thể xây dựng thêm, nhưng không được tính là phần đã hoàn thành.')

h('Chương 13. Triển khai và kết quả kiểm tra')
h('13.1. Phạm vi kiểm chứng',2)
p('Ngày 05/11/2026, bộ kiểm thử hiện có được chạy bằng lệnh dưới đây và cả năm bài đều đạt. Các ca kiểm thử dùng mô hình giả, retriever giả hoặc mock ChatGroq; không dùng khóa thật để đánh giá đầu ra nhà cung cấp.')
code('.\\.venv\\Scripts\\python.exe -m unittest discover -s tests -v')
result=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
(HERE/'test_results.txt').write_text(result.stdout+result.stderr,encoding='utf-8')
if result.returncode: raise RuntimeError('Bộ kiểm thử không đạt; xem test_results.txt')
table(['Bài kiểm thử','Kết quả','Điều được xác nhận'],[
    ('test_page_and_assets_are_served','Đạt','Trang tiếng Việt và app.js, style.css, logo.svg được phục vụ.'),
    ('test_tool_result_returns_to_assistant','Đạt','Chuỗi message human → ai → tool → ai; tool result trở về assistant.'),
    ('test_thread_memory_and_isolation','Đạt','InMemorySaver giữ lịch sử cùng thread, tách thread khác trong test.'),
    ('test_graph_passes_retrieved_text_and_page_to_model','Đạt','Context và trang 5 của dữ liệu giả được truyền tới model giả.'),
    ('test_tool_error_does_not_expose_provider_secrets','Đạt','Lỗi RAG giả lập không đưa chuỗi bí mật vào câu trả lời tool.')])
h('13.2. Kiểm tra khởi chạy và giao diện',2)
p('Máy chủ LangGraph dev được khởi chạy tại 127.0.0.1:2024. Trang / và kiểm tra /ok đã phản hồi khi khởi chạy. Ảnh giao diện bên dưới chụp từ frontend đang chạy; không chèn nội dung hội thoại hoặc kết quả mô hình giả vào ảnh để làm bằng chứng gọi dịch vụ thật.')
if (ASSETS/'ui.png').exists():
    fig('ui','Giao diện chatbot được chụp tại localhost:2024.','Ảnh chụp frontend của chương trình ngày 05/11/2026; trạng thái hiển thị đúng tại thời điểm chụp.')
else:
    p('Ảnh giao diện chưa được đưa vào do chưa có bản chụp xác nhận; phần mô tả giao diện được đối chiếu trực tiếp với frontend/index.html, style.css và app.js.')
p('Ảnh giao diện chỉ chứng minh hình thức hiển thị và trạng thái hiển thị tại thời điểm chụp. Nó không tự chứng minh RAG truy xuất đúng, Tavily trả nguồn hợp lệ hoặc mô hình nhớ đúng lịch sử.')
h('13.3. Những gì chưa được đo trong bản hiện tại',2)
p('Chưa thực hiện bộ benchmark gọi thật Groq/Tavily cho bản nguồn này, chưa có số đo latency p50/p95, token usage tổng hợp, điểm nội dung hoặc số người dùng đồng thời. Vì vậy các bảng 10/10 hội thoại, 13 phiếu RAG, 57/57 test, graph_id của phiên bản cũ và số đo cache TTL được loại khỏi kết quả hiện tại.')
p('Unit test xác nhận logic điều phối và dữ liệu truyền giữa thành phần; nó không xác nhận chất lượng tư vấn tâm lý, mức chính xác thực tế của mô hình, hiệu quả bảo vệ bằng prompt hoặc persistence qua mọi trường hợp khởi động lại. Bộ test hiện cũng chưa kiểm tra trực tiếp native API threads/runs qua HTTP hoặc công cụ Tavily.')
h('13.4. Kịch bản nghiệm thu đề xuất',2)
table(['Kịch bản cần chạy với dịch vụ thật','Minh chứng cần lưu'],[
    ('Lời chào không cần công cụ','Đầu vào, đầu ra, tool_calls và run/thread ID.'),
    ('Câu hỏi có đáp án trong Stress.pdf','Trang/đoạn kỳ vọng, tool_calls, câu trả lời và nguồn.'),
    ('Câu hỏi ngoài tài liệu','Câu trả lời và cách thể hiện giới hạn dữ liệu.'),
    ('Tìm web','URL, thời điểm lấy nguồn, nội dung trả về và tool_calls.'),
    ('Cùng thread / thread mới','Lịch sử state và kiểm tra nhớ hoặc tách ngữ cảnh.'),
    ('Thiếu PDF, khóa web sai, lỗi mạng','Thông báo tool, lỗi frontend và nhật ký không chứa khóa.')])
p('Để đo hiệu năng, cần ghi phiên bản thư viện, cấu hình model, câu hỏi cố định, trạng thái khởi tạo embedding, số lần gọi LLM và thời gian toàn bộ run. Tách lần đầu tải mô hình/dựng chỉ mục khỏi các lần đã sẵn sàng. Chỉ báo cáo token khi có metadata thực tế; không suy ra 0 token từ việc thiếu dữ liệu.')

h('Phần 4. Tổng kết')
h('Chương 14. Đánh giá và bài học')
p('Kết quả của đề tài là một ứng dụng chatbot dùng LangGraph để điều phối hội thoại và công cụ, có truy xuất tài liệu bằng FAISS, tìm kiếm web qua Tavily và frontend dùng API threads/runs. Việc tách assistant, ToolNode, retrieve và answer giúp người học xác định được nơi gọi mô hình, nơi truy xuất và đường đi của dữ liệu.')
p('Năm bài kiểm thử hiện có đều đạt, cung cấp bằng chứng về vòng gọi công cụ, truyền context/trang, tách lịch sử trong test và phục vụ frontend. Báo cáo không quy các kiểm tra đó thành mức độ chính xác nội dung hoặc hiệu quả hỗ trợ tâm lý.')
p('Các hạn chế chính là phụ thuộc dịch vụ ngoài, khởi tạo embedding có thể chậm, lịch sử chưa được cắt gọn, trích dẫn chưa được kiểm chứng bằng mã và thiếu xác thực/phân quyền. Mô hình vẫn có thể chọn sai công cụ hoặc tạo câu trả lời chưa phù hợp dù system prompt đã quy định giới hạn.')
p('Bài học quan trọng là phải phân biệt khả năng chung của công nghệ với tính năng đã triển khai. StateGraph không tự tạo bộ nhớ bền vững, embedding không phải LLM sinh văn bản, và một hình luồng tham khảo không thể thay thế bằng chứng thực thi của chương trình.')

h('Chương 15. Hướng phát triển')
table(['Ưu tiên','Hướng cải tiến','Cách đánh giá đề xuất'],[
    ('1','Khóa phiên bản và kiểm thử API native qua HTTP','Tái cài môi trường, tạo thread, chạy, đọc lại state.'),
    ('2','Bộ câu hỏi RAG có đáp án và trang tham chiếu','Đo retrieval recall, mức đủ ý và độ chính xác nguồn.'),
    ('3','Kiểm chứng trích dẫn và xử lý thiếu ngữ cảnh','Ca có nguồn, sai trang, ngoài PDF và nguồn rỗng.'),
    ('4','Tóm tắt/cắt lịch sử, quan sát số lần gọi và token','Kiểm tra giữ thông tin quan trọng cùng chi phí thực tế.'),
    ('5','Xác thực, phân quyền và chính sách xóa hội thoại','Kiểm tra truy cập thread giữa các tài khoản.'),
    ('6','Lưu chỉ mục và lựa chọn persistence khi triển khai','Kiểm tra khởi động lại, thay PDF và phục hồi state.')])
p('Nếu bổ sung kiểm duyệt nội dung hoặc hỗ trợ tình huống nghiêm trọng, cần tiêu chí đánh giá chuyên biệt và người có chuyên môn tham gia. Các hướng này là đề xuất cho phiên bản sau; chưa được tính vào chức năng hiện tại.')

h('Tài liệu tham khảo')
refs=[
    ('[1] LangChain. Graph API overview.','https://docs.langchain.com/oss/python/langgraph/graph-api'),
    ('[2] LangChain. Local development & testing.','https://docs.langchain.com/langsmith/local-dev-testing'),
    ('[3] Mã nguồn chương trình được đối chiếu trực tiếp.','agent.py; Rag_tool.py; searchweb_tool.py; graph.py; main.py; langgraph.json; frontend/app.js; tests/test_chatbot.py; README.md.'),
]
for title,url in refs: p(title+' '+url)
p('Các trang [1]–[2] được truy cập ngày 05/11/2026 để đối chiếu khái niệm Graph API và chế độ dev. Mô tả tính năng, thông số và kết quả kiểm thử trong báo cáo lấy từ mã nguồn [3]. Stress.pdf là dữ liệu demo của chương trình; báo cáo không khẳng định độc lập độ tin cậy y khoa của tài liệu.')

h('Phụ lục A. Thực hành trực tiếp với code hiện tại')
h('A.1. Quan sát cấu trúc graph không gọi mô hình',2)
p('Chạy trong thư mục dự án đã cài thư viện. Đoạn mã sau chỉ khởi tạo Agent với mô hình giả rồi in cấu trúc Mermaid; nó không cần GROQ_API_KEY và không gửi yêu cầu tới dịch vụ ngoài. Tên tools vẫn xuất hiện trong đồ thị dù danh sách tool rỗng.')
code('from agent import Agent\n\nclass FakeModel:\n    async def ainvoke(self, messages):\n        from langchain_core.messages import AIMessage\n        return AIMessage(content="Xin chào")\n\ngraph = Agent(model=FakeModel(), tools=[]).create_agent()\nprint(graph.get_graph().draw_mermaid())')
h('A.2. Kiểm tra nhiều lượt bằng InMemorySaver',2)
p('Ví dụ dưới đây dùng FakeModel có sẵn trong tests/test_chatbot.py, khôi phục cùng một thread trong tiến trình Python. Đây là bài thực hành test cục bộ, không thay đổi checkpointer của graph triển khai trên Agent Server.')
code('import asyncio\nimport sys\nsys.path.insert(0, "tests")\nfrom test_chatbot import FakeModel\nfrom agent import Agent\nfrom langgraph.checkpoint.memory import InMemorySaver\n\nasync def demo():\n    graph = Agent(model=FakeModel(), tools=[]).create_agent(InMemorySaver())\n    config = {"configurable": {"thread_id": "lab-1"}}\n    await graph.ainvoke({"messages": [("user", "Toi la An")]}, config)\n    result = await graph.ainvoke(\n        {"messages": [("user", "Ten toi la gi?")]}, config)\n    print(result["messages"][-1].content)\n\nasyncio.run(demo())')
p('FakeModel trong test nối nội dung các HumanMessage; kết quả cho thấy lịch sử được truyền, không phải phép đo khả năng hiểu ngữ cảnh của mô hình thật. Đổi thread_id cần tạo lịch sử riêng. InMemorySaver trong ví dụ mất dữ liệu khi tiến trình kết thúc.')
h('A.3. Câu hỏi tự kiểm tra',2)
for s in [
    'Chỉ ra cạnh nào tạo vòng lặp công cụ và điều kiện nào dẫn đến END.',
    'Giải thích vì sao tools_condition không phải router theo từ khóa.',
    'Xác định nơi cộng 1 vào số trang PDF và nơi đặt k=2.',
    'Phân biệt message state, checkpoint theo thread và sessionStorage.',
    'Giải thích vì sao main.py chạy riêng không cung cấp API threads/runs.',
]: p(s)

h('Phụ lục B. Đối chiếu những nội dung đã sửa')
table(['Mô tả cũ cần sửa','Mô tả đúng với code hiện tại'],[
    ('classify / grounded / refuse, router từ khóa','assistant / tools; LLM tạo tool_calls, tools_condition rẽ nhánh.'),
    ('BM25, top-3, chunk 650/180','FAISS + Hugging Face; top-2; chunk 500/50.'),
    ('Memory MySQL hoặc chỉ 5 tin','Agent Server quản lý thread; assistant dùng messages hiện có.'),
    ('Cache đáp án TTL 300 giây, 128 mục','Không có; chỉ giữ retriever/graph trong đối tượng và cache mô hình.'),
    ('POST /chatbot ở cổng 8000','Native /threads và /threads/{id}/runs/wait ở cổng 2024.'),
    ('RAG grade/rewrite/validate/fallback','Chỉ retrieve → answer; chưa có các node đó.'),
    ('57 test và các benchmark/điểm chấm cũ','5 test của tests/test_chatbot.py; chưa đo chất lượng provider thật.'),
    ('Ảnh code mô hình và API bản cũ','Ảnh code trích từ tệp đang chạy, sơ đồ mới và ảnh frontend hiện tại.')])
p('Giữ thông tin bìa gốc của nhóm 15. Phần nội dung được biên tập lại theo bố cục 15 chương để loại mâu thuẫn giữa nhiều phiên bản. Các ảnh minh họa chương trình cũ không còn được dùng làm bằng chứng của bản hiện tại.')

h('Danh mục hình minh họa')
for i,(name,caption,source) in enumerate(figures,1): p(f'Hình {i}. {caption}')

update=OxmlElement('w:updateFields'); update.set(qn('w:val'),'true'); doc.settings.element.append(update)
doc.core_properties.title='Tìm hiểu và ứng dụng framework LangGraph — Nhóm 15'
doc.core_properties.subject='Đối chiếu mã nguồn chatbot LangGraph ngày 05/11/2026'
doc.core_properties.author='Nhóm 15'
doc.save(OUTPUT)
files=['agent.py','Rag_tool.py','searchweb_tool.py','main.py','graph.py','langgraph.json','frontend/app.js','tests/test_chatbot.py']
manifest={
    'source_report':str(SOURCE),'output':str(OUTPUT),'review_date':'2026-11-05',
    'source_files':{x:hashlib.sha256((ROOT/x).read_bytes()).hexdigest() for x in files},
    'figures':[{'file':name+'.png','caption':caption,'source':source} for name,caption,source in figures],
    'test_count':5,'test_returncode':result.returncode,
}
(HERE/'revision_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(OUTPUT)
print(f'{len(figures)} figures; {len(doc.paragraphs)} paragraphs; {len(doc.tables)} tables')
