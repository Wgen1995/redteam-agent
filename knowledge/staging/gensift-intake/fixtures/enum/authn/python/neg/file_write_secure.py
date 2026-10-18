# 出处:人工构造(硬负例:固定路径安全写)
EXPORT_PATH = "/var/app/exports/report.csv"
def write_report(rows) -> None:
    with open(EXPORT_PATH, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(",".join(row) + "\n")
