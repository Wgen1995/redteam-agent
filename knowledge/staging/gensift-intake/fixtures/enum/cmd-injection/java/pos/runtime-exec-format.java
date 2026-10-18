// 出处:人工构造(String.format 构造命令)
Runtime.getRuntime().exec(String.format("convert %s -resize 100x100 %s", in, out));
