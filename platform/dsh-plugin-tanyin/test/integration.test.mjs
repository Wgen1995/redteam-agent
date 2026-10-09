// v0.3 集成测：真 cordis Context 装载三模块，断言工具/技能真挂上
import test from 'node:test';
import assert from 'node:assert/strict';
import { Context } from 'cordis';
import { apply as applyIndex } from '../lib/index.js';
import { apply as applyTools } from '../lib/tools.js';
import { apply as applySkills } from '../lib/skills.js';

test('真 cordis 加载：service+tools+skills 三面齐挂', async () => {
  const ctx = new Context();
  const registered = [];
  ctx.tools = { register: (t) => registered.push(t) };
  const providers = [];
  ctx.skills = { registerProvider: (f) => providers.push(f({})) };
  // 直接调 apply（=loader 装载入口契约）；经 ctx.plugin 会包代理隔离属性赋值，
  // 那层由宿主集成验收（headless 可见性）覆盖，此处测装载契约本身。
  applyIndex(ctx, {});
  applyTools(ctx);
  applySkills(ctx);
  assert.ok(ctx.tanyin, 'service 面: ctx.tanyin 在');
  assert.deepEqual(registered.map((t) => t.name).sort(),
    ['tanyin_book', 'tanyin_gate', 'tanyin_query'], '工具面: 三工具注册');
  assert.equal(providers.length, 1, '技能面: provider 注册');
  const list = await providers[0].list({});
  assert.ok(list.some((s) => s.name === 'tanyin'), 'tanyin 技能可发现');
});
