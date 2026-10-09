// dsh-plugin-tanyin · v0.2 工具面（agent typed-tool face）
// ToolDefinition 契约遵循 dsh-tools（schema+output+execute(args,exec)→canonical JSON，尊重 exec.signal）。
// 命令映射全部经实探核实（rows/show/replay 已证不存在——幻影命令零容忍）。
import { spawn } from 'node:child_process';
import path from 'node:path';
import os from 'node:os';
import Schema from '@deepseek-ai/schemastery';

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

function inputSchema(kind, cmds) {
  return Schema.object({
    goalDir: Schema.string().required().description('账本 goal 目录（如 ~/.tanyin/battles/battle-24/G-r25）——写操作强制锚定'),
    command: Schema.string().required().description(`命令（${kind} 面：${cmds.join(' / ')}）`),
    args: Schema.array(String).default([]).description('命令其余参数原样透传（如 --label svc-x）'),
  });
}

export function defineTools(config = {}) {
  const run = config._runLedger || ((bin, goalDir, command, args) =>
    runProc(config.repo || defaultRepo(), bin, goalDir, command, args, config.timeoutMs));

  const make = (name, kind) => {
    const map = TOOL_MAPS[kind];
    const cmds = Object.keys(map);
    const tool = {
      name,
      description: `探隐账本 ${kind} 面（${cmds.length} 命令）。${LAWS[kind]}`,
      input: inputSchema(kind, cmds),
      output: Schema.object({
        ok: Schema.boolean().description('rc==0'),
        command: Schema.string(),
        rc: Schema.number(),
        stdout: Schema.string(),
        stderr: Schema.string(),
      }).description('canonical 信封：账本输出原样+执行面'),
      async execute(args, exec) {
        if (exec?.signal?.aborted) throw new Error('aborted before dispatch');
        const { goalDir, command, argv } = { argv: [], ...args };
        if (!goalDir) throw new Error('tanyin: goalDir 必填（写操作锚定账本根）');
        if (!Object.prototype.hasOwnProperty.call(map, command)) {
          throw new Error(`tanyin: command not in ${name} allowlist: ${command}（本面仅 ${cmds.join(' ')}）`);
        }
        const r = await run(map[command], goalDir, command, argv);
        return {
          ok: r.rc === 0, command, goalDir, rc: r.rc,
          stdout: r.out, stderr: r.err,
        };
      },
    };
    return tool;
  };

  return [make('tanyin_book', 'book'), make('tanyin_gate', 'gate'), make('tanyin_query', 'query')];
}
