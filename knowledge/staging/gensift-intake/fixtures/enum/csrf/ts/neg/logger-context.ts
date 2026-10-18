// 出处:人工构造(硬负例:日志上下文绑定)
export function withRequestContext(logger: Logger, req: Request): Logger {
  return logger.child({ traceId: req.headers["x-trace-id"], path: req.path });
}
