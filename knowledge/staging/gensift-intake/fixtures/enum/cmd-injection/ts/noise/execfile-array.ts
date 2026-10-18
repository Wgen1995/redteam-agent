// 出处:人工构造(噪音:execFile 不走 shell——允许命中,由五步判别)
const { execFile } = require('child_process');
execFile('ffmpeg', ['-i', input, '-vn', output], cb);
