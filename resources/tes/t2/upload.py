#
#
# import pandas as pd
#
# path = "./out_v2_chinese_teaching.csv"  # 改成你的文件名
# df = pd.read_csv(path)
#
# print("columns:", list(df.columns))
# print("shape:", df.shape)
# print(df.head(5).to_string(index=False))
# print("\nnull counts:\n", df.isna().sum())

#
# import pandas as pd
# from neo4j import GraphDatabase
#
# URI = "neo4j+s://cf63d19b.databases.neo4j.io"
# USER = "neo4j"
# PWD  = "your_password"
#
# df = pd.read_csv("kg.csv")
# df = df.dropna(subset=["实体", "属性", "值"])
# df = df[(df["属性"].str.strip() != "") & (df["值"].str.strip() != "")]
#
# def split_entity(s):
#     if "[" in s and s.endswith("]"):
#         name, sense = s[:-1].split("[", 1)
#         return name, sense
#     return s, ""
#
# df[["entity_name", "entity_sense"]] = df["实体"].apply(
#     lambda x: pd.Series(split_entity(x))
# )
#
# rows = df.to_dict("records")
#
# driver = GraphDatabase.driver(URI, auth=(USER, PWD))
#
# def import_batch(tx, rows):
#     cypher = """
#     UNWIND $rows AS row
#
#     MERGE (e:Entity {
#         name: row.entity_name,
#         sense: row.entity_sense
#     })
#
#     MERGE (a:Attribute {
#         name: row.属性
#     })
#
#     MERGE (v:Value {
#         value: row.值,
#         type: row.属性
#     })
#
#     MERGE (e)-[r:HAS_ATTRIBUTE]->(v)
#     SET r.match_score = row.match_score,
#         r.is_core = row.is_core
#
#     MERGE (a)-[:DESCRIBES]->(v)
#     """
#     tx.run(cypher, rows=rows)
#
# with driver.session() as session:
#     batch_size = 1000
#     for i in range(0, len(rows), batch_size):
#         session.execute_write(import_batch, rows[i:i+batch_size])
#         print(f"imported {min(i+batch_size, len(rows))}/{len(rows)}")
#
# driver.close()

import os
import re
import math
import base64
import pandas as pd
import requests

TOKEN_URL = "https://api.neo4j.io/oauth/token"
QUERY_URL = "https://cf63d19b.databases.neo4j.io/db/neo4j/query/v2"
CLIENT_ID ="C9skKAMZfisoRQRBSRCc7Wy9mhTVoOp5"
CLIENT_SECRET ="wNVjTn2ACfSgCFlClBcyIV0u2xe7r4C8PHX2W122on_W91i7f4YsD7dQnqFxSk-C"

def get_access_token() -> str:
    r = requests.post(
        TOKEN_URL,
        auth=(CLIENT_ID, CLIENT_SECRET),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={"grant_type": "client_credentials"},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["access_token"]

def post_query(token: str, statement: str, parameters: dict | None = None) -> dict:
    body = {"statement": statement, "parameters": parameters or {}}
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    r = requests.post(QUERY_URL, json=body, headers=headers, timeout=120)
    if r.status_code == 401:
        b64 = base64.b64encode(token.encode("utf-8")).decode("utf-8")
        headers["Authorization"] = f"Bearer {b64}"
        r = requests.post(QUERY_URL, json=body, headers=headers, timeout=120)
    r.raise_for_status()
    return r.json()

def split_entity(s: str):
    s = str(s)
    m = re.match(r"^(.*)\[(.*)\]$", s)
    if m:
        return m.group(1), m.group(2)
    return s, ""

def chunked(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i+size]

if __name__ == "__main__":
    csv_path = "out_v2_chinese_teaching.csv"   # 改成你的文件名
    df = pd.read_csv(csv_path)

    # 只保留完整三元组
    df = df.dropna(subset=["实体", "属性", "值"])
    df = df[(df["属性"].astype(str).str.strip() != "") & (df["值"].astype(str).str.strip() != "")]

    # 拆实体：name + sense
    df["entity_name"], df["entity_sense"] = zip(*df["实体"].map(split_entity))

    # 缺省列处理
    if "match_score" not in df.columns:
        df["match_score"] = None
    if "is_core" not in df.columns:
        df["is_core"] = None

    rows = df[["entity_name","entity_sense","属性","值","match_score","is_core"]].to_dict("records")

    token = get_access_token()

    # 先建约束（Aura 支持 IF NOT EXISTS 的话就不会重复报错；如果报错你再手动在 Browser 跑一次）
    constraints = [
        "CREATE CONSTRAINT entity_unique IF NOT EXISTS FOR (e:Entity) REQUIRE (e.name, e.sense) IS UNIQUE",
    ]
    for c in constraints:
        post_query(token, c)

    # 批量导入
    stmt = (
        "UNWIND $rows AS row "
        "MERGE (e:Entity {name: row.entity_name, sense: row.entity_sense}) "
        "MERGE (v:Value {value: toString(row.`值`), type: toString(row.`属性`)}) "
        "MERGE (e)-[r:HAS_ATTRIBUTE {attr: toString(row.`属性`)}]->(v) "
        "SET r.match_score = row.match_score, r.is_core = row.is_core "
    )

    batch_size = 1000
    total = len(rows)
    for idx, batch in enumerate(chunked(rows, batch_size), start=1):
        post_query(token, stmt, {"rows": batch})
        done = min(idx * batch_size, total)
        print(f"imported {done}/{total}")

    # 简单验证：统计一下
    out = post_query(token, "MATCH (e:Entity) RETURN count(e) AS n")
    print(out)

