import hashlib
import os
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, File, Form, Path, Request, UploadFile, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from core.agent.chatAgent import *
from core.agent.dataprocessAgent import *
from core.backend.crud.crud_document import *
from core.backend.crud.crud_knowledge import update_knowledge_content
from core.backend.crud.crud_note import create_note, del_note
from core.backend.crud.crud_tmpdocument import create_tmp_document, get_tmp_document_by_filename
from core.backend.router.req_res_schema import DeleteDocument
from core.backend.schema.noteschema import NoteCreate, NoteDelete
from core.backend.schema.schema import *
from core.backend.utils.utils import get_current_user, get_db, get_document_tags, get_filtered_documents, vector_paper_for_tmp
from core.vectordb.chromadb import *

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
router = APIRouter()

@router.get("/document/getDocumentList")
async def get_documents_all(knowledgeID:str, token: str = Depends(oauth2_scheme),db: Session = Depends(get_db)):
    documents=get_document_by_knowledgeID(db, knowledgeID)
    
    filtered_documents = get_filtered_documents(documents)
    return {
            "status_code": 200, 
            "msg":"Get document list successfully", 
            "data":filtered_documents
            }

# 获取document的状态
@router.get("/document/Info")
async def get_document_info(documentID: str,knowledgeID:str,token: str = Depends(oauth2_scheme),db: Session = Depends(get_db)):
    await get_current_user(token,db)
    print(documentID,knowledgeID)
    document =db.query(Document).filter(Document.uid == documentID,Document.knowledgeID==knowledgeID).first()
    return {
        "status_code": 200,
        "msg": "Get document info successfully",
        "data": {
            "documentID": document.uid,
            "documentName": document.documentName,
            "documentStatus": document.documentStatus,
            "vectorNum": document.documentVector,
            "documentTags": get_document_tags(document) if (document.primaryClassification or document.secondaryClassification or document.tags) else [],
            "createTime":document.createTime_timestamp
        }
    }
# 获取文档的总结
@router.get("/document/summarize")
async def get_document_summarize(documentID: str,knowledgeID:str,token: str = Depends(oauth2_scheme),db: Session = Depends(get_db)):
    await get_current_user(token,db)
    document =get_document_by_uid_kid(db, documentID,knowledgeID)
    if not document:
        return {
            "status_code": 404,
            "msg": "未找到指定文件",
        }
    return {
        "status_code": 200,
        "msg": "成功获取文档总结",
        "data": {
            "summarize": document.documentDescription,
        }
    }
## 根据documentID获取pdf文件
@router.get("/document/getFile")
def get_document(documentID: str,knowledgeID:str,db: Session = Depends(get_db)):
    Document =get_document_by_uid_kid(db, documentID,knowledgeID)
    if not Document:
        return {
            "status_code": 404,
            "msg": "document not found",
        }
    file_path =os.getenv("AcadeAgent_DIR")+Document.documentPath
    print("File_path",file_path) # 替换成你实际的 PDF 文件路径
    return FileResponse(file_path)

## 多文件对话-文件上传 
@router.post("/document/multi_file_chat_upload")
async def  upload_document(request:Request,documentFile:UploadFile=File,token: str = Depends(oauth2_scheme),db: Session = Depends(get_db)):
    tmpPDFStoragePath =os.getenv("TMP_PAPER_SAVE_DIR")
    user = await get_current_user(token,db)
    createtime=datetime.datetime.now(timezone.utc)
        # 计算文件的MD5哈希值
    hasher = hashlib.md5()
    file_content = await documentFile.read()
    hasher.update(file_content)
    file_md5 = hasher.hexdigest()
    print("FILE_MD5",file_md5)
    #检查临时知识库中是否存在该文件
    document =get_tmp_document_by_filename(db, file_md5)
    if document:
        #直接返回
        return {
            "status_code": 200,
            "msg": "upload successfully",
            "data": {
                "documentID": document.uid,
                "documentName": document.documentName,
                "vectorNum": 0,
                "createTime": int(createtime.timestamp())
            }
        }

        
    # 重置文件内容读取位置，以便后续写入文件
    documentFile.file.seek(0)
    print("saving ",documentFile.filename,"...")
    file_path=os.path.join(tmpPDFStoragePath,documentFile.filename)
    with open(file_path, "wb") as buffer:
        buffer.write(documentFile.file.read())
    uid=cal_file_md5(file_path)
    
    print("UID",uid)
    # 向量化
    vectornum=vector_paper_for_tmp(file_path,uid,"THIS_IS_A_TMP_KID",request.app.chroma_db)

    createtime=datetime.datetime.now(timezone.utc)
    document = TMPDocumentCreate(documentName=documentFile.filename,documentPath=os.path.join("/res/tmppdf/",documentFile.filename),documentStatus=0,uid=uid,knowledgeID="THIS_IS_A_TMP_KID",lid="THIS_IS_A_TMP_LID",createTime=createtime)

    create_tmp_document(db=db, document=document)
    return {
        "status_code": 200,
        "msg": "upload successfully",
        "data": {
            "documentID": uid,
            "documentName": documentFile.filename,
            "vectorNum": vectornum,
            "createTime": int(createtime.timestamp())
        }
    }


## 单文件上传
@router.post("/document/upload")
async def  upload_document(knowledgeID:str=Form(),documentFile:UploadFile=File, token: str = Depends(oauth2_scheme),db: Session = Depends(get_db)):
    pdf_storage_path =os.getenv("PAPER_SAVE_DIR")
    user =await get_current_user(token,db)

        # 计算文件的MD5哈希值
    hasher = hashlib.md5()
    file_content = await documentFile.read()
    hasher.update(file_content)
    file_md5 = hasher.hexdigest()
    print("FILE_MD5",file_md5)
    document =get_document_by_uid_kid(db, file_md5, knowledgeID)
    if document:
        # 同一知识库内已存在该文件（按文件内容 MD5 判断），则不再重复上传
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=jsonable_encoder({                
                "status_code": status.HTTP_409_CONFLICT,
                "msg": "该知识库中已存在此文件",
                }),
        )
        
    # 重置文件内容读取位置，以便后续写入文件
    documentFile.file.seek(0)
    print("saving ",documentFile.filename,"...")
    file_path=os.path.join(pdf_storage_path,documentFile.filename)
    with open(file_path, "wb") as buffer:
        buffer.write(documentFile.file.read())
    uid=cal_file_md5(file_path)

    print("UID",uid)
    createtime=datetime.datetime.now(timezone.utc)
    document = DocumentCreate(documentName=documentFile.filename,documentPath=os.path.join("/res/pdf/",documentFile.filename),documentStatus=0,uid=uid,knowledgeID=knowledgeID,lid=user.lid,createTime=createtime)
    ### 增加创建笔记
    addnotedata=NoteCreate(
        uid=uid,knowledgeID=knowledgeID,lid=user.lid,
    )
    create_note(db=db,info=addnotedata)
    ###
    create_document(db=db, document=document)
    return {
        "status_code": 200,
        "msg": "upload successfully",
        "data": {
            "documentID": uid,
            "documentName": documentFile.filename,
            "documentStatus": 0,
            "documentTags": [],
            "knowledgeID": knowledgeID,
            "vectorNum": 0,
            "createTime": int(createtime.timestamp())
        }
    }

## 文件删除
@router.post("/document/delete")
async def delete_document(deleteDocument:DeleteDocument,request:Request,token: str = Depends(oauth2_scheme),db: Session = Depends(get_db)):
    user =await get_current_user(token,db)
    document =get_document_by_uid_kid(db, deleteDocument.documentID,deleteDocument.knowledgeID)
    if not document:
        return {
            "status_code": 404,
            "msg": "文件不存在",
        }
    #在document表中删除
    db.delete(document)
    db.commit()
    #在向量数据库中删除
    request.app.chroma_db.delete_paper_from_layer1(deleteDocument.knowledgeID,deleteDocument.documentID)
    request.app.chroma_db.delete_paper_from_layer2(deleteDocument.knowledgeID,deleteDocument.documentID)
    #更新知识库状态 file -1  vector -N
    update_knowledge_content(db,-document.documentVector,-1,document.knowledgeID)
    ### 增加删除笔记
    delnotedata=NoteDelete(
        uid=deleteDocument.documentID,knowledgeID=deleteDocument.knowledgeID,lid=user.lid,
    )
    del_note(db=db,delNote=delnotedata)
    ###
    #删除文件
    doc =get_document_by_uid(db, deleteDocument.documentID)#检查其他知识中是否还有该文档,如果有就不需要删除向量和源文件
    if not doc: #如果没有则进行删除
        file_path =os.getenv("AcadeAgent_DIR")+document.documentPath
        os.remove(file_path)
    return {
        "status_code": 200,
        "msg": "文件删除成功",
    }