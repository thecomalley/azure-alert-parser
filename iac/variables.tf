variable "subscription_id" {
  type        = string
  description = "The Azure subscription ID"
}

variable "workload" {
  type        = string
  description = "The name of the workload"
  default     = "alert-parser"
}

variable "environment" {
  type        = string
  description = "The environment to deploy to"
  default     = "dev"
}

variable "location" {
  type        = string
  description = "The region to deploy to"
  default     = "Australia East"
}

variable "tags" {
  type        = map(string)
  description = "Tags to apply to all resources"
  default     = {}
}