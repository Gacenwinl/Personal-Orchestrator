# Phase 5：自动化法庭 + 六阶工作流

在 Phase 4 交互 SOP 的基础上，Phase 5 通过 Hermes kanban swarm 实现法庭并行辩论真实执行，用 Python workflow daemon 驱动六阶自动流转。**Phase A→B 授权门仍为硬门控，不得绕过。**

## 系统架构（简图）

```
02_team_selection → court_dispatch.py
                         ↓
              hermes kanban swarm (orchestrator-court board)
                  ↓         ↓         ↓
           court-team   court-team  court-team    ← harness-court-team skill
           (team A)     (team B)    (team N)      ← calls MiMo API
                  ↓         ↓         ↓
           artifacts/team_blocks/*.md  ← written to case dir
                         ↓
              court-verify → court-synthesize
                         ↓
              05_court_summary.md
                         ↓
         [AUTH GATE: execution_authorized=true]
                         ↓
         workflow_daemon → build_work_order → hermes send
                         ↓
              10 → 11 → 12 → complete
```

## 六阶工作流

| 阶段 | 触发条件 | 产物 |
|------|----------|------|
| Stage 1 法庭触发 | 00+01+02+02b+03 就绪 | `artifacts/court_dispatch.json` |
| Stage 2 汇总等待 | team_blocks 全就绪 | `05_court_summary.md`（synthesizer 写） |
| **AUTH GATE** | court_done → 等待 Owner | `execution_authorized=true`（手动） |
| Stage 3 执行 | 授权后 | `artifacts/work_order.json` + Hermes send |
| Stage 4 反馈改进 | `10` 就绪 | 可选触发 meta_review |
| Stage 5 全局评估 | `11` 就绪 | `artifacts/stage5_eval.json` |
| Stage 6 改进 | P0 存在 | `artifacts/stage6_improvement_needed.md` |

## 快速开始

```bash
# 前提：make hermes-setup（创建 profiles + 安装 skill，只需运行一次）
make hermes-setup

# 对一个已有案件，启动全自动工作流
make workflow CASE=cases/active/CASE-xxx

# 或分步执行：
# 1. 仅派发法庭
make court-run CASE=cases/active/CASE-xxx

# 2. 查看 daemon 进度
tail -f cases/active/CASE-xxx/artifacts/daemon.log

# 3. Phase A→B 授权（看板操作或手动）
make sop-console   # → 浏览器 → 向导 Tab → 授权闸门

# 4. 生成工单（workflow daemon 自动调用，也可手动）
make work-order CASE=cases/active/CASE-xxx
```

## Hermes 初始化（首次使用）

```bash
make hermes-setup
```

输出的命令需要手工执行（`hermes profile create …` 和 `hermes skills install …`）。
需要 `XIAOMI_API_KEY` 已写入 `~/.openclaw/.env`。

## Makefile 目标

| 目标 | 说明 |
|------|------|
| `make court-run CASE=…` | 派发法庭 swarm + 启动 kanban daemon |
| `make workflow CASE=…` | 启动六阶 workflow daemon（持续轮询） |
| `make work-order CASE=…` | 单独生成 `artifacts/work_order.json` |
| `make hermes-setup` | 打印 profiles + skill 安装命令 |

## 关键约束（HARNESS_ENGINE §8 Phase 5 条款）

- court skill 和 synthesizer **不写** `execution_authorized` 字段
- `workflow_daemon` 在 AUTH GATE 处**只等待**，不自动授权
- Phase B 工单发送仅在 `execution_authorized=true` + `human_approval_required=false` 后执行
- 不自动创建 Hermes cron

## 回滚

停止 `workflow_daemon`（Ctrl-C）即可中断。删除 `artifacts/daemon_state.json` 可重置状态机到初始阶段。已写入的 `team_blocks/*.md` 有 `.bak` 备份，可手动恢复。

## 验收

```bash
make smoke
python3 scripts/court_dispatch.py cases/samples/CASE-001-mems-career-direction --check
python3 scripts/workflow_daemon.py --case cases/samples/CASE-001-mems-career-direction --check
python3 scripts/build_work_order.py cases/samples/CASE-001-mems-career-direction --check
```
