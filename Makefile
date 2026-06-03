.PHONY: smoke dashboard dashboards sop-console court-launch

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
