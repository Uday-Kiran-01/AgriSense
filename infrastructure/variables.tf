variable "hf_token" {
  description = "HuggingFace API token"
  type        = string
  sensitive   = true
}

variable "github_token" {
  description = "GitHub personal access token"
  type        = string
  sensitive   = true
}

terraform {
  backend "local" {
    path = "terraform.tfstate"
  }
}

output "space_url" {
  value = module.agrisense_prod.hf_space_url
}

output "live_url" {
  value = module.agrisense_prod.live_app_url
}

output "actions_url" {
  value = module.agrisense_prod.github_actions_url
}
