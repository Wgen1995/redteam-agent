# 出处:人工构造(Flask send_file join 传播形态)
return send_file(os.path.join(EXPORT_DIR, request.args.get('report')))
