#!/bin/bash
set -ex

# Update packages
dnf update -y

# Install Docker
dnf install -y docker git

# Start Docker service
systemctl enable docker
systemctl start docker
usermod -aG docker ec2-user

# Install Docker Compose Plugin
# For Amazon Linux 2023, docker-compose is available as a plugin
dnf install -y docker-compose-plugin

# Clone the repository
cd /home/ec2-user
sudo -u ec2-user git clone https://github.com/shritaetta/GameBackend.git GamePulse
cd GamePulse

# Start the application using Docker Compose
sudo -u ec2-user docker compose up --build -d
