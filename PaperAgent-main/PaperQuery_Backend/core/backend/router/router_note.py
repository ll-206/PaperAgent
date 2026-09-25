from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from core.backend.crud.crud_note import get_note, update_note
from core.backend.schema.noteschema import NoteQuery, NoteRequest, NoteUpdate,NoteUpdateRequest
from core.backend.utils.utils import *
from core.backend.router.dependencies import get_db
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
router = APIRouter()

## 因为笔记是跟用户和知识库唯一绑定的,因此创建和删除笔记的部分都跟创建删除文档绑定到一起了。

#获取笔记
@router.get("/note/getnote")
async def get_current_note(token: str=Depends(oauth2_scheme),db:Session=Depends(get_db),noteRequest:NoteRequest=Depends()):
    #获取当前用户
    user =await get_current_user(token,db)
    request_data = NoteQuery(knowledgeID=noteRequest.knowledgeID, lid=user.lid, uid=noteRequest.documentID)
    notequeryresult = get_note(db, request_data)
    db.commit()
    if not notequeryresult:
        raise HTTPException(status_code=404, detail="Note not found")
    #根据条件进行查询
    return{
        "status_code":200,
        "msg":"get note sucessfully",
        "data":{
            "note":notequeryresult.note
        }
    }

# 更新
@router.post("/note/updatenote")
async def update_current_note(noteUpdateRequest:NoteUpdateRequest,token:str=Depends(oauth2_scheme),db:Session=Depends(get_db)):
    #获取当前用户
    user =await get_current_user(token,db)
    #更新笔记
    updateQueryData=NoteUpdate(
        knowledgeID=noteUpdateRequest.knowledgeID,
        lid=user.lid,
        uid=noteUpdateRequest.documentID,
        note=noteUpdateRequest.note
    )
    update_note(db,updateQueryData)
    db.commit()
    #响应
    
    return{
        "status_code":200,
        "msg":"update note sucessfully",
    }
