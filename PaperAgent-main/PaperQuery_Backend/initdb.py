from datetime import datetime, timezone
import sqlite3
import uuid
import dotenv
import os
dotenv.load_dotenv()
# 创建数据库连接
db_path = os.getenv("DB_PATH")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 创建表
cursor.execute('''
CREATE TABLE IF NOT EXISTS "users" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) NOT NULL,  -- 定义为最多50个字符的变长字符串
    password VARCHAR(255) NOT NULL, -- 定义为最多255个字符的变长字符串
    lid TEXT NOT NULL
)
''')

userlid=uuid.uuid1()
knowledgeID1=uuid.uuid1()
knowledgeID2=uuid.uuid1()
knowledgeID3=uuid.uuid1()
# 插入数据
users_data = [
    ("admin", "123456", "admin"),
    ("qwrdxer", "123456","user"),
    ("hoyi","123456","user"),
    ("CharXL","123456","user")
]

for user in users_data:
    cursor.execute('''
    INSERT INTO "users" (username, password, lid)
    VALUES (?, ?, ?)
    ''', user)


# 查询数据并打印
cursor.execute('SELECT * FROM "users"')
# rows = cursor.fetchall()
# for row in rows:
#     print(row)


# 删除表（如果存在）
cursor.execute('''
DROP TABLE IF EXISTS documents
''')

# 创建表，增加时间戳列
cursor.execute('''
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid VARCHAR(255) NOT NULL,
    knowledgeID VARCHAR(255) NOT NULL,
    lid VARCHAR(255) NOT NULL,
    documentName VARCHAR(255) NOT NULL,
    documentPath VARCHAR(255) NOT NULL,
    documentStatus INTEGER,
    documentVector INTEGER,
    primaryClassification VARCHAR(255),
    secondaryClassification VARCHAR(255),
    tags VARCHAR(255),
    documentDescription TEXT,
    createTime TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# # 查询数据并打印
# cursor.execute('SELECT * FROM documents')
# rows = cursor.fetchall()
# for row in rows:
#     print(row)




# 删除表（如果存在）
cursor.execute('''
DROP TABLE IF EXISTS knowledges
''')

# 创建表，并增加时间戳列
cursor.execute('''
CREATE TABLE IF NOT EXISTS knowledges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    knowledgeID VARCHAR(255) NOT NULL,
    lid VARCHAR(255) NOT NULL,
    knowledgeName VARCHAR(255) NOT NULL,
    knowledgeDescription TEXT,
    documentNum INTEGER,
    vectorNum INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')
# 删除表（如果存在）
cursor.execute('''
DROP TABLE IF EXISTS notes
''')

# 创建表，并增加时间戳列
cursor.execute('''
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lid VARCHAR(255) NOT NULL,
    knowledgeID VARCHAR(255) NOT NULL,
    uid VARCHAR(255) NOT NULL,
    note TEXT
)
''')

# 删除表（如果存在）
cursor.execute('''
DROP TABLE IF EXISTS posts
''')

# 创建表，并增加时间戳列
cursor.execute('''
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lid VARCHAR(255) NOT NULL,
    username VARCHAR(255) NOT NULL,
    postid VARCHAR(255) NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    publishtime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updatetime  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# 删除表（如果存在）
cursor.execute('''
DROP TABLE IF EXISTS commits
''')

# 创建表，并增加时间戳列
cursor.execute('''
CREATE TABLE IF NOT EXISTS commits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lid VARCHAR(255) NOT NULL,
    postid VARCHAR(255) NOT NULL,
    commitid VARCHAR(255) NOT NULL,
    username VARCHAR(255) NOT NULL,
    content TEXT,
    publishtime TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')
# # # 插入数据
# # knowledges_data = [
# #     (f"kid{i+1}", "admin", f"Knowledge {i+1}", f"Description of Knowledge {i+1}", i+1, (i+1) * 100, datetime.now(timezone.utc))
# #     for i in range(3)
# # ]

# # for knowledge in knowledges_data:
# #     cursor.execute('''
# #     INSERT INTO knowledges (knowledgeID, lid, knowledgeName, knowledgeDescription, documentNum, vectorNum, timestamp)
# #     VALUES (?, ?, ?, ?, ?, ?, ?)
# #     ''', knowledge)

# # 提交事务
# conn.commit()

# # 查询数据并打印
# cursor.execute('SELECT * FROM knowledges')
# rows = cursor.fetchall()
# for row in rows:
#     print(row)
conn.commit()
# 关闭连接
conn.close()