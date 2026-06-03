.PHONY: smoke dashboard dashboards sop-console court-launch \
        court-run workflow work-order hermes-setup

smoke:
	python3 scripts/smoke_test.py

dashboard:
	@test -n "$(CASE)" || (echo "Usage: make dashboard CASE=cases/active/CASE-xxx" && exit 1)
	python3 scripts/render_case_dashboard.py "$(CASE)" --force

dashboards:
	python3 scripts/render_case_dashboard.py --index --force
	python3 scripts/render_case_dashboard.py cases/active/* cases/samples/* --force 2>/dev/null || true

sop-console:
	python3 scripts/case_sop_server.py

court-launch:
	@test -n "$(CASE)" || (echo "Usage: make court-launch CASE=cases/active/CASE-xxx" && exit 1)
	python3 scripts/court_launcher.py "$(CASE)" --force

# Phase 5 targets ──────────────────────────────────────────────────────────

court-run:
	@test -n "$(CASE)" || (echo "Usage: make court-run CASE=cases/active/CASE-xxx" && exit 1)
	python3 scripts/court_dispatch.py "$(CASE)"
	@echo "Starting Hermes kanban daemon (Ctrl-C to stop)..."
	hermes kanban daemon --interval 30 --verbose

workflow:
	@test -n "$(CASE)" || (echo "Usage: make workflow CASE=cases/active/CASE-xxx" && exit 1)
	python3 scripts/workflow_daemon.py --case "$(CASE)"

work-order:
	@test -n "$(CASE)" || (echo "Usage: make work-order CASE=cases/active/CASE-xxx" && exit 1)
	python3 scripts/build_work_order.py "$(CASE)"

hermes-setup:
	@echo "=== Hermes Phase 5 Setup ==="
	@echo "Run the following commands to create profiles and install the skill:"
	@echo ""
	@echo "  hermes profile create court-team"
	@echo "  hermes profile create court-verify"
	@echo "  hermes profile create court-synthesize"
	@echo "  hermes skills install scripts/skills/harness-court-team --as court-team"
	@echo "  hermes skills install scripts/skills/harness-court-team --as court-verify"
	@echo "  hermes skills install scripts/skills/harness-court-team --as court-synthesize"
	@echo ""
	@echo "Ensure XIAOMI_API_KEY is set in ~/.openclaw/.env (shared with Hermes)."
