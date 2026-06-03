# Owner 旅程（日常只看本文 + Web Hub）

> 硬规则仍以 [HARNESS_ENGINE.md](../constraints/HARNESS_ENGINE.md) 为准。本文只回答：**我现在该点哪**。

**推荐入口：** `make hub` → 浏览器 `http://127.0.0.1:8765/`（见 [PHASE6_WEB_HUB.md](PHASE6_WEB_HUB.md)）。手机 QQ：`h cases` 等见 [integrations/qq_harness_bridge.md](../integrations/qq_harness_bridge.md)。

## 场景速查

| 你想做什么 | 怎么做 |
|------------|--------|
| **新 topic，新文件夹** | Hub 首页「新建案件」或 `make start` |
| **同一 topic 干净重来** | Hub「Fork」或 `make fork FROM=…` |
| **继续审理（补 md）** | Hub 打开案件 → **向导** Tab → 复制口令到 Cursor |
| **分析已结案（如 PhD 路径案）** | **下一步** Tab（默认）→ 点 outputs 链接 |
| **批准 Hermes 执行** | 看板授权闸门；QQ：`h authorize` → `confirm <token>` |
| **自动法庭** | 看板「检测 Hermes」→「派发 court-dispatch」 |
| **全自动六阶流** | 看板「workflow 单步」或终端 `make workflow` |

## 打开看板之后（分阶段）

### 立案 / 法庭中（lifecycle = 立案中 / 法庭进行中）

1. 默认 **向导** Tab：看「当前步」、复制 Cursor 口令。
2. 终端辅助：`suggest_teams` / `suggest_modes`（见向导 cli_hint）。
3. 改完 md 后：`make dashboard CASE=…` 并刷新浏览器。
4. 可选：`make sop-console` 用表单 PATCH status、追加 03 纪要。

### 分析结案（lifecycle = 分析结案）— 例：PhD 转美路径案

1. 默认 **下一步** Tab（不是向导）。
2. 按清单阅读 `outputs/us_phd_path_analysis.md` 等。
3. 补 `inputs/evidence_pack.md`。
4. **不要**在未批准时勾选授权或写可执行 `09`。

### 待授权执行

1. **下一步** Tab 会提示授权。
2. Owner 口头批准后：`make sop-console` → 授权闸门，或改 `07` 四字段。
3. `make work-order CASE=…` → `render_handoff` → 本机 Hermes。

## 命令只记 2 条（其余在 Hub 里点按钮）

```bash
make hub                          # 日常唯一入口
make hermes-setup                 # 首次 Phase 5 前一次
```

终端进阶：`make court-run`、`make workflow`、`make dashboard`（离线 html 备份）。

## 常见误区

| 误区 | 正确理解 |
|------|----------|
| index 里点旧案 = 重来 | 旧案仍在；重来请 `make fork` 或 `make start` **新目录** |
| 向导说 validate = 还要补 00–07 | 若阶段已是「分析结案」，请改看 **下一步** Tab |
| court-launch = 自动法庭 | launch 只生成手册；自动是 **court-run** |
| verdict = 可以执行 | 必须 `execution_authorized: true` 且 Owner 批准 |

## PhD 案示例路径

`cases/active/CASE-20260603-msc-us-phd-agent-pi-outreach`

```bash
make hub
# 列表中打开 PhD 案 → 默认「下一步」Tab
```

应看到 07 中的三条 Owner 行动项与 outputs 链接。
