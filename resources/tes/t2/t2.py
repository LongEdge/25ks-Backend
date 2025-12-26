import duckdb
import os

# ===================== 基础配置 =====================
INPUT_CSV_PATH = r"D:\BaiduNetdiskDownload\ownthink_v2.csv"
OUTPUT_CSV_PATH = "out_v2_mini_test.csv"

# 👉 小规模验证：只读前 N 行
LIMIT_INPUT_ROWS = 50_000   # 建议 1万～5万

# ===================== 核心教学概念（强保） =====================
CORE_CONCEPTS = [
    "语文", "修辞", "句式", "文体", "主旨",
    "表达", "理解", "推断", "论证",
    "导学", "板书", "评价"
]

# ===================== 教学关键词（召回） =====================
CHINESE_KEYWORDS = list(set(
    CORE_CONCEPTS + [
        "诗词", "文言", "小说", "散文",
        "作文", "阅读", "写作",
        "比喻", "拟人", "夸张",
        "作者", "作品", "课堂", "备课"
    ]
))

# ===================== 工具函数 =====================
def like_any(field, kws):
    return " OR ".join([f"{field} LIKE '%{kw}%'" for kw in kws])


# ===================== 主流程 =====================
def extract_v2_mini():
    conn = duckdb.connect()
    try:
        print("🧪 开始 V2-Mini 小规模验证...")

        entity_hit = like_any("实体", CHINESE_KEYWORDS)
        attr_hit   = like_any("属性", CHINESE_KEYWORDS)
        value_hit  = like_any("值", CHINESE_KEYWORDS)

        core_hit = " OR ".join([f"实体 LIKE '%{c}%'" for c in CORE_CONCEPTS])

        # ---------- 1. 读取前 N 行 ----------
        # conn.execute(f"""
        # CREATE TEMP TABLE source_limited AS
        # SELECT *
        # FROM read_csv(
        #     '{INPUT_CSV_PATH}',
        #     header = TRUE,
        #     sep = ',',
        #     encoding = 'utf-8',
        #     ignore_errors = TRUE
        # )
        # LIMIT {LIMIT_INPUT_ROWS};
        # """)

        conn.execute(f"""
        CREATE TEMP TABLE source_limited AS
        SELECT *
        FROM read_csv(
            '{INPUT_CSV_PATH}',
            header = TRUE,
            sep = ',',
            encoding = 'utf-8',
            ignore_errors = TRUE
        )
        """)

        total_src = conn.execute("SELECT COUNT(*) FROM source_limited").fetchone()[0]
        print(f"📥 输入行数：{total_src}")

        # ---------- 2. 过滤 + 打分 ----------
        conn.execute(f"""
        CREATE TEMP TABLE filtered AS
        SELECT
            *,
            (
                CASE WHEN {entity_hit} THEN 3 ELSE 0 END +
                CASE WHEN {attr_hit}   THEN 2 ELSE 0 END +
                CASE WHEN {value_hit}  THEN 1 ELSE 0 END
            ) AS match_score,
            CASE
                WHEN {core_hit} THEN 1 ELSE 0
            END AS is_core
        FROM source_limited
        WHERE ({entity_hit} OR {attr_hit} OR {value_hit});
        """)

        hit_cnt = conn.execute("SELECT COUNT(*) FROM filtered").fetchone()[0]
        core_cnt = conn.execute("SELECT COUNT(*) FROM filtered WHERE is_core = 1").fetchone()[0]

        print(f"🎯 命中语文相关：{hit_cnt}")
        print(f"⭐ 核心概念命中：{core_cnt}")

        # ---------- 3. 非核心少量抽样 ----------
        sampled_non_core = min(2000, hit_cnt - core_cnt)

        conn.execute(f"""
        CREATE TEMP TABLE final_sample AS

        SELECT * FROM filtered WHERE is_core = 1

        UNION ALL

        SELECT * FROM (
            SELECT *
            FROM filtered TABLESAMPLE RESERVOIR({sampled_non_core})
            WHERE is_core = 0
        );
        """)

        final_cnt = conn.execute("SELECT COUNT(*) FROM final_sample").fetchone()[0]
        print(f"📦 最终输出行数：{final_cnt}")

        # ---------- 4. 导出 ----------
        conn.execute(f"""
        COPY final_sample
        TO '{OUTPUT_CSV_PATH}'
        WITH (HEADER TRUE, DELIMITER ',');
        """)

        size_mb = os.path.getsize(OUTPUT_CSV_PATH) / (1024 * 1024)
        print("✅ V2-Mini 验证完成")
        print(f"📄 输出文件：{OUTPUT_CSV_PATH}")
        print(f"💾 文件大小：{size_mb:.2f} MB")

        # ---------- 5. 快速 sanity check ----------
        print("\n🔍 示例数据（前 5 行）：")
        preview = conn.execute("""
            SELECT 实体, 属性, 值, match_score, is_core
            FROM final_sample
            LIMIT 5
        """).fetchall()
        for row in preview:
            print(row)

    finally:
        conn.close()


# ===================== 入口 =====================
if __name__ == "__main__":
    extract_v2_mini()
