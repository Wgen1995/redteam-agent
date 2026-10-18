# 出处:人工构造(硬负例:CSV 导出)
with open(EXPORT_CSV, 'w', newline='') as fh:
    writer = csv.writer(fh)
    for row in rows:
        writer.writerow(row)
