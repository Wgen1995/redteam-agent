# 钥匙进位说明（/tmp/channels.json）· 2026-10-20

> 缺口背景：全史综合档 §⑤A桶「模型钥匙」——`/tmp/channels.json` 被重启清空、全盘无钥，点火前用户一次性粘贴（first-battle-checklist:30-31）。本档=贴钥时的**形状/位置/后端对应**说明。

## 一、文件形状（6 字段/道，有序数组）

```json
[
  {
    "name": "glm-4.7",                  // 道名(自命名,入budget/事件可见)
    "provider": "openai_compatible",    // 供应商协议形
    "model": "glm-4.7",                 // 模型名(发请求用)
    "base_url": "https://open.bigmodel.cn/api/coding/paas/v4",
    "api_key": "<真钥>",                 // ← 唯一要贴的位
    "priority": 1                       // 故障转移顺序(小者先)
  }
]
```

- 校验执法在 `cli/warrior/__main__.py:_load_channels`：须非空 JSON 数组、逐道必有 name/model/base_url/api_key（缺=环境问题拒启）。
- 可复制模板：`docs/runbook/channels.template.json`（同仓还有 `cli/warrior/channels.example.json`，占位符形状有测试钉——两件都**永不填真钥**）。

## 二、哪个后端吃哪个钥匙

| 后端（cli/backends/） | 吃不吃 /tmp/channels.json | 说明 |
|---|---|---|
| **local（默认）** | **吃**——首仗走的就是它 | 进程内自有战士回环：`local.py` 把 channels 列表喂 llmpool，`python3 -m cli.warrior --channels /tmp/channels.json` 直达；多道=链式故障转移（400不转移/401-404硬熔/408-5xx软3次/429冷却60s，llmpool 全链） |
| dsh | 不吃 | adapter 起外部 harness CLI（dsh），用其**自身登录态**，钥匙不经我们的配置（F24a 编外肌肉，首仗不用） |
| claude | 不吃 | 同上，起 claude CLI，自身凭据 |

→ **首仗只需填 local 后端的钥匙**：OpenAI 兼容道（智谱 open.bigmodel.cn 形或其他兼容道，改 name/model/base_url 三件套+贴钥即可）。dsh/claude 后端零配置要求。

## 三、进位五步（贴钥动作本身）

```bash
cp docs/runbook/channels.template.json /tmp/channels.json   # 1 拷到仓外
#   2 编辑 /tmp/channels.json: 每个 "api_key" 占位符整串换真钥
chmod 600 /tmp/channels.json                                 # 3 收权限
python3 -c "import json;cs=json.load(open('/tmp/channels.json'));assert all(c.get('api_key') and 'YOUR_API_KEY_HERE' not in c['api_key'] for c in cs);print('OK channels=%d 道就绪'%len(cs))"   # 4 形状+占位符残留自检
#   5 (点火时) llmpool 真道健康: 第一发真实调用即验——见 first-battle-checklist.md 点火步
```

## 四、铁律（照 RUNBOOK 第三步原文精神）

1. **channels.json 永远放仓外**（/tmp 会被重启清空——每次点火前重验存在性）；真钥**永不入 git**（样例/模板件有测试钉占位符形状，填错会红）。
2. 钥匙一经贴入，账本/日志/简报里出现的永远是道 name，不是真钥（密值脱敏入账红线）。
3. 换道/加道：数组里加一项+priority 排序即可；llmpool 分类-熔断-冷却-切道全链自动接管。

## 五、点火后验活（不花大钱的验法）

- 战士起飞命令带 `--channels /tmp/channels.json` 后，首条 LLM 事件落 timeline（llmpool 故障转移事件入哈希链）——400/401 = 钥形或余额问题，逐道看事件行归因。
- `--dry-run` 不吃真钥（假道零调用），**不能**用来验钥；验钥只能真点火首发（或仓外手工 curl base_url 一发）。
