from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer

from core.backend.schema.schema import LoginRequest
from core.backend.utils.utils import *

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)],db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=[os.getenv("ALGORITHM")])
        username: str = payload.get("username") 
    except Exception:
        raise credentials_exception
    user = query_user(db, username=username)
    if user is None:
        raise credentials_exception
    return user


@router.post("/login")
def login_for_access_token(loginrequest: LoginRequest,db: Session = Depends(get_db)):
    user = query_user(db, loginrequest.username)
    if not user or user.password != loginrequest.password:
            return  JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=jsonable_encoder({"status_code": status.HTTP_401_UNAUTHORIZED, "msg": "用户名或密码错误"}),
        )
    access_token_expires = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")))
    access_token = create_access_token(
        data={"username": loginrequest.username,"lid":user.lid}, expires_delta=access_token_expires
    )
    return {
        "status_code": 200,
        "msg": "登录成功",
        "data":{"access_token": access_token, "token_type": "Bearer","expire":generate_future_timestamp(int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")))}
    }

# 测试登录状态
@router.get("/testlogin")
async def testlogin(token: str = Depends(oauth2_scheme),db: Session = Depends(get_db)):
    user =await get_current_user(token,db)
    return user