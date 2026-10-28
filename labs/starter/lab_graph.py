from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

class State(TypedDict):
    question: str
    answer: str
    branch: str
    turns: int
    usage: dict

def no_usage():
    return dict(input_tokens=0, output_tokens=0, total_tokens=0)

def route(state):
    # TODO: empty -> clarify; question contains LangGraph -> lookup; otherwise answer.
    raise NotImplementedError("Hoàn thành hàm route theo đề bài")


def finish(state, answer, branch, usage):
    return {"answer": answer, "branch": branch,
            "turns": state.get("turns", 0) + 1, "usage": usage}

def clarify(state):
    return finish(state, "Vui lòng nhập câu hỏi.",
                  "clarify", no_usage())

def lookup(state):
    text = "LangGraph tổ chức luồng xử lý bằng State, Node và Edge."
    return finish(state, text, "lookup", no_usage())

def answer(state):
    if state["question"] == "!error":
        raise RuntimeError("Lỗi chủ động của bài lab")
    return finish(state, "Đã nhận: " + state["question"],
                  "answer", no_usage())
builder = StateGraph(State)
for name, fn in [("clarify", clarify), ("lookup", lookup),
                 ("answer", answer)]:
    builder.add_node(name, fn)
builder.add_conditional_edges(START, route, {
    "clarify": "clarify", "lookup": "lookup", "answer": "answer"})
for name in ["clarify", "lookup", "answer"]:
    builder.add_edge(name, END)
graph = builder.compile(checkpointer=InMemorySaver())

def ask(question, thread_id):
    config = {"configurable": {"thread_id": thread_id}}
    return graph.invoke({"question": question}, config)
