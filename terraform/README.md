# GamePulse Terraform Infrastructure

This directory contains the Terraform configuration files to provision the AWS infrastructure required to run GamePulse.

## Architecture

- **VPC & Public Subnet**: A dedicated network environment.
- **Security Group**: Allows inbound traffic on ports 22 (SSH), 8000 (FastAPI), 3000 (Grafana), and 9090 (Prometheus).
- **EC2 Instance (t3.micro)**: A free-tier eligible instance running Amazon Linux 2023.
- **User Data**: A startup script that automatically installs Docker, clones the repository, and starts the full GamePulse stack via `docker compose`.

## Prerequisites

1. Install [Terraform](https://developer.hashicorp.com/terraform/downloads).
2. Install the [AWS CLI](https://aws.amazon.com/cli/) and configure it with your credentials (`aws configure`).
3. Have an existing AWS EC2 Key Pair to use for SSH access.

## Quick Start

### 1. Configuration
First, copy the example variables file:
```bash
cp terraform.tfvars.example terraform.tfvars
```
Edit `terraform.tfvars` and set your `key_pair_name` to match an existing key pair in your AWS account.

### 2. Initialize
Initialize the Terraform working directory. This downloads the AWS provider.
```bash
terraform init
```

### 3. Plan
Review the resources that Terraform will create:
```bash
terraform plan
```

### 4. Apply
Provision the infrastructure:
```bash
terraform apply
```
Type `yes` when prompted. Wait a few minutes for the EC2 instance to boot and execute the user data script.

### 5. Access
Once complete, Terraform will output the `public_ip` and `public_dns`.
- **API**: `http://<public_ip>:8000`
- **Grafana**: `http://<public_ip>:3000` (admin/admin)
- **Prometheus**: `http://<public_ip>:9090`

*Note: It may take 3-5 minutes for the user data script to finish installing Docker and starting the containers.*

## Teardown

To destroy the infrastructure and stop incurring charges:
```bash
terraform destroy
```
Type `yes` when prompted.
