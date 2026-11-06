"""Source-based diagrams in the grid and monochrome style of the originals."""
from pathlib import Path
import math
from PIL import Image, ImageDraw, ImageFont

ASSETS = Path(__file__).parent / 'individual_assets'
ASSETS.mkdir(exist_ok=True)
FONT = 'C:/Windows/Fonts/arial.ttf'
BOLD = 'C:/Windows/Fonts/arialbd.ttf'


def diagram(name, title, size, boxes, edges, notes=()):
    im = Image.new('RGB', size, 'white')
    d = ImageDraw.Draw(im)
    for x in range(0, size[0], 20):
        d.line((x, 0, x, size[1]), fill='#e9e9e9' if x % 100 == 0 else '#f4f4f4')
    for y in range(0, size[1], 20):
        d.line((0, y, size[0], y), fill='#e9e9e9' if y % 100 == 0 else '#f4f4f4')
    d.text((size[0]/2, 45), title, font=ImageFont.truetype(BOLD,34), fill='black', anchor='mm')
    for pts, label, label_pos in edges:
        d.line(pts, fill='#282828', width=3)
        a, b = pts[-2], pts[-1]
        angle=math.atan2(b[1]-a[1],b[0]-a[0])
        d.polygon([b,(b[0]-16*math.cos(angle-.4),b[1]-16*math.sin(angle-.4)),
                   (b[0]-16*math.cos(angle+.4),b[1]-16*math.sin(angle+.4))],fill='#282828')
        if label:
            font=ImageFont.truetype(FONT,25)
            rect=d.multiline_textbbox(label_pos,label,font=font,anchor='mm',align='center')
            d.rectangle((rect[0]-8,rect[1]-5,rect[2]+8,rect[3]+5),fill='white')
            d.multiline_text(label_pos,label,font=font,fill='black',anchor='mm',align='center',spacing=6)
    for rect, text in boxes:
        d.rounded_rectangle(rect,radius=13,outline='#282828',width=3,fill='white')
        d.multiline_text(((rect[0]+rect[2])/2,(rect[1]+rect[3])/2),text,
                         font=ImageFont.truetype(FONT,27),fill='black',anchor='mm',align='center',spacing=9)
    for i,line in enumerate(notes):
        d.text((35,size[1]-len(notes)*34-20+i*34),line,font=ImageFont.truetype(FONT,23),fill='#333333')
    path=ASSETS/f'{name}.png'
    im.save(path)
    return path


def create():
    diagram('agent_grid','Đồ thị hội thoại LangGraph — agent.py',(1200,1020),[
        ((430,110,770,190),'START'),
        ((330,300,870,440),'assistant\nSystemMessage + messages → ChatGroq'),
        ((95,630,645,790),'tools — ToolNode\nrag_tool / search_web'),
        ((855,650,1125,770),'END'),
    ],[
        ([(600,190),(600,300)],'',(0,0)),
        ([(470,440),(370,630)],'Có tool_calls',(320,530)),
        ([(790,440),(990,650)],'Không có\ntool_calls',(990,530)),
        ([(95,710),(45,710),(45,370),(330,370)],'ToolMessage',(140,470)),
    ],['Mô hình chọn công cụ; tools_condition kiểm tra tool_calls.',
       'Kết quả công cụ quay lại assistant để tạo phản hồi cuối.',
       'END kết thúc lượt chạy; lịch sử vẫn thuộc thread.'])
    diagram('architecture_grid','Pipeline chatbot hỗ trợ tâm lý',(1500,780),[
        ((70,145,450,290),'Người dùng\nGiao diện HTML / CSS / JavaScript'),
        ((580,145,960,290),'LangGraph Agent Server\nAPI threads / runs'),
        ((1090,145,1440,290),'Đồ thị chatbot\nassistant ↔ tools'),
        ((1080,475,1445,620),'rag_tool: Stress.pdf\nsearch_web: Tavily'),
        ((580,475,960,620),'State và checkpoint\nLịch sử theo thread'),
        ((70,475,450,620),'Hiển thị câu trả lời\nTrên giao diện web'),
    ],[
        ([(450,215),(580,215)],'Gửi tin',(515,180)),
        ([(960,215),(1090,215)],'Chạy graph',(1020,170)),
        ([(1265,290),(1265,475)],'Khi có tool_calls',(1265,380)),
        ([(770,290),(770,475)],'Nạp / lưu state',(770,380)),
        ([(580,550),(450,550)],'Phản hồi',(515,510)),
        ([(260,475),(260,290)],'',(0,0)),
    ],['Frontend dùng POST /threads, GET /threads/{id}/state và POST /threads/{id}/runs/wait.',
       'FastAPI phục vụ giao diện trong Agent Server qua cấu hình http.app.'])
    diagram('rag_grid','Xử lý tài liệu và đồ thị RAG — Rag_tool.py',(1100,1330),[
        ((280,105,820,205),'Stress.pdf → PyPDFLoader'),
        ((280,270,820,375),'Chia đoạn: 500 ký tự\nChồng lấn: 50 ký tự'),
        ((280,445,820,550),'HuggingFaceEmbeddings\n→ FAISS'),
        ((55,690,300,795),'query\nSTART'),
        ((390,680,990,810),'retrieve\nLấy 2 đoạn liên quan + số trang'),
        ((390,900,990,1030),'answer\nChatGroq + context → answer'),
        ((535,1120,845,1200),'END'),
    ],[
        ([(550,205),(550,270)],'',(0,0)),
        ([(550,375),(550,445)],'',(0,0)),
        ([(690,550),(690,680)],'Retriever',(690,615)),
        ([(300,745),(390,745)],'',(0,0)),
        ([(690,810),(690,900)],'context',(690,855)),
        ([(690,1030),(690,1120)],'answer',(690,1075)),
    ],['RAGState gồm query, context, answer. Công cụ có tên rag_tool.',
       'Prompt yêu cầu dẫn Stress.pdf và trang; không tự bảo đảm độ đúng.'])
    diagram('memory_grid','Bộ nhớ hội thoại theo thread',(1500,740),[
        ((60,145,460,285),'Trình duyệt\nsessionStorage: thread_id'),
        ((600,145,1060,285),'LangGraph Agent Server\nTạo thread / đọc state / chạy run'),
        ((600,435,1060,575),'State + checkpoint\nmessages của thread hiện tại'),
        ((1150,435,1450,575),'assistant\nDùng lịch sử'),
        ((60,435,460,575),'Cuộc trò chuyện mới\nTạo thread_id khác'),
    ],[
        ([(460,215),(600,215)],'API',(530,180)),
        ([(830,285),(830,435)],'Nạp và lưu',(830,355)),
        ([(1060,505),(1150,505)],'',(0,0)),
        ([(260,435),(260,285)],'',(0,0)),
    ],['Trình duyệt chỉ giữ mã thread; nội dung hội thoại thuộc máy chủ.',
       'Thread mới tách ngữ cảnh và không xóa thread cũ.'])
    # Installation illustration corresponds to the actual Windows project layout.
    im=Image.new('RGB',(1350,700),'white');d=ImageDraw.Draw(im)
    d.text((50,35),'Cài đặt và chạy LangGraph trên Windows',font=ImageFont.truetype(BOLD,35),fill='black')
    lines=[('1. Tạo môi trường ảo','python -m venv .venv'),
           ('2. Cài thư viện',r'.venv\Scripts\python.exe -m pip install -r requirements.txt'),
           ('3. Cấu hình .env','GROQ_API_KEY; TAVILY_API_KEY (cho tìm kiếm web)'),
           ('4. Khởi động',r'.venv\Scripts\python.exe start_langgraph.py'),
           ('5. Mở trình duyệt','http://127.0.0.1:2024  |  Có thể chạy run_langgraph.bat')]
    for i,(label,code) in enumerate(lines):
        y=105+i*115
        d.text((55,y),label,font=ImageFont.truetype(BOLD,26),fill='black')
        d.rounded_rectangle((50,y+36,1300,y+95),radius=9,fill='#f0f4fa')
        d.text((70,y+52),code,font=ImageFont.truetype(FONT,27),fill='#25344b')
    im.save(ASSETS/'install_current.png')


if __name__ == '__main__':
    create()
