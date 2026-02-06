# Example Terraform configuration for demonstrating Berm policy checks

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

# Compliant S3 bucket with all security features enabled
resource "aws_s3_bucket" "compliant_bucket" {
  bucket = "my-compliant-bucket-example"

  tags = {
    Environment = "production"
    Compliance  = "enabled"
  }
}

resource "aws_s3_bucket_versioning" "compliant_versioning" {
  bucket = aws_s3_bucket.compliant_bucket.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "compliant_encryption" {
  bucket = aws_s3_bucket.compliant_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "compliant_access" {
  bucket = aws_s3_bucket.compliant_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Non-compliant S3 bucket (missing security features)
resource "aws_s3_bucket" "non_compliant_bucket" {
  bucket = "my-insecure-bucket-example"

  tags = {
    Environment = "development"
  }
}

# Versioning is disabled - VIOLATION
resource "aws_s3_bucket_versioning" "non_compliant_versioning" {
  bucket = aws_s3_bucket.non_compliant_bucket.id

  versioning_configuration {
    status = "Disabled"
  }
}

# Public access is not blocked - VIOLATION
resource "aws_s3_bucket_public_access_block" "non_compliant_access" {
  bucket = aws_s3_bucket.non_compliant_bucket.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

# Compliant RDS instance with encryption and adequate backup
resource "aws_db_instance" "compliant_database" {
  identifier           = "compliant-database"
  engine              = "postgres"
  engine_version      = "15.3"
  instance_class      = "db.t3.micro"
  allocated_storage   = 20
  storage_encrypted   = true

  username            = "admin"
  password            = "ChangeMeInProduction!"

  backup_retention_period = 7
  skip_final_snapshot     = true

  tags = {
    Environment = "production"
  }
}

# Non-compliant RDS instance - WARNING (low backup retention)
resource "aws_db_instance" "non_compliant_database" {
  identifier           = "insecure-database"
  engine              = "postgres"
  engine_version      = "15.3"
  instance_class      = "db.t3.micro"
  allocated_storage   = 20
  storage_encrypted   = false  # VIOLATION: Not encrypted

  username            = "admin"
  password            = "ChangeMeInProduction!"

  backup_retention_period = 3  # WARNING: Less than 7 days
  skip_final_snapshot     = true

  tags = {
    Environment = "development"
  }
}
