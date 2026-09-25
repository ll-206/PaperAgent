
import os

from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import (
    TencentCloudSDKException,
)
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.tmt.v20180321 import models, tmt_client


class Translator:
    def __init__(self, from_lang, to_lang, secret_id=None, secret_key=None):
        self.from_lang = from_lang
        self.to_lang = to_lang
        self.secret_id = secret_id or os.getenv("TENCENT_SECRET_ID", "")
        self.secret_key = secret_key or os.getenv("TENCENT_SECRET_KEY", "")
    def translate(self, text):
        try: 
            cred = credential.Credential(self.secret_id, self.secret_key)
            httpProfile = HttpProfile()
            httpProfile.endpoint = "tmt.tencentcloudapi.com"

            clientProfile = ClientProfile()
            clientProfile.httpProfile = httpProfile
            client = tmt_client.TmtClient(cred, "ap-beijing", clientProfile) 

            req = models.TextTranslateRequest()
            req.SourceText = text
            req.Source = self.from_lang
            req.Target = self.to_lang
            req.ProjectId = 0

            resp = client.TextTranslate(req) 
            return resp.TargetText

        except TencentCloudSDKException as err:
            # 翻译失败（如未配置密钥）时降级返回原文，避免异常对象流入下游导致类型错误
            print(f"[translate] 翻译失败，降级使用原文: {err}")
            return text

if __name__ == '__main__':
    translator = Translator(from_lang="en", to_lang="zh")
    print(translator.translate("Hello, world!"))
