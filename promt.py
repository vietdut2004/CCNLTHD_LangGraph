from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
# (Hoặc gộp lại nếu muốn: from langchain_core.messages import SystemMessage, HumanMessage)  

#  Định nghĩa System Message
system_template = (
    "Bạn là một trợ lý đồng cảm, lắng nghe. Tuy nhiên, bạn không phải là chuyên gia y tế "
    "và phải nhắc người dùng tìm sự giúp đỡ chuyên nghiệp nếu vấn đề nghiêm trọng."
)

#  Định nghĩa Human Message với 2 biến
human_template = (
    "Cảm xúc hiện tại của tôi là: {user_feeling}. "
    "Tôi muốn nói về chủ đề: {user_topic}. "
    "Hãy lắng nghe và đưa ra lời phản hồi đồng cảm, có trách nhiệm."
)

#  Tạo ChatPromptTemplate hoàn chỉnh
chat_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessage(content=system_template),
        HumanMessage(content=human_template)
    ]
)

#  Dữ liệu mẫu
data_mau = {
    "user_feeling": "căng thẳng",
    "user_topic": "công việc"
}

#  Tạo prompt hoàn chỉnh với dữ liệu mẫu (sử dụng .format())
prompt_hoan_chinh = chat_prompt.format(**data_mau)

print("--- Prompt Hoàn Chỉnh (Dùng để gửi đến LLM) ---")
print(prompt_hoan_chinh)