#!/usr/bin/env python3
"""Validate a Personal-Orchestrator-Harness case directory.

This script is intentionally dependency-free. It checks the Markdown harness
invariants that should be mechanical before a case is marked completed.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any


VALID_STATUS = {
    "draft",
    "intake_complete",
    "court_in_progress",
    "court_complete",
    "cac_complete",
    "orchestrator_decided",
    "execution_pending",
    "no_execution_needed",
    "phase_planned",
    "instruction_issued",
    "execution_done",
    "acceptance_complete",
    "lesson_pending",
    "completed",
    "blocked",
    "in_progress",
}

VALID_RISK = {"low", "medium", "high", "critical"}

VALID_VERDICTS = {
    "REJECT",
    "MODIFY",
    "RECOMMENDED_WITH_MODIFICATIONS",
    "RECOMMENDED",
    "IMMEDIATELY_RECOMMENDED",
}

AUTH_FIELDS = {
    "needs_execution",
    "execution_authorized",
    "authorized_phase",
    "human_approval_required",
}

RECOMMENDED_PLUS = {
    "RECOMMENDED_WITH_MODIFICATIONS",
    "RECOMMENDED",
    "IMMEDIATELY_RECOMMENDED",
}


class CaseValidator:
    def __init__(self, case_dir: Path) -> None:
        self.case_dir = case_dir
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def path(self, rel: str) -> Path:
        return self.case_dir / rel

    def exists(self, rel: str) -> bool:
        return self.path(rel).is_file()

    def read_frontmatter(self, rel: str) -> dict[str, Any]:
        path = self.path(rel)
        if not path.is_file():
            self.error(f"missing required file: {rel}")
            return {}
        return parse_frontmatter(path)

    def validate(self) -> int:
        if not self.case_dir.is_dir():
            self.error(f"case directory does not exist: {self.case_dir}")
            return self.report()

        intake = self.read_frontmatter("01_case_intake.md")
        decision = self.read_frontmatter("07_orchestrator_decision.md")

        self.validate_intake(intake)
        self.validate_audit_chain(intake, decision)
        self.validate_team_blocks()
        self.validate_cac(intake)
        self.validate_authorization(intake, decision)
        self.validate_executor_files(intake, decision)

        return self.report()

    def validate_intake(self, intake: dict[str, Any]) -> None:
        required = {
            "case_id",
            "status",
            "case_type",
            "risk_tier",
            "needs_execution",
            "execution_authorized",
            "authorized_phase",
            "human_approval_required",
            "court_verdict_tier",
            "cac_required",
        }
        for key in sorted(required):
            if key not in intake:
                self.error(f"01_case_intake.md missing frontmatter field: {key}")

        status = intake.get("status")
        if status is not None and status not in VALID_STATUS:
            self.warn(f"01_case_intake.md has non-standard status: {status}")

        risk = intake.get("risk_tier")
        if risk is not None and risk not in VALID_RISK:
            self.error(f"01_case_intake.md invalid risk_tier: {risk}")

        verdict = intake.get("court_verdict_tier")
        if verdict is not None and verdict not in VALID_VERDICTS:
            self.error(f"01_case_intake.md invalid court_verdict_tier: {verdict}")

        for field in AUTH_FIELDS - {"authorized_phase"}:
            if field in intake and not isinstance(intake[field], bool):
                self.error(f"01_case_intake.md {field} must be boolean")

    def validate_audit_chain(self, intake: dict[str, Any], decision: dict[str, Any]) -> None:
        status = intake.get("status")
        always_required = [
            "00_owner_intent.md",
            "01_case_intake.md",
            "02_team_selection.md",
            "02b_mode_selection.md",
            "03_debate_session.md",
            "05_court_summary.md",
            "07_orchestrator_decision.md",
            "12_lesson_proposal.md",
        ]
        for rel in always_required:
            if not self.exists(rel):
                self.error(f"missing audit-chain file: {rel}")

        if status == "completed":
            if not self.exists("06_critical_assumption_check.md"):
                self.error("completed case must include 06_critical_assumption_check.md")

            needs_execution = bool_value(decision.get("needs_execution", intake.get("needs_execution")))
            authorized = bool_value(
                decision.get("execution_authorized", intake.get("execution_authorized"))
            )
            if needs_execution and authorized:
                for rel in [
                    "08_phase_plan.md",
                    "09_executor_instruction.md",
                    "10_execution_feedback.md",
                    "11_acceptance_review.md",
                ]:
                    if not self.exists(rel):
                        self.error(f"completed executed case missing: {rel}")
            elif needs_execution and not authorized:
                self.error(
                    "status completed is inconsistent with needs_execution:true "
                    "and execution_authorized:false"
                )

    def validate_team_blocks(self) -> None:
        team_dir = self.path("artifacts/team_blocks")
        if not team_dir.is_dir():
            self.error("missing team verdict block directory: artifacts/team_blocks/")
            return

        blocks = sorted(team_dir.glob("*.md"))
        if not blocks:
            self.error("no team verdict blocks found in artifacts/team_blocks/")
            return

        for block in blocks:
            fm = parse_frontmatter(block)
            rel = block.relative_to(self.case_dir)
            for key in ["case_id", "team_id", "team_verdict_tier", "confidence", "registry_ref"]:
                if key not in fm:
                    self.error(f"{rel} missing frontmatter field: {key}")
            verdict = fm.get("team_verdict_tier")
            if verdict is not None and verdict not in VALID_VERDICTS:
                self.error(f"{rel} invalid team_verdict_tier: {verdict}")

    def validate_cac(self, intake: dict[str, Any]) -> None:
        risk = intake.get("risk_tier")
        verdict = intake.get("court_verdict_tier")
        cac_required_by_rule = risk in {"high", "critical"} or verdict in RECOMMENDED_PLUS
        cac_required = bool_value(intake.get("cac_required"))

        if cac_required_by_rule and not cac_required:
            self.error(
                "CAC should be required when risk_tier is high/critical "
                "or court_verdict_tier is RECOMMENDED+"
            )
        if cac_required_by_rule and not self.exists("06_critical_assumption_check.md"):
            self.error("CAC is required but 06_critical_assumption_check.md is missing")

        critical_block = self.path("artifacts/team_blocks/critical_assumption.md")
        if cac_required_by_rule and not critical_block.is_file():
            self.error(
                "critical_assumption team block is required for high risk or RECOMMENDED+ cases"
            )

    def validate_authorization(
        self, intake: dict[str, Any], decision: dict[str, Any]
    ) -> None:
        for rel, fm in [("01_case_intake.md", intake), ("07_orchestrator_decision.md", decision)]:
            for field in AUTH_FIELDS:
                if field not in fm:
                    self.error(f"{rel} missing authorization field: {field}")
            for field in AUTH_FIELDS - {"authorized_phase"}:
                if field in fm and not isinstance(fm[field], bool):
                    self.error(f"{rel} {field} must be boolean")

        authorized = bool_value(decision.get("execution_authorized", intake.get("execution_authorized")))
        authorized_phase = decision.get("authorized_phase", intake.get("authorized_phase"))
        human_gate = bool_value(
            decision.get("human_approval_required", intake.get("human_approval_required"))
        )

        if authorized and (authorized_phase is None or authorized_phase == "null"):
            self.error("execution_authorized:true requires authorized_phase")
        if authorized and human_gate:
            self.error(
                "execution_authorized:true is inconsistent with human_approval_required:true"
            )

    def validate_executor_files(
        self, intake: dict[str, Any], decision: dict[str, Any]
    ) -> None:
        needs_execution = bool_value(decision.get("needs_execution", intake.get("needs_execution")))
        authorized = bool_value(decision.get("execution_authorized", intake.get("execution_authorized")))

        if not needs_execution:
            return
        if not authorized:
            if self.exists("09_executor_instruction.md"):
                self.warn(
                    "09_executor_instruction.md exists while execution_authorized is false; "
                    "ensure it is a draft only"
                )
            return

        instruction = self.read_frontmatter("09_executor_instruction.md")
        if instruction.get("execution_authorized") is not True:
            self.error("09_executor_instruction.md must set execution_authorized: true")

        phase = instruction.get("phase")
        authorized_phase = decision.get("authorized_phase", intake.get("authorized_phase"))
        if phase and authorized_phase and phase != authorized_phase:
            self.error(
                f"09_executor_instruction.md phase ({phase}) does not match "
                f"authorized_phase ({authorized_phase})"
            )

        text = self.path("09_executor_instruction.md").read_text(encoding="utf-8")
        for needle in ["禁止事项", "验收标准", "停止并回报条件"]:
            if needle not in text:
                self.error(f"09_executor_instruction.md missing section: {needle}")

    def report(self) -> int:
        rel = self.case_dir
        print(f"Validating case: {rel}")
        if self.warnings:
            print("\nWarnings:")
            for warning in self.warnings:
                print(f"  WARN: {warning}")
        if self.errors:
            print("\nErrors:")
            for error in self.errors:
                print(f"  ERROR: {error}")
            print(f"\nResult: FAIL ({len(self.errors)} errors, {len(self.warnings)} warnings)")
            return 1
        print(f"\nResult: PASS ({len(self.warnings)} warnings)")
        return 0


def parse_frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, flags=re.DOTALL)
    if not match:
        return {}
    data: dict[str, Any] = {}
    for raw_line in match.group(1).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = strip_inline_comment(value).strip()
        data[key] = parse_scalar(value)
    return data


def strip_inline_comment(value: str) -> str:
    in_quote: str | None = None
    for index, char in enumerate(value):
        if char in {"'", '"'}:
            if in_quote == char:
                in_quote = None
            elif in_quote is None:
                in_quote = char
        elif char == "#" and in_quote is None:
            return value[:index]
    return value


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value in {"", "null", "None", "~"}:
        return None
    if value == "true":
        return True
    if value == "false":
        return False
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [parse_scalar(part.strip()) for part in inner.split(",")]
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value


def bool_value(value: Any) -> bool:
    return value is True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a harness case directory.")
    parser.add_argument("case_dir", help="Path to cases/.../CASE-... directory")
    args = parser.parse_args(argv)
    return CaseValidator(Path(args.case_dir)).validate()


if __name__ == "__main__":
    raise SystemExit(main())
