// 出处:人工构造(硬负例:redact 配置)
const pinoLogger = pino({ redact: ["req.headers.authorization", "password"] });
