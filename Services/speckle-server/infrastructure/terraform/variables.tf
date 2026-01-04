variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ca-central-1"
}

variable "cluster_name" {
  description = "Name of the EKS cluster"
  type        = string
  default     = "speckle-cluster"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "database_name" {
  description = "Name of the database"
  type        = string
  default     = "speckle"
}

variable "database_username" {
  description = "Database master username"
  type        = string
  default     = "speckle"
  sensitive   = true
}

variable "database_password" {
  description = "Database master password (you'll provide this)"
  type        = string
  sensitive   = true
}

variable "allowed_cidr_blocks" {
  description = "CIDR blocks allowed to access the cluster (for security groups)"
  type        = list(string)
  default     = ["0.0.0.0/0"]  # Change this later for security!
}