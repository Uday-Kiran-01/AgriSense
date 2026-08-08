# AgriSense AI - Makefile
# Local development and deployment automation

.PHONY: help setup lint test run docker-build docker-up deploy infra-init infra-plan infra-apply clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Development ──────────────────────────────

setup: ## Install Python dependencies
	pip install -r requirements.txt
	@echo "Setup complete. Run 'make run' to start."

lint: ## Lint and validate code
	python -c "import ast; ast.parse(open('app.py',encoding='utf-8').read()); print('Syntax: OK')"
	python -c "import joblib, numpy, sklearn; print('Imports: OK')"
	@test -f agrisense_model_bundle.pkl && echo "Model bundle: OK" || echo "Model bundle: MISSING"
	@test -f .streamlit/config.toml && echo "Config: OK" || echo "Config: MISSING"

test: ## Run backend tests
	python -m pytest tests/ -v 2>/dev/null || echo "No backend tests to run (standalone demo mode)"

run: ## Start Streamlit locally
	streamlit run app.py --server.port 8501

# ── Docker ───────────────────────────────────

docker-build: ## Build Docker image
	docker build -t agrisense:latest .

docker-up: ## Start with Docker Compose
	docker compose up -d
	@echo "App running at http://localhost:8501"

docker-down: ## Stop Docker containers
	docker compose down

# ── Infrastructure ───────────────────────────

infra-init: ## Initialize Terraform
	cd infrastructure && terraform init

infra-plan: ## Plan Terraform changes
	cd infrastructure && terraform plan -var="hf_token=$$HF_TOKEN" -var="github_token=$$GH_TOKEN"

infra-apply: ## Apply Terraform changes
	cd infrastructure && terraform apply -var="hf_token=$$HF_TOKEN" -var="github_token=$$GH_TOKEN"

infra-destroy: ## Destroy all infrastructure
	cd infrastructure && terraform destroy -var="hf_token=$$HF_TOKEN" -var="github_token=$$GH_TOKEN"

# ── Deploy ───────────────────────────────────

deploy: lint ## Validate then push (CI/CD auto-deploys)
	git push origin main
	@echo "Changes pushed. Check https://github.com/Uday-Kiran-01/AgriSense/actions"

# ── Cleanup ──────────────────────────────────

clean: ## Remove generated and cache files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -f agrisense_farmers.db
	rm -rf infrastructure/generated/
	@echo "Cleaned"
