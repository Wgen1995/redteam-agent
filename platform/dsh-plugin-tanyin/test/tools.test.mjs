import test from 'node:test';
import assert from 'node:assert/strict';

// v0.2 工具面测试（先于实现——TDD 红灯）
// 依赖注缝：config._runLedger 可注入伪执行器（不 spawn 真 python，测试确定性）
const { defineTools, TOOL_MAPS } = await import('../lib/tools.js');

function fakeRunner(results = {}) {
  return async (bin, goalDir, command, args) =>
    results[command] ?? { rc: 0, out: `OK ${command} ${goalDir} ${args.join(',')}`, err: '' };
}

function makeExec(signal) {
  return { signal: signal ?? new AbortController().signal, defer: () => {} };
}

test('注册：三工具齐备，schema/output/execute 形状完整（ToolDefinition 契约）', () => {
  const tools = defineTools({ _runLedger: fakeRunner() });
  assert.equal(tools.length, 3);
  const names = tools.map((t) => t.name).sort();
  assert.deepEqual(names, ['tanyin_book', 'tanyin_gate', 'tanyin_query']);
  for (const t of tools) {
    assert.equal(typeof t.description, 'string');
    assert.ok(t.description.length > 20, '描述须含律的化身说明');
    assert.ok(t.input, 'input schema 必在');
    assert.ok(t.output, 'output 声明必在（canonical 输出契约）');
    assert.equal(typeof t.execute, 'function');
  }
  // 律即类型面：book 工具描述必须点明 scope 联查与一洞一行
  const book = tools.find((t) => t.name === 'tanyin_book');
  assert.match(book.description, /scope 联查|一洞一行/);
});

test('白名单：跨工具命令越界即拒（不落盘不 spawn）', async () => {
  const book = defineTools({ _runLedger: fakeRunner() }).find((t) => t.name === 'tanyin_book');
  await assert.rejects(
    () => book.execute({ goalDir: '/tmp/G-test', command: 'verify-chain' }, makeExec()),
    /allowlist|不在/,
  );
  const query = defineTools({ _runLedger: fakeRunner() }).find((t) => t.name === 'tanyin_query');
  await assert.rejects(
    () => query.execute({ goalDir: '/tmp/G-test', command: 'add-finding' }, makeExec()),
    /allowlist|不在/,
  );
  await assert.rejects(
    () => book.execute({ goalDir: '', command: 'add-finding' }, makeExec()),
    /goalDir/,
  );
});

test('输出面包：canonical JSON 信封（ok/command/rc/stdout/stderr）+信号尊重', async () => {
  const book = defineTools({ _runLedger: fakeRunner() }).find((t) => t.name === 'tanyin_book');
  const r = await book.execute(
    { goalDir: '/tmp/G-test', command: 'add-asset', args: ['--label', 'svc-x'] },
    makeExec(),
  );
  assert.equal(r.ok, true);
  assert.equal(r.command, 'add-asset');
  assert.equal(r.goalDir, '/tmp/G-test');
  assert.equal(r.rc, 0);
  assert.match(r.stdout, /OK add-asset/);
  // 失败信封：rc!=0 → ok:false 不 throw（模型可读错误面）
  const failing = defineTools({
    _runLedger: async () => ({ rc: 3, out: '', err: 'REJECT add-finding scope mismatch' }),
  }).find((t) => t.name === 'tanyin_book');
  const r2 = await failing.execute(
    { goalDir: '/tmp/G-test', command: 'add-finding', args: [] },
    makeExec(),
  );
  assert.equal(r2.ok, false);
  assert.match(r2.stderr, /REJECT/);
  // 中止信号：已中止即弃
  const ac = new AbortController();
  ac.abort();
  await assert.rejects(
    () => book.execute({ goalDir: '/tmp/G-test', command: 'add-asset' }, makeExec(ac.signal)),
    /abort/i,
  );
});

test('命令映射表：全部命令均经实战核实存在于 CLI（无幻影命令）', () => {
  const all = [...new Set(Object.values(TOOL_MAPS).flatMap((m) => Object.keys(m)))];
  // 实探核实面：rows/show/replay 不存在（已实证），故不在表内
  assert.ok(!all.includes('rows'));
  assert.ok(!all.includes('replay'));
  assert.deepEqual([...new Set(all)].sort(), [
    'add-asset', 'add-cred', 'add-evidence', 'add-finding', 'add-goal', 'add-scope',
    'gate', 'set-replay-state', 'state-rebuild', 'supersede-finding',
    'unconsumed-facts', 'validate', 'verify-chain',
  ]);
});
