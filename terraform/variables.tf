variable "aws_region" {
  description = "The AWS region to deploy the infrastructure in."
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "The EC2 instance type."
  type        = string
  default     = "t3.micro"
}

variable "key_pair_name" {
  description = "The name of the existing AWS Key Pair to use for SSH access."
  type        = string
}
