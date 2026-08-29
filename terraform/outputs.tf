output "public_ip" {
  description = "The public IP address of the GamePulse EC2 instance."
  value       = aws_instance.gamepulse_server.public_ip
}

output "public_dns" {
  description = "The public DNS name of the GamePulse EC2 instance."
  value       = aws_instance.gamepulse_server.public_dns
}
