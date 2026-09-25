import tiktoken
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
script_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(script_dir, '../..', '.env')  # 假设 .env 文件在上一级目录
load_dotenv(dotenv_path=dotenv_path)


class LLM:
    def __init__(self):
        self.llms = {}

        # OpenAI (保留兼容)
        self.llms['openai'] = ChatOpenAI(
            model="gpt-4o-mini",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_api_base=os.getenv("OPENAI_API_BASE"),
            default_headers={"x-foo": "true"}
        )

        # DeepSeek
        self.llms['deepseek'] = ChatOpenAI(
            model="deepseek-chat",
            openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
            openai_api_base=os.getenv("DEEPSEEK_API_BASE"),
        )

        # Kimi K3 (Moonshot)
        self.llms['kimi'] = ChatOpenAI(
            model="kimi-k3",
            temperature=1,
            openai_api_key=os.getenv("KIMI_API_KEY"),
            openai_api_base=os.getenv("KIMI_API_BASE"),
        )

        self.tokenizer = tiktoken.encoding_for_model('gpt-4o')
        self.chatllm = self.llms['deepseek']

    def get_llm(self, name):
        return self.llms[name]

    def get_all_llms(self):
        return self.llms

    def count_doc_token(self, text):
        return len(self.tokenizer(text)['input_ids'])

    ## 将提示词发送给大模型，获取回复
    def chat_with_llm(self, chat_prompt):
        print(chat_prompt)
        max_retries = 5
        retries = 0
        while retries < max_retries:
            try:
                response = self.chatllm.invoke(chat_prompt)
                return response
            except Exception:
                retries += 1
                if retries == max_retries:
                    print("Max retries reached. Exiting...")
                    return None
                print(f"Retrying... (Attempt {retries})")

    def get_stream_llm(self, model_name='deepseek'):
        """获取用于流式输出的 LLM"""
        if model_name == 'deepseek':
            return ChatOpenAI(
                model="deepseek-chat",
                streaming=True,
                openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
                openai_api_base=os.getenv("DEEPSEEK_API_BASE"),
            )
        elif model_name == 'kimi':
            return ChatOpenAI(
                model="kimi-k3",
                streaming=True,
                temperature=1,
                openai_api_key=os.getenv("KIMI_API_KEY"),
                openai_api_base=os.getenv("KIMI_API_BASE"),
            )
        elif model_name == 'openai':
            return ChatOpenAI(
                model="gpt-4o-mini",
                streaming=True,
                openai_api_key=os.getenv("OPENAI_API_KEY"),
                openai_api_base=os.getenv("OPENAI_API_BASE"),
                default_headers={"x-foo": "true"}
            )
        else:
            # 默认返回 deepseek
            return self.get_stream_llm('deepseek')
