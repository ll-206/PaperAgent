
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer
import re
from core.backend.router.req_res_schema import TranslateRequest
from core.backend.services.translate import Translator

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
router = APIRouter()


@router.post("/translate")
def translate(translatetext: TranslateRequest, token: str = Depends(oauth2_scheme)):
    translator = Translator(from_lang="en", to_lang="zh")
    result =translator.translate(re.sub(r'[\n\r\t]', '', translatetext.text))
    return {
    "status_code": 200,
    "msg": "translate successfully",
    "data": {
        "text": result
    }
}
