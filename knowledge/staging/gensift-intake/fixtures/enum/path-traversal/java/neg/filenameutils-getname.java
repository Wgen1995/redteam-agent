// 出处:人工构造(硬负例:commons-io 取文件名做净化展示)
String base = FilenameUtils.getName(submitted);
String ext = FilenameUtils.getExtension(submitted);
logger.info("parsed {} {}", base, ext);
