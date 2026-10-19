import { execFile, spawn, type ChildProcess } from "node:child_process";
import fs from "node:fs";
import net from "node:net";
import os from "node:os";
import path from "node:path";
import { chromium, expect, test, type Locator, type Page } from "@playwright/test";

/**
 * T13 E2E 冒烟——活体全旅程: 合成根 + 真 uvicorn(随机端口,8901 同构)
 * + Playwright channel=chrome。
 *
 * 铁律对齐:
 * - 产品码零改: 只造根/起服务/点页面/断言 DOM;
 * - 合成根 = make_root.py(G-r18 副本+微型在跑仗,T12 造法),TANYIN_HOME
 *   指向它 + channels.json 副件;不碰 ~/.tanyin 与 /tmp/gl-review-home;
 * - 每次全跑新根+新随机端口,afterAll 停服+删根(完清);
 * - say 步真调 LLM;若链 429 全败(say-error 含「模型链全败」)→该步及
 *   其后续确认步如实标 SKIP 不判 FAIL,其余步照常断言;
 * - 断言用各页 data-testid 契约(与其组件测试同源),并附账本真写核验:
 *   dry-run 零落账 / steer+halt 真长行——不止看 UI 文案。
 */

const REPO_ROOT = path.resolve(__dirname, "..", "..");
const SAY_CMD =
  "开一场新仗:目标 e2e-demo.example.com,范围 *.e2e-demo.example.com,只读探测,预算 50 万 tokens,时限 4 小时";
const SAY_RETRY =
  "再确认一次,开一场全新的仗(不是对进行中仗的指令):目标 e2e-demo.example.com,只读探测,范围 *.e2e-demo.example.com,预算 50 万 tokens,时限 4 小时";
const STEER_TEXT = "E2E 冒烟:重点打 10.2.0.7,跳过 10.2.0.9";
const HALT_REASON = "E2E 冒烟全停";

// ---- 服务生命周期(每文件一次: 新根+新端口,afterAll 完清) ----

interface Srv {
  url: string;
  root: string;
  channelsCopied: boolean;
  proc: ChildProcess;
  out: string;
}

let srv: Srv | null = null;
let chromeOk = true;

function freePort(): Promise<number> {
  return new Promise((resolve, reject) => {
    const s = net.createServer();
    s.listen(0, "127.0.0.1", () => {
      const addr = s.address();
      const port = typeof addr === "object" && addr ? addr.port : 0;
      s.close(() => (port ? resolve(port) : reject(new Error("无端口"))));
    });
    s.on("error", reject);
  });
}

test.beforeAll(async () => {
  // env-skip 探测(计划铁律: Playwright channel="chrome",缺则 env-skip)
  const probe = await chromium.launch({ channel: "chrome" }).catch(() => null);
  if (!probe) {
    chromeOk = false;
    return;
  }
  await probe.close();

  // ① 合成根(G-r18 副本 + 微型在跑仗 + channels.json 副件)
  const root = await fs.promises.mkdtemp(path.join(os.tmpdir(), "gl-e2e-t13-"));
  const made = await new Promise<{ channels_copied: boolean }>((resolve, reject) => {
    execFile(
      "python3",
      [path.join(__dirname, "make_root.py"), "--root", root],
      { cwd: REPO_ROOT, maxBuffer: 1 << 24 },
      (err, stdout, stderr) => {
        if (err) reject(new Error("make_root 失败: " + stdout + stderr));
        else {
          try {
            resolve(JSON.parse(stdout.trim().split("\n").pop() as string));
          } catch (e) {
            reject(new Error("make_root 输出非 JSON: " + stdout + stderr));
          }
        }
      },
    );
  });

  // ② 起 uvicorn(随机端口;TANYIN_HOME=合成根 READFACE_ALLOW_DEMO=1)
  const port = await freePort();
  const proc = spawn(
    "python3",
    ["-m", "uvicorn", "server.readface.main:app", "--host", "127.0.0.1", "--port", String(port)],
    {
      cwd: REPO_ROOT,
      env: { ...process.env, TANYIN_HOME: root, READFACE_ALLOW_DEMO: "1" },
      stdio: ["ignore", "pipe", "pipe"],
    },
  );
  const chunks: string[] = [];
  proc.stdout?.on("data", (d) => chunks.push(String(d)));
  proc.stderr?.on("data", (d) => chunks.push(String(d)));
  const url = "http://127.0.0.1:" + port;
  const deadline = Date.now() + 30_000;
  for (;;) {
    if (Date.now() > deadline) {
      proc.kill("SIGKILL");
      throw new Error("uvicorn 30s 未就绪:\n" + chunks.join(""));
    }
    try {
      const r = await fetch(url + "/health");
      if (r.ok) {
        const j = (await r.json()) as { ok?: boolean };
        if (j.ok) break;
      }
    } catch {
      /* 起动中,继续轮询 */
    }
    await new Promise((r) => setTimeout(r, 300));
  }
  srv = { url, root, channelsCopied: made.channels_copied, proc, out: "" };
  console.log(
    "[e2e] 活体就绪 " + url + " 根=" + root + " channels.json 副件=" + made.channels_copied,
  );
});

test.afterAll(async () => {
  if (!srv) return;
  const s = srv;
  srv = null;
  s.proc.kill("SIGTERM");
  await new Promise<void>((resolve) => {
    const t = setTimeout(() => {
      s.proc.kill("SIGKILL");
      resolve();
    }, 5000);
    s.proc.on("exit", () => {
      clearTimeout(t);
      resolve();
    });
  });
  await fs.promises.rm(s.root, { recursive: true, force: true, maxRetries: 3, retryDelay: 200 });
  const gone = !fs.existsSync(s.root);
  console.log("[e2e] 服务已停;合成根" + (gone ? "已清: " : "残留(完清失败!): ") + s.root);
  if (!gone) throw new Error("完清失败,根残留: " + s.root);
});

/** 四态竞等: 先现者胜(say 的确认卡/红条/问询/闲聊)。 */
async function firstVisible(page: Page, ids: string[], timeoutMs: number): Promise<Locator> {
  const locs = ids.map((id) => page.getByTestId(id));
  return Promise.race([
    ...locs.map((l) => l.waitFor({ state: "visible", timeout: timeoutMs }).then(() => l)),
    new Promise<never>((_, rej) =>
      setTimeout(() => rej(new Error("say 流态 " + timeoutMs + "ms 未决")), timeoutMs + 1_000),
    ),
  ]);
}

test("P0 指挥台全旅程冒烟(活体 8901 同构)", async ({ page }) => {
  test.skip(!chromeOk, "chrome 通道不可用→env-skip(计划铁律: channel=chrome,缺则 env-skip)");
  test.skip(srv === null, "活体服务未起(不应发生,除 chrome 探测失败)");
  const base = srv!.url;

  // ③-1 demo 登录 → /chat(空钥缺省+READFACE_ALLOW_DEMO=1→demo 放行)
  await test.step("demo 登录→指挥台", async () => {
    await page.goto(base + "/");
    await expect(page).toHaveURL(/\/login$/);
    await page.locator("#op-key").fill("e2e-smoke");
    await page.getByRole("button", { name: "登录" }).click();
    await expect(page.getByTestId("chat-page")).toBeVisible({ timeout: 15_000 });
    await expect(page).toHaveURL(/\/chat$/);
    await expect(page.getByTestId("topbar").getByText("演示模式:未设密钥")).toBeVisible();
  });

  // ③-2 /chat 人话卡渲染(G-r18 尾窗跨仗合并)
  await test.step("/chat 人话卡渲染", async () => {
    const rows = page.locator('[data-testid="chat-row"]');
    await expect(rows.first()).toBeVisible({ timeout: 15_000 });
    expect(await rows.count()).toBeGreaterThanOrEqual(10);
    await expect(page.locator('[data-testid="moment-time"]').first()).toBeVisible();
  });

  // ③-3 say 一句完整指令(真调 LLM;链全败→SKIP 不判 FAIL)
  let cardSeen = false;
  let llmDead = false;
  let deadWhy = "";
  await test.step("say 一句完整指令(真调 LLM)", async () => {
    console.log("[e2e] channels.json 副件在场=" + srv!.channelsCopied + "(say 走真 LLM 链)");
    for (let attempt = 1; attempt <= 2 && !cardSeen && !llmDead; attempt++) {
      await page.getByTestId("chat-input").fill(attempt === 1 ? SAY_CMD : SAY_RETRY);
      await page.getByRole("button", { name: "发送" }).click();
      await expect(page.getByTestId("say-flow")).toBeVisible();
      const hit = await firstVisible(
        page,
        ["say-card", "say-error", "say-ask", "say-chat"],
        90_000,
      );
      const tid = await hit.getAttribute("data-testid");
      const text = (await hit.textContent()) ?? "";
      if (tid === "say-card") {
        cardSeen = true;
        return;
      }
      if (tid === "say-error") {
        if (text.includes("模型链全败")) {
          llmDead = true;
          deadWhy = text;
          console.log("[e2e] LLM 链全败→say 步 SKIP: " + text);
        } else {
          throw new Error("say 红条(非链全败,如实 FAIL): " + text);
        }
      }
      // ask(缺信息)/chat(误分类)→用更明确的一句话重试一轮
    }
    if (!cardSeen && !llmDead) {
      throw new Error("say 两轮未出确认卡(非链全败,如实 FAIL)");
    }
  });

  // ③-4 确认卡→确认→dry-run 回执气泡(链全败则整步 SKIP)
  if (llmDead) {
    test.info().annotations.push({ type: "SKIP", description: "say/确认/dry-run 步 SKIP: " + deadWhy });
    await test.step.skip("确认卡→确认→dry-run 回执(LLM 链全败→SKIP)", async () => {});
  } else {
    await test.step("确认卡→确认→dry-run 回执气泡", async () => {
      const card = page.getByTestId("say-card");
      const cardText = (await card.textContent()) ?? "";
      expect(cardText, "确认卡应含抽取目标").toContain("e2e-demo.example.com");
      expect(cardText, "确认卡应带授权提示").toContain("授权");
      await page.getByTestId("say-confirm").click();
      await expect(page.getByTestId("say-result")).toBeVisible({ timeout: 60_000 });
      const result = page.getByTestId("say-result");
      await expect(result).toContainText("dry-run 点火演练");
      await expect(result).toContainText("battle-3"); // 根上最大 battle-2→演练号 3
      // 账本真写核验: dry-run 零落账(battles 根纹丝不动)
      const battles = (await fs.promises.readdir(path.join(srv!.root, "battles"))).sort();
      expect(battles).toEqual(["battle-1", "battle-2"]);
    });
  }

  // ③-5 /tasks 列表(两仗卡,统计如实)——/tasks 是 20 页 IA 外深链页
  // (T11 定案,侧栏无入口),直访 URL=真用户入口,兼测 SPA 深链回退。
  await test.step("/tasks 任务列表", async () => {
    await page.goto(base + "/tasks");
    await expect(page.getByTestId("tasks-page")).toBeVisible({ timeout: 15_000 });
    const cards = page.locator('[data-testid="task-card"]');
    await expect(cards).toHaveCount(2, { timeout: 15_000 });
    const b1 = page.locator('[data-testid="task-card"][data-battle="battle-1"]');
    await expect(b1.getByTestId("task-findings")).toContainText("76"); // G-r18 发现数
    await expect(b1.getByTestId("task-goal")).toContainText("G-r18");
    await expect(page.locator('[data-testid="task-card"][data-battle="battle-2"]')).toBeVisible();
  });

  // ③-6 任务详情·会话签(battle-2 在跑,战士会话卡)
  await test.step("任务详情·会话卡", async () => {
    await page.locator('[data-testid="task-card"][data-battle="battle-2"]').click();
    await expect(page.getByTestId("task-detail")).toBeVisible({ timeout: 15_000 });
    await expect(page).toHaveURL(/\/tasks\/battle-2$/);
    await expect(page.getByTestId("task-status")).toHaveAttribute("data-running", "true");
    await expect(page.getByTestId("session-tabs")).toBeVisible();
    expect(await page.locator('[data-testid="session-card"]').count()).toBeGreaterThanOrEqual(2);
    await expect(page.locator('[data-testid="session-card"][data-key="w:w1"]')).toBeVisible();
  });

  // ③-7 组内时刻流(会话卡点开→组流行;返回会话签)
  await test.step("会话组流", async () => {
    await page.locator('[data-testid="session-card"][data-key="w:w1"]').click();
    await expect(page.getByTestId("session-stream")).toBeVisible({ timeout: 15_000 });
    const srows = page.locator('[data-testid="session-row"]');
    // 组流异步拉取: 先等首行可见(容器先现,行随 fetch 到)
    await expect(srows.first()).toBeVisible({ timeout: 15_000 });
    expect(await srows.count()).toBeGreaterThanOrEqual(1);
    await expect(srows.first().locator('[data-testid="moment-time"]')).toBeVisible();
    await page.getByTestId("back-to-sessions").click();
    await expect(page.getByTestId("session-tabs")).toBeVisible();
  });

  // ③-8 /findings 统计+灰卡(G-r18 76+FD-s-9=77;灰卡=待机器复验区)
  let grey76: Locator;
  await test.step("/findings 统计+灰卡", async () => {
    await page.locator('a[href="/findings"]').first().click();
    await expect(page.getByTestId("stat-total")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("stat-total")).toHaveText("77");
    const pend = parseInt((await page.getByTestId("stat-pending").textContent()) ?? "0", 10);
    expect(pend).toBeGreaterThanOrEqual(1);
    await expect(page.getByTestId("stat-verified")).toHaveText(String(77 - pend));
    await expect(page.getByTestId("grey-zone")).toBeVisible();
    grey76 = page.locator('[data-testid="grey-zone"] > div', { hasText: "FD-r18-0076" });
    await expect(grey76).toBeVisible();
    await expect(grey76.getByTestId("reverify-FD-r18-0076")).toBeVisible();
  });

  // ③-9 详情抽屉(证据袋明细+复放史)
  await test.step("发现详情抽屉", async () => {
    await grey76.getByRole("button", { name: "详情" }).click();
    const drawer = page.getByTestId("drawer-FD-r18-0076");
    await expect(drawer).toBeVisible({ timeout: 15_000 });
    await expect(drawer.getByText("证据袋(1)")).toBeVisible();
    await expect(drawer.getByText("EV-r18-0102").first()).toBeVisible(); // 证据袋行(复放史同号另现)
    await expect(drawer.getByText(/复放史/)).toBeVisible();
    await expect(drawer.getByTestId("reverify-FD-r18-0076")).toBeVisible();
  });

  // ③-10 复验(REJECT 授权窗口外如实显示)
  await test.step("复验→REJECT(授权窗口外)如实显示", async () => {
    const drawer = page.getByTestId("drawer-FD-r18-0076");
    await drawer.getByTestId("reverify-FD-r18-0076").click();
    await expect(page.getByTestId("reverify-note")).toBeVisible({ timeout: 90_000 });
    const note = (await page.getByTestId("reverify-note").textContent()) ?? "";
    expect(note, "复验判定应含 REJECT(窗口外如实回报): " + note).toContain("REJECT");
    await drawer.getByRole("button", { name: "关闭" }).click();
    await expect(drawer).toBeHidden();
  });

  // ③-11 回 /chat 插话一句(对在跑仗;流中时刻卡自然来)
  await test.step("回 /chat 插话(对在跑仗 battle-2)", async () => {
    await page.locator('a[href="/chat"]').first().click();
    await expect(page.getByTestId("chat-page")).toBeVisible();
    await expect(page.getByTestId("running-bar")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("running-battle-2")).toBeVisible();
    await page.getByTestId("chat-input").fill(STEER_TEXT);
    const steerBtn = page.getByTestId("steer-battle-2");
    await expect(steerBtn).toBeEnabled();
    await steerBtn.click();
    await expect(page.getByTestId("deck-result")).toBeVisible({ timeout: 60_000 });
    await expect(page.getByTestId("deck-result")).toContainText("插话已入链");
    await expect(page.getByTestId("deck-result")).toContainText("w1");
    await expect(
      page.locator('[data-testid="chat-row"] [data-kind="warrior-steer"]').first(),
      "流中应自然来 warrior-steer 时刻卡",
    ).toBeVisible({ timeout: 20_000 });
  });

  // ③-12 全停确认(确认小卡→halt;流中 deck-halt 时刻卡;账本真写核验)
  await test.step("全停确认", async () => {
    await page.getByTestId("halt-battle-2").click();
    await expect(page.getByTestId("halt-confirm")).toBeVisible();
    await page.getByTestId("halt-reason").fill(HALT_REASON);
    await page.getByTestId("halt-confirm-ok").click();
    await expect(page.getByTestId("deck-result")).toContainText("全停已入链", { timeout: 60_000 });
    await expect(
      page.locator('[data-testid="chat-row"] [data-kind="deck-halt"]').first(),
      "流中应自然来 deck-halt 时刻卡",
    ).toBeVisible({ timeout: 20_000 });
    // 账本真写核验: 3 存量+2 steer+2 stop+1 deck-halt=8 行,原文/原因逐字在链
    const tl = await fs.promises.readFile(
      path.join(srv!.root, "battles", "battle-2", "G-1", "timeline.tsv"),
      "utf8",
    );
    const n = tl.trim().split("\n").length;
    expect(n, "battle-2 timeline 应真长到 8 行,实为 " + n).toBe(8);
    expect(tl).toContain("warrior-steer target=w1 text=" + STEER_TEXT);
    expect(tl).toContain("warrior-steer target=w2 text=" + STEER_TEXT);
    expect(tl).toContain("warrior-stop warrior=w1 reason=" + HALT_REASON);
    expect(tl).toContain("warrior-stop warrior=w2 reason=" + HALT_REASON);
    expect(tl).toContain("deck-halt battle=battle-2 reason=" + HALT_REASON);
  });

  if (llmDead) {
    console.log("[e2e] 结果: 绿(含 1 步 SKIP——LLM 链全败: " + deadWhy + ")");
  } else {
    console.log("[e2e] 结果: 绿(say 步真调 LLM,全旅程无 SKIP)");
  }
});
