output "bucket_name" {
  value = aws_s3_bucket.force_and_lock_logs[each.key].bucket
}