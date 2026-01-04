aws_region     = "ca-central-1"
cluster_name   = "speckle-cluster"
environment    = "production"
database_name  = "speckle"

# IMPORTANT: Set these to secure values!
database_username = "speckle"
database_password = "Sidian2025!"

# Security: Restrict this to your IP for better security
allowed_cidr_blocks = ["0.0.0.0/0"]