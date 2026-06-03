# Human Approval Gate

以下任一条件为真时，`human_approval_required` **必须为 true**，且 Owner 明确同意前不得 `execution_authorized: true`：

- `risk_tier` 为 `high` 或 `critical`
- 涉及登录、填表（即使不点提交）、账号、支付
- 涉及删除、覆盖、权限、密钥、暴露端口
- 涉及对外发送（消息、邮件、投递）
- `court_verdict_tier` 为 `IMMEDIATELY_RECOMMENDED` 且动作不可轻易回滚
- Orchestrator 在 `07` 中标记 `owner_decision_required: true`

Owner 批准后，Orchestrator 更新 frontmatter：

```yaml
execution_authorized: true
authorized_phase: phase1
human_approval_required: false   # 仅表示本 phase 已批；下一 phase 重新评估
```
