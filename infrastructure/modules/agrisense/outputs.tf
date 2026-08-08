output "hf_space_url" {
  description = "HF Space URL for the deployed application"
  value       = "https://huggingface.co/spaces/${var.hf_username}/${var.space_name}"
}

output "live_app_url" {
  description = "Live application URL"
  value       = "https://${lower(var.hf_username)}-${lower(replace(var.space_name, "-", "-"))}.hf.space"
}

output "github_actions_url" {
  description = "GitHub Actions workflow URL"
  value       = "https://github.com/${var.github_owner}/${var.github_repo}/actions"
}

output "environment" {
  description = "Current deployment environment"
  value       = var.environment
}

output "deployment_manifest" {
  description = "Path to generated deployment manifest"
  value       = local_file.deployment_manifest.filename
}
