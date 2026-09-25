import erniebot
import os
import dotenv
dotenv.load_dotenv()
models = erniebot.Model.list()
print(os.getenv("BAIDU_ACCTOKEN"))
erniebot.api_type = "aistudio"
erniebot.access_token = os.getenv("BAIDU_ACCTOKEN")

# Create a chat completion
response = erniebot.ChatCompletion.create(model="ernie-3.5", messages=[{"role": "user", "content": "你好，请介绍下你自己"}])
print(response.get_result())