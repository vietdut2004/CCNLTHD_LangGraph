"""Draw a source-derived architecture diagram, not an execution trace."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.font_manager import FontProperties

BASE = Path(__file__).resolve().parent
FONT = FontProperties(fname='C:/Windows/Fonts/arial.ttf', size=30)
fig, ax = plt.subplots(figsize=(19, 13.25), dpi=100)
fig.patch.set_facecolor('white')
ax.set(xlim=(0, 19), ylim=(0, 13.25))
ax.axis('off')


def box(x, y, w, h, text, fill='#edf2f6'):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
        boxstyle='round,pad=0.10,rounding_size=0.15',
        facecolor=fill, edgecolor='#344758', linewidth=2))
    ax.text(x+w/2, y+h/2, text, ha='center', va='center',
            fontproperties=FONT, linespacing=1.35, color='#152b3e')


def arrow(points, label=None, label_xy=None, dashed=False):
    for (x1,y1), (x2,y2) in zip(points, points[1:]):
        last = (x2,y2)==points[-1]
        ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2),
            arrowstyle='-|>' if last else '-', mutation_scale=20,
            linewidth=2, color='#435d76', linestyle='--' if dashed else '-'))
    if label:
        ax.text(*label_xy,label, ha='center',va='center',
                fontproperties=FontProperties(fname='C:/Windows/Fonts/arial.ttf',size=23),
                bbox=dict(facecolor='white',edgecolor='none',pad=2))


box(7.4,11.7,4.2,1.0,'START',fill='white')
box(5.2,8.9,8.6,2.0,'classify\nMô hình chọn công cụ (auto)\nĐọc tối đa 5 tin nhắn gần nhất')
box(0.5,5.9,4.6,1.6,'rag\nEmbedding + FAISS\nTra cứu Stress.pdf')
box(6.2,5.9,4.6,1.6,'web\nTìm kiếm Tavily\nNội dung và URL')
box(12.0,5.9,3.9,1.6,'answer\nTrả lời\ntrò chuyện')
box(2.4,2.5,7.4,1.9,'grounded\nSinh câu trả lời từ nguồn\nKiểm tra mã nguồn và trích dẫn')
box(12.0,2.5,6.4,1.9,'refuse\nThiếu bằng chứng hoặc\nyêu cầu vượt phạm vi')
box(8.4,0.2,4.2,1.0,'END',fill='white')

arrow([(9.5,11.7),(9.5,10.9)])
arrow([(7.0,8.9),(2.8,7.5)],'rag_tool',(4.4,8.3))
arrow([(9.5,8.9),(8.5,7.5)],'search_web',(9.4,8.1))
arrow([(12.2,8.9),(13.95,7.5)],'Không gọi tool',(14.2,8.2))
arrow([(2.8,5.9),(4.6,4.4)],'Có đoạn nguồn',(2.4,4.95))
arrow([(8.5,5.9),(7.6,4.4)],'Có kết quả',(8.8,4.95))
arrow([(13.95,5.9),(13.95,4.9),(18.7,4.9),(18.7,1.5),(11.5,1.5),(11.5,1.2)])
arrow([(2.8,5.9),(2.8,5.5),(16.7,5.5),(16.7,4.4)],
      'Nguồn rỗng',(15.8,5.2),dashed=True)
arrow([(8.5,5.9),(8.5,5.5)],dashed=True)
arrow([(9.8,3.45),(12.0,3.45)],'Không hợp lệ',(10.9,3.9),dashed=True)
arrow([(6.1,2.5),(9.5,1.2)],'Có căn cứ',(6.7,1.65))
arrow([(15.2,2.5),(11.5,1.2)])
arrow([(13.8,9.9),(18.0,9.9),(18.0,4.4)],'Ngoài phạm vi',(17.2,8.3),dashed=True)

fig.subplots_adjust(left=0.005,right=0.995,bottom=0.005,top=0.995)
fig.savefig(BASE/'report_runtime_flow.png',dpi=100)
fig.savefig(BASE/'report_runtime_flow.svg')
plt.close(fig)
print(BASE/'report_runtime_flow.png')
