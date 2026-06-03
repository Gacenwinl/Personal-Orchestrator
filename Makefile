.PHONY: smoke dashboard dashboards sop-console hub court-launch \
        court-run workflow work-order hermes-setup hermes-doctor start fork

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

hub:
	bash scripts/open_hub.sh

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

CASE_TYPE ?= career_direction
RISK ?= high
SLUG ?= fork

start:
	@test -n "$(TOPIC)" || (echo "Usage: make start TOPIC='你的 topic'" && exit 1)
	python3 scripts/start_case.py "$(TOPIC)" --case-type $(CASE_TYPE) --risk-tier $(RISK)

fork:
	@test -n "$(FROM)" || (echo "Usage: make fork FROM=cases/active/CASE-xxx SLUG=fork" && exit 1)
	python3 scripts/fork_case.py "$(FROM)" --slug $(SLUG)

hermes-doctor:
	python3 scripts/hermes_doctor.py

hermes-setup:
	bash scripts/hermes_bootstrap.sh
	@echo "---"
	python3 scripts/hermes_doctor.py
