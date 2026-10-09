// dsh-plugin-tanyin · v0.3 工具面（真 API：defineTool + ctx.tools.register）
// 接线对照真样本 redteam-bundle/lib/tools.js（import dsh-tools/inject ['tools']/register）。
// 命令映射全部经实探核实（rows/show/replay 已证不存在——幻影命令零容忍）。
// 修复：v0.2 的 execute 调用了不存在的 run()（从未真正可执行）。
import { spawn } from 'node:child_process';
import path from 'node:path';
import os from 'node:os';
import { defineTool } from '@deepseek-ai/dsh-tools';

export const name = 'tanyin-tools';
export const inject = ['tools'];

// 命令→执行器映射：ledger = cli/tanyin-ledger；phases = cli/tanyin-phases
export const TOOL_MAPS = {
  book: {
    'add-goal': 'ledger', 'add-scope': 'ledger', 'add-cred': 'ledger',
    'add-asset': 'ledger', 'add-evidence': 'ledger', 'add-finding': 'ledger',
    'supersede-finding': 'ledger',
  },
  gate: {
    gate: 'phases', 'set-replay-state': 'ledger', 'state-rebuild': 'ledger',
  },
  query: {
    'verify-chain': 'ledger', validate: 'ledger', 'unconsumed-facts': 'ledger',
  },
};

function defaultRepo() {
  return process.env.TANYIN_REPO || path.join(os.homedir(), 'redteam-agent');
}

function runProc(repo, bin, goalDir, command, args, timeoutMs = 60000) {
  return new Promise((resolve) => {
    const prog = bin === 'phases' ? 'tanyin-phases' : 'tanyin-ledger';
    const argv = ['python3', path.join(repo, 'cli', prog), command, '--goal-dir', goalDir, ...args];
    const child = spawn(argv[0], argv.slice(1), { cwd: repo, windowsHide: true });
    let out = '', err = '', timer;
    const done = (rc) => { clearTimeout(timer); resolve({ rc, out, err }); };
    timer = setTimeout(() => { child.kill('SIGKILL'); done(-1); }, timeoutMs);
    child.stdout.on('data', (d) => (out += d));
    child.stderr.on('data', (d) => (err += d));
    child.on('close', (rc) => done(rc));
    child.on('error', (e) => { err += String(e); done(-2); });
  });
}

const LAWS = {
  book: '落账律：一洞一行（一 vuln 一行）；scope 联查断言（资产账面 in_scope 须先立）；EV 卡 raw_request 须完整可执行报文（请求行+HTTP/1.1+Host）；REJECT 是执法不是故障——先修账再重铸。',
  gate: '门律：gate 经 tanyin-phases 按相门判（P0-P6 断言集）；set-replay-state 三态裁决（VERIFIED/REJECTED/not-reproduced）；state-rebuild 仅在账损恢复时用。',
  query: '查律：只读三面——verify-chain（链完整）/validate（表形状）/unconsumed-facts（未消费事实防漏）；查不改账。',
};

function spec(kind) {
  const map = TOOL_MAPS[kind];
  const cmds = Object.keys(map);
  return { map, cmds };
}

function makeTool(toolName, kind) {
  const { map, cmds } = spec(kind);
  return defineTool({
    name: toolName,
    description: `探隐账本 ${kind} 面（${cmds.length} 命令）。${LAWS[kind]}`,
    parameters: {
      goalDir: { type: 'string', required: true, description: '账本 goal 目录（如 ~/.tanyin/battles/battle-26/G-r27）——写操作强制锚定' },
      command: { type: 'string', required: true, description: `命令（${kind} 面：${cmds.join(' / ')}）` },
      args: { type: 'array', items: { type: 'string' }, description: '命令其余参数原样透传（值含空格请自行加引号由 CLI 解析）' },
    },
    output: {
      schema: { type: 'string' },
      render: (_args, value) => String(value),
    },
    async execute(args, exec) {
      if (exec?.signal?.aborted) throw new Error('aborted before dispatch');
      const { goalDir, command } = args;
      const argv = Array.isArray(args.args) ? args.args : [];
      if (!goalDir) throw new Error('tanyin: goalDir 必填（写操作锚定账本根）');
      if (!Object.prototype.hasOwnProperty.call(map, command)) {
        throw new Error(`tanyin: command not in ${toolName} allowlist: ${command}（本面仅 ${cmds.join(' ')}）`);
      }
      const r = await runProc(defaultRepo(), map[command], goalDir, command, argv);
      return JSON.stringify({
        ok: r.rc === 0, command, goalDir, rc: r.rc,
        stdout: r.out, stderr: r.err,
      }, null, 2);
    },
  });
}

/** 注册三工具进 ctx.tools（真 API）。 */
export function apply(ctx) {
  ctx.tools.register(makeTool('tanyin_book', 'book'));
  ctx.tools.register(makeTool('tanyin_gate', 'gate'));
  ctx.tools.register(makeTool('tanyin_query', 'query'));
}

export default { apply, name, inject };
