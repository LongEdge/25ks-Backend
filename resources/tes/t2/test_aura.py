import pandas as pd
from neo4j import GraphDatabase
import re
URI = "neo4j+s://9829d9f6.databases.neo4j.io"
USER = "neo4j"
PASSWORD = "q3Fkyat8kdoVZdu4VnpTSr8cdkNo1rTJa27T-nkRZgU"
CSV_PATH=r"D:\code\projects\ks\resources\tes\t2\out_v2_chinese_teaching.csv"
driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

df = pd.read_csv(CSV_PATH)
df = df.dropna(subset=["实体", "属性", "值"])
df = df[(df["属性"].astype(str).str.strip() != "") & (df["值"].astype(str).str.strip() != "")]
df = df[df["is_core"] == 1]
def split_entity(s: str):
    s = str(s)
    m = re.match(r"^(.*)\[(.*)\]$", s)
    if m:
        return m.group(1), m.group(2)
    return s, ""

df["entity_name"], df["entity_sense"] = zip(*df["实体"].map(split_entity))

if "match_score" not in df.columns:
    df["match_score"] = None
if "is_core" not in df.columns:
    df["is_core"] = None

rows = df[[
    "entity_name",
    "entity_sense",
    "属性",
    "值",
    "match_score",
    "is_core"
]].to_dict("records")

# ---------- 2. 写入 Neo4j ----------
driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

def write_batch(tx, batch):
    tx.run("""
    UNWIND $rows AS row

    MERGE (e:Entity {
        name: row.entity_name,
        sense: row.entity_sense
    })

    MERGE (e)-[r:HAS_ATTRIBUTE {
        attr: toString(row.`属性`),
        value: toString(row.`值`)
    }]->(e)

    SET r.match_score = row.match_score,
        r.is_core = row.is_core
    """, rows=batch)

# def write_batch(tx, batch):
#     tx.run("""
#     UNWIND $rows AS row
#
#     MERGE (e:Entity {
#         name: row.entity_name,
#         sense: row.entity_sense
#     })
#
#     MERGE (v:Value {
#         value: toString(row.`值`),
#         type: toString(row.`属性`)
#     })
#
#     MERGE (e)-[r:HAS_ATTRIBUTE {attr: toString(row.`属性`)}]->(v)
#     SET r.match_score = row.match_score,
#         r.is_core = row.is_core
#     """, rows=batch)

with driver.session() as session:
    batch_size = 1000
    for i in range(0, len(rows), batch_size):
        session.execute_write(write_batch, rows[i:i+batch_size])
        print(f"imported {min(i+batch_size, len(rows))}/{len(rows)}")

driver.close()
print("import done")