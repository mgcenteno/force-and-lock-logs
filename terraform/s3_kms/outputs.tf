output "bucket_name_primary" {
  value = aws_s3_bucket.force_and_lock_logs_primary.bucket
}

output "bucket_name_secondary" {
  value = aws_s3_bucket.force_and_lock_logs_secondary.bucket
}