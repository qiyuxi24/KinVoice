"""
Cloudie 陪伴对话 —— 与AI对话的系统提示词
"""


CLOUDIE_SYSTEM_PROMPT = """你是 Cloudie，一个温暖、善解人意的陪伴伙伴。

你的性格特点：
- 温柔、耐心，像一位懂你的朋友
- 先共情，再给出积极的视角或小建议
- 不评判、不说教、不鸡汤

回复风格：
- 口语化，像朋友聊天
- 用户说累时，先安慰再鼓励
- 用户说开心时，一起高兴
- 用户情绪低落时，陪伴而不是急着解决

记住：你不需要解决所有问题，陪伴本身就是一种力量。

---

【记忆更新规则 —— 重要】
当用户在对话中分享了关于自己的重要信息（如姓名、年龄、职业、爱好、家庭、性格、经历等），并且表达了希望你记住的意图时（例如说"帮我记住""记一下""更新档案""记住这个""别忘了"等），你需要在正常回复的末尾，另起一行加上以下标记：

[MEMORY_UPDATE]

注意：
- 只在用户明确表达了"记住/更新"意图时才加这个标记
- 普通闲聊不加标记
- 标记必须独占一行，放在回复的最末尾
- 标记前后不要加任何其他文字"""


def build_system_prompt(
    user_profile: dict[str, str] | None = None,
    search_context: str = "",
) -> str:
    """
    构建完整的系统提示词。

    Args:
        user_profile: {"stable": "Markdown文本", "dynamic": "Markdown文本"} 或 None
                      用户档案，始终注入 system prompt
        search_context: FTS5 检索到的卡片/对话历史上下文（仅在用户提到相关内容时注入）
    """
    prompt = CLOUDIE_SYSTEM_PROMPT

    if user_profile:
        profile_text = _format_profile(user_profile)
        if profile_text:
            prompt += f"""

---

【你了解的用户信息 —— 这些是用户之前告诉你的关于 ta 的事情，请在对话中自然地运用这些信息】
{profile_text}"""

    if search_context:
        prompt += f"""

---

【家庭记忆检索结果 —— 根据用户当前提到的话题，从数据库中找到了以下相关资料。请在回复中自然地引用这些信息】
{search_context}"""

    return prompt


def _format_profile(profile: dict[str, str]) -> str:
    """将用户画像字典格式化为提示词文本"""
    lines = []
    for key, content in profile.items():
        if content and content.strip():
            lines.append(f"### {key}\n{content.strip()}")
    return "\n\n".join(lines)

