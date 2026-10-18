# 出处:人工构造(硬负例:导出本地 CSV)
with open(out_path, "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerows(rows)
