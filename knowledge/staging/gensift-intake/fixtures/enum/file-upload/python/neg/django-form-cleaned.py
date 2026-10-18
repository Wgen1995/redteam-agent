# 出处:人工构造(硬负例:表单清洗数据)
title = form.cleaned_data['title']
tags = form.cleaned_data.get('tags', [])
