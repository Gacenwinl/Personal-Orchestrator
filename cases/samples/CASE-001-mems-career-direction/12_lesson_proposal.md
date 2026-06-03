---
case_id: CASE-001-mems-career-direction
lesson_id: LESSON-20260603-001
promote_to_lessons: true
promote_to_agents: false
promote_to_soul: false
one_off: false
---

# Lesson Proposal

## 失败/风险场景

- 关键词 rubric 导致「CAE/仿真」JD 假高分，未读职责即推荐匹配。

## 触发条件

- 批量 JD 匹配或法庭未读 JD 全文即给 fit 结论。

## 表现

- 岗位名含「仿真」但职责以嵌入式/软件为主。

## 根因

- 评审依赖关键词而非职责对齐；证据审计未强制抽样读 JD。

## 下次预防

- Phase1 后强制抽样 5 条「人工读 JD」写入 11；法庭 fit 矩阵须引用 jd_excerpt。

## Fallback

- 降权关键词分，引入「核心职责」人工标签字段。

## 沉淀决策

| 目标 | 是否写入 | 理由 |
|------|----------|------|
| lessons/approved/ | true | 可复现 |
| AGENTS.md | false | 待第二案验证 |
| SOUL.md | false | 已在 SOUL 有类似原则 |
| 仅本案归档 | false | |
