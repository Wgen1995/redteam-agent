// 出处:人工构造(硬负例:绝对路径守卫)
if (path.isAbsolute(submitted)) {
  throw new Error('absolute path not allowed');
}
