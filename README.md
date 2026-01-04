# AI-powered Support Ticket Summariser & Classifier using AWS Bedrock

An intelligent support ticket analysis system powered by AWS Bedrock (Amazon Nova Pro model) that automatically summarizes, categorizes, and prioritizes customer support tickets.

##  Features

- **AI-Powered Analysis**: Uses Amazon Nova Pro model via AWS Bedrock for intelligent ticket analysis
- **Automatic Classification**: Categorizes tickets (technical, billing, account, etc.)
- **Severity Detection**: Identifies urgency levels (critical, high, medium, low)
- **Smart Summaries**: Generates concise ticket summaries
- **Suggested Responses**: Provides AI-generated customer response templates
- **RESTful API**: Simple HTTP endpoints for integration
- **CloudWatch Integration**: Application logging and monitoring
- **Auto-scaling Ready**: Systemd service with automatic restart

##  Prerequisites

- AWS Account with Bedrock access
- Python 3.9+ (Python 3.11 recommended)
- AWS CLI configured
- boto3, watchtower Python packages

##  Local Setup

1. **Clone the repository**
```bash
git clone git@github.com:JeevaByte/AI-powered-Support-Ticket-Summariser-Classifier-using-AWS-Bedrock.git
cd AI-powered-Support-Ticket-Summariser-Classifier-using-AWS-Bedrock
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure AWS credentials**
```bash
aws configure
# Enter your AWS Access Key, Secret Key, and set region to eu-west-2
```

4. **Run the application**
```bash
python app.py
```

5. **Test the endpoints**
```bash
# Health check
curl http://localhost:8080/health

# Analyze a ticket
curl -X POST http://localhost:8080/ \
  -H "Content-Type: application/json" \
  -d '{"ticket":"Cannot login to account","ticket_id":"TEST-001"}'
```

## ☁️ AWS Deployment

### Quick Deploy with CloudFormation

```bash
aws cloudformation create-stack \
  --stack-name bedrock-support-app \
  --template-body file://bedrock-ec2-standalone.yaml \
  --parameters ParameterKey=AllowedCIDR,ParameterValue=YOUR_IP/32 \
  --capabilities CAPABILITY_NAMED_IAM \
  --region eu-west-2
```

### Wait for deployment
```bash
aws cloudformation wait stack-create-complete \
  --stack-name bedrock-support-app \
  --region eu-west-2
```

### Get the public IP
```bash
aws cloudformation describe-stacks \
  --stack-name bedrock-support-app \
  --region eu-west-2 \
  --query "Stacks[0].Outputs[?OutputKey=='InstancePublicIP'].OutputValue" \
  --output text
```

## 📡 API Endpoints

### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-04T00:19:37.658411",
  "service": "bedrock-support-assistant",
  "region": "eu-west-2",
  "model": "amazon.nova-pro-v1:0"
}
```

### Analyze Ticket
```http
POST /
Content-Type: application/json

{
  "ticket": "Customer complaint text here",
  "ticket_id": "TICKET-123"
}
```

**Response:**
```json
{
  "ticket_id": "TICKET-123",
  "analysis": {
    "summary": "Brief summary of the issue",
    "severity": "high",
    "category": "technical",
    "suggested_response": "Recommended response to customer"
  }
}
```

##  Architecture

- **Compute**: AWS EC2 (t3.micro) running Amazon Linux 2023
- **AI Model**: Amazon Nova Pro via AWS Bedrock Runtime
- **Networking**: VPC with public subnet and Internet Gateway
- **Security**: Security groups with IP-based access control
- **IAM**: EC2 instance role with Bedrock and CloudWatch permissions
- **Monitoring**: CloudWatch Logs for application logging
- **Service Management**: Systemd for automatic restart and management

##  Security

- ✅ IAM role-based authentication (no hardcoded credentials)
- ✅ Security group restricts access to specific IP addresses
- ✅ HTTPS recommended for production (not included in POC)
- ✅ No sensitive data stored in logs
- ✅ Credentials excluded from Git via .gitignore

##  Testing

Run the included test script:
```bash
python test_app.py
```

This will test:
- Health endpoint availability
- Bedrock model connectivity
- Ticket analysis functionality

##  AWS Resources Created

- VPC (10.0.0.0/16)
- Public Subnet
- Internet Gateway
- Route Tables
- Security Group (Port 8080)
- EC2 Instance (t3.micro)
- IAM Role and Instance Profile
- CloudWatch Log Groups

##  Cost Estimation

- **EC2 t3.micro**: ~$0.0104/hour (~$7.50/month)
- **Bedrock Nova Pro**: Pay per token (varies by usage)
- **Data Transfer**: First 1GB free, then $0.09/GB
- **CloudWatch Logs**: First 5GB free

**Estimated monthly cost**: $10-20 for light usage

## Cleanup

Delete the CloudFormation stack to remove all resources:
```bash
aws cloudformation delete-stack \
  --stack-name bedrock-support-app \
  --region eu-west-2
```

##  Configuration

Key configuration variables in `app.py`:
- `REGION`: AWS region (default: eu-west-2)
- `MODEL_ID`: Bedrock model (default: amazon.nova-pro-v1:0)
- `PORT`: HTTP port (default: 8080)
- `MAX_TICKET_LENGTH`: Maximum ticket size (default: 5000 chars)

##  Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

##  License

MIT License - see LICENSE file for details

##  Author

**JeevaByte**
- GitHub: [@JeevaByte](https://github.com/JeevaByte)

##  Acknowledgments

- AWS Bedrock team for the Nova Pro model
- Amazon Linux team for the base AMI
- Community contributors

## 📚 Additional Resources

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Amazon Nova Models](https://aws.amazon.com/bedrock/nova/)
- [CloudFormation User Guide](https://docs.aws.amazon.com/cloudformation/)

---

**Note**: This is a proof-of-concept application. For production use, consider adding:
- HTTPS/TLS encryption
- Authentication/API keys
- Rate limiting
- Database for ticket storage
- Load balancing
- Auto-scaling groups
