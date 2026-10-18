// 出处:人工构造(硬负例:URL 仅解析,无外发)
const parsed = new URL(submitted);
const host = parsed.hostname;
logger.info('host=%s', host);
