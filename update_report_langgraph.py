from __future__ import annotations

import re
import shutil
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path


SRC = Path(r"C:\Users\Admin\Downloads\Các báo cáo cần nôp\Báo cáo nhóm 10.docx")
OUT = Path(r"C:\Users\Admin\Downloads\demo_LangChain (1)\Bao_cao_nhom_10_LangGraph.docx")
ASSETS = Path(r"C:\Users\Admin\Downloads\demo_LangChain (1)\generated_langgraph_assets")

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
ET.register_namespace("w", W_NS)
ET.register_namespace("r", "http://schemas.openxmlformats.org/officeDocument/2006/relationships")
ET.register_namespace("wp", "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing")
ET.register_namespace("a", "http://schemas.openxmlformats.org/drawingml/2006/main")
ET.register_namespace("pic", "http://schemas.openxmlformats.org/drawingml/2006/picture")


TEXT_REPLACEMENTS = [
    (re.compile(r"TÌM HIỀU FRAMEWORK\s+LANGCHAIN", re.IGNORECASE), "TÌM HIỂU FRAMEWORK LANGGRAPH"),
    (re.compile(r"Tổng quan về công nghệ LangChain", re.IGNORECASE), "Tổng quan về công nghệ LangGraph"),
    (re.compile(r"Cài đặt môi trường Lang\s*C\s*hain", re.IGNORECASE), "Cài đặt môi trường LangGraph"),
    (re.compile(r"Cài đặt môi trường LangChain", re.IGNORECASE), "Cài đặt môi trường LangGraph"),
    (re.compile(r"LangChain Expression Language \(LCEL\)", re.IGNORECASE), "LangGraph StateGraph"),
    (re.compile(r"\bLangChain\b"), "LangGraph"),
    (re.compile(r"\bLangchain\b"), "LangGraph"),
    (re.compile(r"\bLANGCHAIN\b"), "LANGGRAPH"),
    (re.compile(r"\blangchain\b"), "langgraph"),
    (re.compile(r"\bChains, Agents, Prompts, Memory và Tools\b", re.IGNORECASE), "StateGraph, Nodes, Edges, State, Prompts và Tools"),
    (re.compile(r"\bChains, Agents, Prompts, Memory and Tools\b", re.IGNORECASE), "StateGraph, Nodes, Edges, State, Prompts and Tools"),
    (re.compile(r"\bChains\b"), "Graphs"),
    (re.compile(r"\bchains\b"), "graphs"),
    (re.compile(r"\brag chain\b", re.IGNORECASE), "RAG graph"),
    (re.compile(r"\bRAG chain\b"), "RAG graph"),
    (re.compile(r"\b5\. Chain\b"), "5. Graph"),
]


PARAGRAPH_REWRITES = [
    (
        re.compile(r"LangGraph\s+–\s+một framework mã nguồn mở phổ biến\s+–\s+được phát triển nhằm khắc phục những điểm yếu đó\.", re.IGNORECASE),
        "LangGraph – một framework mã nguồn mở trong hệ sinh thái LangChain – được phát triển để xây dựng ứng dụng AI theo dạng đồ thị trạng thái, giúp kiểm soát luồng xử lý, nhánh điều kiện và bộ nhớ hội thoại rõ ràng hơn.",
    ),
    (
        re.compile(r"LangGraph cho phép kết hợp sức mạnh của LLM với dữ liệu riêng, công cụ tìm kiếm và API,", re.IGNORECASE),
        "LangGraph cho phép kết hợp LLM với state, tool, retriever, API và checkpoint trong cùng một workflow,",
    ),
    (
        re.compile(r"Kiến thức xây dựng chatbot với LangGraph có thể áp dụng ngay", re.IGNORECASE),
        "Kiến thức xây dựng chatbot và agent workflow với LangGraph có thể áp dụng ngay",
    ),
    (
        re.compile(r"LangGraph giúp chúng em chuyển hóa kiến thức lý thuyết về LLM, NLP, Machine Learning thành ứng dụng thực tiễn,", re.IGNORECASE),
        "LangGraph giúp chúng em chuyển hóa kiến thức lý thuyết về LLM, NLP, Machine Learning thành ứng dụng thực tiễn có luồng xử lý rõ ràng,",
    ),
]


MEDIA_REPLACEMENTS = {
    "word/media/image8.jpeg": "overview.jpeg",
    "word/media/image9.png": "overview.png",
    "word/media/image10.png": "install.png",
    "word/media/image18.png": "stategraph.png",
    "word/media/image19.png": "stategraph.png",
    "word/media/image22.png": "stategraph.png",
    "word/media/image41.png": "stategraph.png",
    "word/media/image58.png": "rag.png",
    "word/media/image59.png": "rag.png",
    "word/media/image70.png": "rag.png",
    "word/media/image83.png": "agent.png",
    "word/media/image84.png": "agent.png",
    "word/media/image85.png": "agent.png",
    "word/media/image86.png": "agent.png",
    "word/media/image93.png": "api.png",
    "word/media/image94.png": "api.png",
}


def replace_text_value(value: str) -> str:
    new = value
    for pattern, repl in TEXT_REPLACEMENTS:
        new = pattern.sub(repl, new)
    for pattern, repl in PARAGRAPH_REWRITES:
        new = pattern.sub(repl, new)
    return new


def iter_text_nodes(root: ET.Element):
    for node in root.iter(f"{{{W_NS}}}t"):
        yield node


def paragraph_text(p: ET.Element) -> str:
    return "".join(node.text or "" for node in iter_text_nodes(p))


def set_paragraph_text(p: ET.Element, text: str) -> None:
    nodes = list(iter_text_nodes(p))
    if not nodes:
        return
    nodes[0].text = text
    for node in nodes[1:]:
        node.text = ""


def process_xml(data: bytes) -> bytes:
    root = ET.fromstring(data)

    for node in iter_text_nodes(root):
        if node.text:
            node.text = replace_text_value(node.text)

    for p in root.iter(f"{{{W_NS}}}p"):
        text = paragraph_text(p)
        if not text:
            continue
        rewritten = replace_text_value(text)
        if rewritten != text or re.search(r"Lang\s*C\s*hain", text, re.IGNORECASE):
            rewritten = re.sub(r"Lang\s*C\s*hain", "LangGraph", rewritten, flags=re.IGNORECASE)
            set_paragraph_text(p, rewritten)

    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def convert_media_name(name: str, data: bytes) -> bytes:
    replacement = MEDIA_REPLACEMENTS.get(name)
    if not replacement:
        return data
    asset = ASSETS / replacement
    if not asset.exists():
        raise FileNotFoundError(asset)
    return asset.read_bytes()


def main() -> None:
    if not SRC.exists():
        raise FileNotFoundError(SRC)
    if OUT.exists():
        OUT.unlink()

    tmp = OUT.with_suffix(".tmp.docx")
    if tmp.exists():
        tmp.unlink()
    shutil.copyfile(SRC, tmp)

    with zipfile.ZipFile(tmp, "r") as zin, zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename.startswith("word/") and item.filename.endswith(".xml"):
                data = process_xml(data)
            elif item.filename.startswith("word/") and item.filename.endswith(".rels"):
                text = data.decode("utf-8")
                text = text.replace(
                    "https://python.langchain.com/docs/how_to/installation",
                    "https://langchain-ai.github.io/langgraph/tutorials/introduction/",
                )
                text = text.replace(
                    "https://python.langchain.com/docs/how_to/qa_chat_history_how_to/",
                    "https://langchain-ai.github.io/langgraph/tutorials/get-started/3-add-memory/",
                )
                data = text.encode("utf-8")
            elif item.filename.startswith("word/media/"):
                data = convert_media_name(item.filename, data)
            zout.writestr(item, data)

    tmp.unlink(missing_ok=True)
    print(OUT)


if __name__ == "__main__":
    main()
