// v0.3 单测：真 API 挂载断言（ctx.tools.register / ctx.skills.registerProvider）+白名单+信封
import test from 'node:test';
import assert from 'node:assert/strict';
import { apply as applyTools } from '../lib/tools.js';
import { apply as applySkills } from '../lib/skills.js';

function mockCtx() {
  const registered = [];
  const providers = [];
  return {
    registered, providers,
    tools: { register: (t) => registered.push(t) },
    skills: { registerProvider: (factory) => providers.push(factory({})) },
    logger: { info: () => {} },
  };
}

test('tools.apply 经真 API 注册三工具（defineTool 形）', () => {
  const ctx = mockCtx();
  applyTools(ctx);
  assert.equal(ctx.registered.length, 3);
  const names = ctx.registered.map((t) => t.name).sort();
  assert.deepEqual(names, ['tanyin_book', 'tanyin_gate', 'tanyin_query']);
  for (const t of ctx.registered) {
    assert.equal(typeof t.execute, 'function', `${t.name}.execute`);
    assert.ok(t.description.length > 20, `${t.name} 描述携带作战律`);
    assert.ok(t.parameters.properties.goalDir, `${t.name} 有 goalDir 参数`);
    assert.ok(t.parameters.required.includes('goalDir'), `${t.name} goalDir 必填`);
  }
});

test('白名单拒越界命令（幻影命令零容忍）', async () => {
  const ctx = mockCtx();
  applyTools(ctx);
  const book = ctx.registered.find((t) => t.name === 'tanyin_book');
  await assert.rejects(
    () => book.execute({ goalDir: '/tmp/x', command: 'rows', args: [] }, {}),
    /allowlist/
  );
  await assert.rejects(
    () => book.execute({ goalDir: '/tmp/x', command: 'replay', args: [] }, {}),
    /allowlist/
  );
});

test('goalDir 缺失即拒（写操作锚定账本根）', async () => {
  const ctx = mockCtx();
  applyTools(ctx);
  const gate = ctx.registered.find((t) => t.name === 'tanyin_gate');
  await assert.rejects(() => gate.execute({ command: 'gate' }, {}), /goalDir/);
});

test('真实 CLI 走通信封（query 面 verify-chain 只读）', async () => {
  const ctx = mockCtx();
  applyTools(ctx);
  const q = ctx.registered.find((t) => t.name === 'tanyin_query');
  const out = await q.execute(
    { goalDir: 'nonexistent-goal-dir-probe', command: 'verify-chain', args: [] },
    {}
  );
  const env = JSON.parse(out);
  assert.equal(env.ok, false);
  assert.equal(env.command, 'verify-chain');
  assert.equal(typeof env.rc, 'number');
});

test('skills.apply 注册 provider 且 list 发现 tanyin 技能', async () => {
  const ctx = mockCtx();
  applySkills(ctx);
  assert.equal(ctx.providers.length, 1);
  const p = ctx.providers[0];
  assert.equal(p.name, 'tanyin-skills');
  const list = await p.list({});
  assert.ok(Array.isArray(list) && list.length >= 1, '发现技能');
  const tanyin = list.find((s) => s.name === 'tanyin');
  assert.ok(tanyin, 'tanyin 技能在场');
  assert.equal(tanyin.source, 'custom');
  assert.equal(tanyin.rank, 550);
  const full = await p.get(tanyin, {});
  assert.ok(full.content.length > 500, '正文按需加载');
  assert.equal(full.resourceBase.kind, 'directory');
});
