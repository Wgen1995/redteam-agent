# 出处:人工构造(硬负例:markupsafe escape 转义后作变量)
from markupsafe import escape
return render_template_string("<p>{{ v }}</p>", v=escape(user_text))
