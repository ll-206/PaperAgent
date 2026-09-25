'''
@Description: 
@Author: qwrdxer
@Date: 2024-07-22 21:31:52
@LastEditTime: 2024-07-23 15:56:37
@LastEditors: qwrdxer
'''
# @File : models.py


from sqlalchemy import TIMESTAMP, Column, Integer, String, Text, func
from sqlalchemy.orm import column_property

from .database import Base


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False)  # 最多50个字符的变长字符串，不允许为空
    password = Column(String(255), nullable=False)  # 最多255个字符的变长字符串，不允许为空
    lid = Column(Text, nullable=False)  # 文本类型，不允许为空

# 定义 Knowledge 表
class Knowledge(Base):
    __tablename__ = 'knowledges'
    id = Column(Integer, primary_key=True, autoincrement=True)
    knowledgeID = Column(String(255), nullable=False)  # 最多255个字符的变长字符串，不允许为空
    lid = Column(String(255), nullable=False)  # 最多255个字符的变长字符串，不允许为空
    knowledgeName = Column(String(255), nullable=False)  # 最多255个字符的变长字符串，不允许为空
    knowledgeDescription = Column(Text)  # 文本类型，可以存储较长的描述信息
    documentNum = Column(Integer)  # 整数类型，用于存储文件相关信息
    vectorNum = Column(Integer)  # 整数类型，用于存储向量信息

# 定义 Document 表
class Document(Base):
    __tablename__ = 'documents'
    id = Column(Integer, primary_key=True, autoincrement=True)
    uid = Column(String(255), nullable=False)  # 最多255个字符的变长字符串，不允许为空
    knowledgeID = Column(String(255), nullable=False)  # 最多255个字符的变长字符串，不允许为空
    lid = Column(String(255), nullable=False)  # 最多255个字符的变长字符串，不允许为空
    documentName = Column(String(255), nullable=False)  # 最多255个字符的变长字符串，不允许为空
    documentPath = Column(String(255), nullable=False)  # 最多255个字符的变长字符串，不允许为空
    documentStatus = Column(Integer)  # 整数类型，用于存储文件状态
    documentVector = Column(Integer)  # 整数类型，用于存储文件向量
    primaryClassification = Column(String(255))  # 最多255个字符的变长字符串，用于存储主分类
    secondaryClassification = Column(String(255))  # 最多255个字符的变长字符串，用于存储次分类
    tags = Column(String(255))  # 最多255个字符的变长字符串，用于存储标签
    documentDescription = Column(Text)  # 文本类型，可以存储较长的描述信息
    createTime = Column(TIMESTAMP, server_default=func.now())  # 增加的时间戳字段，默认当前时间
    createTime_timestamp = column_property(func.extract('epoch', createTime).cast(Integer))
# 临时文件存储
# 定义 Document 表
class TMPDocument(Base):
    __tablename__ = 'tmpdocuments'
    id = Column(Integer, primary_key=True, autoincrement=True)
    uid = Column(String(255), nullable=False)  # 最多255个字符的变长字符串，不允许为空
    knowledgeID = Column(String(255), nullable=False)  # 最多255个字符的变长字符串，不允许为空
    lid = Column(String(255), nullable=False)  # 最多255个字符的变长字符串，不允许为空
    documentName = Column(String(255), nullable=False)  # 最多255个字符的变长字符串，不允许为空
    documentPath = Column(String(255), nullable=False)  # 最多255个字符的变长字符串，不允许为空
    documentStatus = Column(Integer)  # 整数类型，用于存储文件状态
    documentVector = Column(Integer)  # 整数类型，用于存储文件向量
    primaryClassification = Column(String(255))  # 最多255个字符的变长字符串，用于存储主分类
    secondaryClassification = Column(String(255))  # 最多255个字符的变长字符串，用于存储次分类
    tags = Column(String(255))  # 最多255个字符的变长字符串，用于存储标签
    documentDescription = Column(Text)  # 文本类型，可以存储较长的描述信息
    createTime = Column(TIMESTAMP, server_default=func.now())  # 增加的时间戳字段，默认当前时间
    createTime_timestamp = column_property(func.extract('epoch', createTime).cast(Integer))


class Note(Base):
    __tablename__ = 'notes'
    # 表字段映射
    id = Column(Integer, primary_key=True, autoincrement=True)
    lid = Column(String(255), nullable=False)
    knowledgeID = Column(String(255), nullable=False)
    uid = Column(String(255), nullable=False)
    note = Column(Text)


class Post(Base):
    __tablename__ = 'posts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    lid = Column(String(255), nullable=False)
    username = Column(String(255), nullable=False)
    postid = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    publishtime = Column(TIMESTAMP,nullable=True)
    publishtime_timestamp = column_property(func.extract('epoch', publishtime).cast(Integer))
    updatetime = Column(TIMESTAMP,nullable=True)
    updatetime_timestamp = column_property(func.extract('epoch', updatetime).cast(Integer))

class Commit(Base):
    __tablename__ = 'commits'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    lid = Column(String(255), nullable=False)
    postid = Column(String(255), nullable=False)
    username = Column(String(255), nullable=False)
    commitid=Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    publishtime = Column(TIMESTAMP, nullable=True)
    publishtime_timestamp = column_property(func.extract('epoch', publishtime).cast(Integer))


# ===== V2 Research Mode 持久化表 =====
class ResearchTask(Base):
    __tablename__ = 'research_tasks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(64), unique=True, index=True, nullable=False)
    lid = Column(String(255), index=True, nullable=False)
    goal = Column(Text, nullable=False)
    mode = Column(String(32), default="research")
    status = Column(String(32), index=True, nullable=False)
    plan_json = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


class ResearchStep(Base):
    __tablename__ = 'research_steps'

    id = Column(Integer, primary_key=True, autoincrement=True)
    step_id = Column(String(64), nullable=False)
    task_id = Column(String(64), index=True, nullable=False)
    skill_name = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False)
    input_json = Column(Text)
    output_json = Column(Text)
    error = Column(Text)
    duration_ms = Column(Integer)


class SkillRun(Base):
    __tablename__ = 'skill_runs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(64), unique=True, index=True, nullable=False)
    task_id = Column(String(64), index=True)
    step_id = Column(String(64))
    duration_ms = Column(Integer)
    status = Column(String(32))
    error = Column(Text)
    trace_json = Column(Text)


class Artifact(Base):
    __tablename__ = 'artifacts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    artifact_id = Column(String(64), unique=True, index=True, nullable=False)
    task_id = Column(String(64), index=True)
    type = Column(String(32))
    title = Column(String(255))
    data_json = Column(Text)