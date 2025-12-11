import duckdb

# 替换为你的CSV路径
CSV_PATH = r"D:\BaiduNetdiskDownload\ownthink_v2.csv"

# 连接DuckDB，读取表头
conn = duckdb.connect()
# 仅读取表头（limit 0），快速获取字段名
header_df = conn.execute(f"""
    SELECT * FROM read_csv('{CSV_PATH}', header=True, encoding='utf-8', sep=',') LIMIT 0;
""").df()
# 打印所有字段名
print("CSV的真实字段名：", header_df.columns.tolist())
conn.close()