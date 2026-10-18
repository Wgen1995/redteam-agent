// 出处:人工构造(噪音:常量子路径 resolve 链——允许命中)
Path cfgFile = Paths.get(CONFIG_DIR).resolve("app.yaml");
byte[] cfg = Files.readAllBytes(cfgFile);
