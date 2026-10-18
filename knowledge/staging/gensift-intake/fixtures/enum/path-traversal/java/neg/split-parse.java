// 出处:人工构造(硬负例:String.split 普通解析)
String[] segments = relPath.split("/");
for (String s : segments) {
    depth = depth + 1;
}
