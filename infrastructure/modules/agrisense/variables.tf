variable "hf_token" {
  description = "HuggingFace API token with write access"
  type        = string
  sensitive   = true
}

variable "github_token" {
  description = "GitHub personal access token for Actions secrets"
  type        = string
  sensitive   = true
}

variable "hf_username" {
  description = "HuggingFace username or organization"
  type        = string
  default     = "SuperNitro"
}

variable "space_name" {
  description = "HuggingFace Space name"
  type        = string
  default     = "Agri-Sense"
}

variable "github_owner" {
  description = "GitHub repository owner"
  type        = string
  default     = "Uday-Kiran-01"
}

variable "github_repo" {
  description = "GitHub repository name"
  type        = string
  default     = "AgriSense"
}

variable "space_sdk" {
  description = "HF Space SDK (streamlit, gradio, docker)"
  type        = string
  default     = "streamlit"
}

variable "space_hardware" {
  description = "HF Space hardware tier"
  type        = string
  default     = "cpu-basic"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "prod"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod"
  }
}

variable "app_version" {
  description = "Application version tag"
  type        = string
  default     = "1.2.0"
}
