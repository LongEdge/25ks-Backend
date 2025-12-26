from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

# 创建数据库引擎
if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False  # 设置为True可以打印SQL语句，便于调试
    )
else:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=False  # 设置为True可以打印SQL语句，便于调试
    )

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建模型基类
Base = declarative_base()


def get_db() -> Session:
    """获取数据库会话的依赖注入函数"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


#==============================
# DuckDB和知识图谱的连接
#==============================

import duckdb
from functools import lru_cache
from app.core.config import settings

# 假设你在 .env 里加了：
# KG_CSV_PATH=resources/tes/t2/out_v2_chinese_teaching.csv
# KG_DB_PATH=data/kg.duckdb

@lru_cache
def get_duckdb():
    con = duckdb.connect(settings.KG_DB_PATH)
    return con

