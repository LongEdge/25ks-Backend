from app.core.database import engine
from app.models.base import Base
from app.models.user import User


print("正在初始化数据库...")

# 创建所有表
Base.metadata.create_all(bind=engine)

print("数据库初始化完成！")

import duckdb
import os
from dotenv import load_dotenv

load_dotenv()

CSV_PATH = os.getenv("KG_CSV_PATH")
DB_PATH = os.getenv("KG_DB_PATH", "resources/kg.duckdb")

con = duckdb.connect(DB_PATH)

print("loading kg csv...")

con.execute(f"""
CREATE TABLE IF NOT EXISTS kg AS
SELECT *
FROM read_csv_auto('{CSV_PATH}');
""")

con.execute("ANALYZE kg;")

print("done")
