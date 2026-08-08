# AgriSense AI - Infrastructure as Code
# Usage:
#   cd infrastructure
#   terraform init
#   terraform plan -var="hf_token=$HF_TOKEN" -var="github_token=$GH_TOKEN"
#   terraform apply -var="hf_token=$HF_TOKEN" -var="github_token=$GH_TOKEN"

module "agrisense_prod" {
  source = "./modules/agrisense"

  hf_username  = "SuperNitro"
  space_name   = "Agri-Sense"
  github_owner = "Uday-Kiran-01"
  github_repo  = "AgriSense"
  environment  = "prod"
  app_version  = "1.2.0"
  space_sdk    = "streamlit"

  # Pass via TF_VAR or CLI
  hf_token     = var.hf_token
  github_token = var.github_token
}
