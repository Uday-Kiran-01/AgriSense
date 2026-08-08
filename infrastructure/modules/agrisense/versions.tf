terraform {
  required_version = ">= 1.5.0"
  required_providers {
    huggingface = {
      source  = "huggingface/huggingface"
      version = ">= 0.1.0"
    }
    github = {
      source  = "integrations/github"
      version = ">= 6.0.0"
    }
    local = {
      source  = "hashicorp/local"
      version = ">= 2.4.0"
    }
  }
}
