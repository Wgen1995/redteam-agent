// dsh-plugin-tanyin · v0.3 主入口（service 面）
// 工具面/技能面已拆分至 ./tools.js 与 ./skills.js（各自 cordis 行独立挂载，真 API）。
// 本文件只保留 ctx.tanyin 服务面（战况读取/核心命令桥）。
import { Context } from "cordis";
import { spawn } from "node:child_process";
import path from "node:path";
import os from "node:os";

const CORE_COMMANDS = new Set([
  "add-goal", "add-scope", "add-cred", "add-asset", "add-evidence",
  "add-finding", "validate", "verify-chain", "set-replay-state", "append-timeline",
]);

function defaultRepo() {
  return process.env.TANYIN_REPO || path.join(os.homedir(), "redteam-agent");
}

function runLedger(repo, goalDir, command, args, timeoutMs = 60000) {
  return new Promise((resolve) => {
    const argv = ["python3", path.join(repo, "cli", "tanyin-ledger"), command, "--goal-dir", goalDir, ...args];
    const child = spawn(argv[0], argv.slice(1), { cwd: repo, windowsHide: true });
    let out = "", err = "", timer;
    const done = (rc) => { clearTimeout(timer); resolve({ rc, out, err }); };
    timer = setTimeout(() => { child.kill("SIGKILL"); done(-1); }, timeoutMs);
    child.stdout.on("data", (d) => (out += d));
    child.stderr.on("data", (d) => (err += d));
    child.on("close", (rc) => done(rc));
  });
}

export class TanyinService {
  constructor(ctx, config) {
    this.ctx = ctx;
    this.config = config;
  }
  async ledger(goalDir, command, args = [], timeoutMs) {
    if (!CORE_COMMANDS.has(command)) {
      throw new Error(`tanyin: command not in core allowlist: ${command}`);
    }
    const r = await runLedger(this.config.repo || defaultRepo(), goalDir, command, args, timeoutMs);
    if (r.rc !== 0) throw new Error(`tanyin-ledger ${command} rc=${r.rc}: ${r.err.slice(0, 400)}`);
    return r.out;
  }
}

export const inject = { TanyinService: (ctx, config) => new TanyinService(ctx, config) };

export function apply(ctx, config) {
  // service 面挂载：ctx.tanyin.ledger(goalDir, command, args)（v0.1 起稳定）
  ctx.tanyin = new TanyinService(ctx, config);
  // 工具面（tanyin-tools 行）与技能面（tanyin-skills 行）见各自模块——真 API 独立挂载
  ctx.logger.info("tanyin plugin loaded (service face, %d core commands)", CORE_COMMANDS.size);
}

export { Context };
