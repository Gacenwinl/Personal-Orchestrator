# Case Frontmatter Schema

```yaml
case_id: string
status: string
case_type: career_direction | technical_route | automation_design | jd_match | ...
risk_tier: low | medium | high | critical

needs_execution: boolean
execution_authorized: boolean
authorized_phase: null | phase1 | phase2 | ...
human_approval_required: boolean

court_verdict_tier: null | REJECT | MODIFY | RECOMMENDED_WITH_MODIFICATIONS | RECOMMENDED | IMMEDIATELY_RECOMMENDED
cac_required: boolean
```

**Invariant:** `court_verdict_tier` 变更 **不自动** 修改 `execution_authorized`。
