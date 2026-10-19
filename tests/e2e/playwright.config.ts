import { defineConfig } from "@playwright/test";

/**
 * T13 E2E 冒烟配置——铁律对齐: Playwright channel="chrome"(缺则套件内
 * env-skip,不在配置层硬跳);workers=1 单旅程串行(登录态+合成根共享);
 * 服务生命周期(合成根+随机端口 uvicorn)由 p0.spec.ts beforeAll/afterAll
 * 全权管理: 每次全跑新根新端口,完清。
 */
export default defineConfig({
  testDir: ".",
  timeout: 420_000, // 单旅程上限: 真调 LLM(链慢时 60s+/轮)+复验子进程+全程 UI
  expect: { timeout: 10_000 },
  workers: 1,
  fullyParallel: false,
  retries: 0,
  reporter: [["list"]],
  outputDir: "test-results",
  use: {
    channel: "chrome",
    headless: true,
    screenshot: "only-on-failure",
  },
});
