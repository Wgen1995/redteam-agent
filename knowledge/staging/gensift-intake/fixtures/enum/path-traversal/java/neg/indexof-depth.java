// 出处:人工构造(硬负例:indexOf 普通检查)
int dotdot = cleaned.indexOf("..");
if (dotdot >= 0) {
    throw new IllegalArgumentException("bad segment");
}
