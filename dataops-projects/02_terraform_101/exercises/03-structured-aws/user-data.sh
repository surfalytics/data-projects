#!/bin/bash
# User data script for EC2 instance
# This script runs on first boot

# Update system
yum update -y

# Install Apache web server
yum install -y httpd

# Install AWS CLI v2 (if not already installed)
if ! command -v aws &> /dev/null; then
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    ./aws/install
    rm -rf aws awscliv2.zip
fi

# Start and enable Apache
systemctl start httpd
systemctl enable httpd

# Create a simple web page
cat > /var/www/html/index.html <<'HTML'
<!DOCTYPE html>
<html>
<head>
    <title>Terraform Demo</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        h1 { color: #FF9900; }
        .info {
            background-color: #f9f9f9;
            padding: 15px;
            border-left: 4px solid #FF9900;
            margin: 20px 0;
        }
        .success {
            color: #28a745;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Hello from Terraform!</h1>
        <p class="success">✓ This server was deployed using Terraform</p>

        <div class="info">
            <h3>Instance Information:</h3>
            <p><strong>Environment:</strong> ${environment}</p>
            <p><strong>Project:</strong> ${project_name}</p>
            <p><strong>Region:</strong> ${aws_region}</p>
            <p><strong>Instance ID:</strong> <span id="instance-id">Loading...</span></p>
            <p><strong>Availability Zone:</strong> <span id="az">Loading...</span></p>
        </div>

        <div class="info">
            <h3>What's Running:</h3>
            <ul>
                <li>Apache HTTP Server</li>
                <li>AWS CLI v2</li>
                <li>Amazon Linux 2</li>
            </ul>
        </div>

        <div class="info">
            <h3>IAM Role Permissions:</h3>
            <p>This instance has S3 access to: <strong>${bucket_name}</strong></p>
        </div>
    </div>

    <script>
        // Fetch instance metadata
        fetch('http://169.254.169.254/latest/meta-data/instance-id')
            .then(r => r.text())
            .then(d => document.getElementById('instance-id').textContent = d)
            .catch(() => document.getElementById('instance-id').textContent = 'Unable to fetch');

        fetch('http://169.254.169.254/latest/meta-data/placement/availability-zone')
            .then(r => r.text())
            .then(d => document.getElementById('az').textContent = d)
            .catch(() => document.getElementById('az').textContent = 'Unable to fetch');
    </script>
</body>
</html>
HTML

# Test S3 access
echo "Testing S3 access..." > /var/log/s3-test.log
aws s3 ls s3://${bucket_name}/ >> /var/log/s3-test.log 2>&1

# Create a test file and upload to S3
echo "Instance $(ec2-metadata --instance-id | cut -d ' ' -f 2) started at $(date)" > /tmp/startup.txt
aws s3 cp /tmp/startup.txt s3://${bucket_name}/logs/startup-$(date +%Y%m%d-%H%M%S).txt

# Log completion
echo "User data script completed at $(date)" >> /var/log/user-data.log
