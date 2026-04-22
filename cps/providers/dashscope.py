from cps.providers.openai_compatible import OpenAICompatibleChatBackend


class DashScopeChatBackend(OpenAICompatibleChatBackend):
    backend_id = "dashscope_openai_chat"
