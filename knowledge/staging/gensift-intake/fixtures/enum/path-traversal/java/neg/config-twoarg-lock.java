// 出处:人工构造(硬负例:配置目录+固定文件名)
File lock = new File(props.getProperty("storage.dir"), "app.lock");
