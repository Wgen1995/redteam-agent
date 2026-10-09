// dsh-plugin-tanyin · MVP 脚手架（v0.1.0）
// 形态 C 插件层：账本 10 核命令原生化（typed tool）+战况读取。
// 约定遵循已核实范本（dsh-bash-local）：ESM + cordis Context + static inject + schemastery。
// ⚠️ 接线面待办：工具面注册 API（dsh-agent-tool-* 的 ToolDefinition 挂载点）在 0.2 接——
//    当前提供 service 面（ctx.tanyin），供后续 tool/web 面复用。
import { Context } from "cordis";
import { spawn } from "node:child_process";
import path from "node:path";
import os from "node:os";
import { defineTools } from "./tools.js";

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
  // service 面挂载（0.1）：ctx.tanyin.ledger(goalDir, command, args)
  ctx.tanyin = new TanyinService(ctx, config);
  // 工具面挂载（0.2）：三 typed tool（book/gate/query）——ToolDefinition 契约（dsh-tools）
  ctx.tanyin.tools = defineTools(config);
  // 宿主如提供工具注册点则直接挂（dsh-agent-tool-* 桥接）
  if (typeof ctx.tool === "function") {
    for (const t of ctx.tanyin.tools) ctx.tool(t);
  }
  // 0.3 待办：client-ui 战况面板（读 ~/.tanyin/battles/*/runner.tsv）
  ctx.logger.info("tanyin plugin loaded (service+tool face, %d core + %d tools)", CORE_COMMANDS.size, ctx.tanyin.tools.length);
}

export { Context };
