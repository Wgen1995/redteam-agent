# 出处:人工构造(Flask send_file 拼接形态)
rid = request.args.get('rid')
return send_file(REPORTS + '/' + rid)
