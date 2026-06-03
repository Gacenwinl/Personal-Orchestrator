# Cursor Handoff

| 场景 | Cursor 角色 |
|------|-------------|
| 跑案件审理 Session | Orchestrator |
| 改本 Harness 仓库 | Local Executor |
| 按 09 做外网/JD 收集（若授权） | 可作为 External Executor 的一种实现 |

外网执行仍须 `execution_authorized: true` 与 `human_approval_required` 闸门。
