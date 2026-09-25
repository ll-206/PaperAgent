
import uuid

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer

from core.backend.crud.crud_knowledge import (
    create_knowledge,
    get_knowledge_by_lid,
    get_knowledge_by_name,
    get_knowledge_by_name_uid,
    get_knowledges_statistics,
)
from core.backend.router.dependencies import get_db
from core.backend.schema.schema import KnowledgeCreate
from core.backend.utils.utils import *

router = APIRouter()
##-----------------------------------------------------------
# 获取用户的知识库描述
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

@router.get("/knowledges/getLibraryInfo")
async def describe_knowledge(token: str = Depends(oauth2_scheme),db: Session = Depends(get_db)):
    user =await get_current_user(token,db)
    Knowledgecount,filecount,vectorcount=get_knowledges_statistics(db, user.lid)
    return {
        "status_code": 200,
        "msg": "Get knowledge statistics successfully",
        "data": {
            "libraryID" : user.lid,
            "knowledgeNumSum": Knowledgecount,
            "documentNumSum": filecount,
            "vectorNumSum": vectorcount
        }
    }

# 获取用户拥有的所有 `知识`
@router.get("/knowledges/getKnowledgeList")
async def get_knowledges_all(token: str = Depends(oauth2_scheme),db: Session = Depends(get_db)):
    #获取当前用户
    user =await get_current_user(token,db)
    print(user.lid)
    knowledges=get_knowledge_by_lid(db, user.lid)
    filtered_documents = [{"knowledgeID": knowledge.knowledgeID,"knowledgeName":knowledge.knowledgeName, "knowledgeDescription":knowledge.knowledgeDescription,"documentNum":knowledge.documentNum,"vectorNum":knowledge.vectorNum} for knowledge in knowledges]
    
    print(filtered_documents)
    #根据用户lid获取其拥有的全部知识
    return {"status_code": 200, 
            "msg":"Get knowledge list successfully", 
            "data":{
                "knowledgeList": filtered_documents
            }
            }

# 用户创建新的知识
@router.post("/knowledges/createKnowledge")
async def create_knowledges(knowledge: KnowledgeCreate, token: str = Depends(oauth2_scheme),db: Session = Depends(get_db)):
    user =await get_current_user(token,db)
    # 查询是否有重复的知识名
    if get_knowledge_by_name_uid(db, knowledge.knowledgeName,knowledge.lid):
        return {
            "status_code": 409,
            "msg": "Knowledge name already exists",
        }
    knowledge.lid = user.lid
    knowledge.knowledgeID = str(uuid.uuid1())
    created_k= create_knowledge(db, knowledge)

    return{
        "status_code": 200,
        "msg": "Create knowledge successfully",
        "data": {
            "knowledgeID": created_k.knowledgeID,
            "knowledgeName": created_k.knowledgeName,
            "knowledgeDescription": created_k.knowledgeDescription,
            "documentNum": created_k.documentNum,
            "vectorNum": created_k.vectorNum
        }
    }