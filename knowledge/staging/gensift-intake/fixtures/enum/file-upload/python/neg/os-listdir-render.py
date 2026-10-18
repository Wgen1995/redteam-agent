# 出处:人工构造(硬负例:目录列表渲染)
entries = sorted(os.listdir(THUMB_DIR))
return render(request, 'gallery/index.html', {'entries': entries})
