#!/usr/bin/env python3
"""
Bedrock Support Assistant - HTTP Server for Ticket Analysis
Analyzes support tickets using AWS Bedrock Claude 3 Sonnet
"""

import json
import logging
import sys
import os
import traceback
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs

import boto3
from botocore.exceptions import BotoCoreError, ClientError

# Configuration
REGION = "eu-west-2"
MODEL_ID = "amazon.nova-pro-v1:0"
MAX_TICKET_LENGTH = 5000
PORT = 8080

# Setup logging - Use Windows-compatible path
log_dir = os.path.expanduser("~/bedrock-app-logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "app.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Initialize Bedrock client
try:
    bedrock_client = boto3.client("bedrock-runtime", region_name=REGION)
    logger.info(f"Bedrock client initialized for region {REGION}")
except Exception as e:
    logger.error(f"Failed to initialize Bedrock client: {e}")
    bedrock_client = None

# Try to setup CloudWatch logging
try:
    import watchtower
    cloudwatch_handler = watchtower.CloudWatchLogHandler()
    logger.addHandler(cloudwatch_handler)
    logger.info("CloudWatch logging enabled")
except ImportError:
    logger.info("watchtower not installed, CloudWatch logging disabled")
except Exception as e:
    logger.warning(f"CloudWatch logging setup failed: {e}")


class SupportTicketHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler for Bedrock Support Assistant"""

    def send_cors_headers(self):
        """Add CORS headers to response"""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def send_json_response(self, status_code, data):
        """Send JSON response"""
        try:
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json")
            self.send_cors_headers()
            self.end_headers()
            response_body = json.dumps(data)
            self.wfile.write(response_body.encode("utf-8"))
        except Exception as e:
            logger.error(f"Error sending JSON response: {e}")
            logger.error(traceback.format_exc())

    def do_OPTIONS(self):
        """Handle CORS preflight"""
        try:
            self.send_response(200)
            self.send_cors_headers()
            self.end_headers()
        except Exception as e:
            logger.error(f"Error in do_OPTIONS: {e}")

    def do_GET(self):
        """Health check endpoint"""
        try:
            if self.path == "/health":
                # Simple health check - just verify the service is running
                logger.info("Health check requested")
                self.send_json_response(200, {
                    "status": "healthy",
                    "timestamp": datetime.utcnow().isoformat(),
                    "service": "bedrock-support-assistant",
                    "region": REGION,
                    "model": MODEL_ID
                })
            else:
                self.send_json_response(404, {"error": "Not found"})
        except Exception as e:
            logger.error(f"Error in do_GET: {e}")
            logger.error(traceback.format_exc())

    def do_POST(self):
        """Handle ticket analysis requests"""
        try:
            # Validate content type
            content_type = self.headers.get("Content-Type", "")
            if "application/json" not in content_type:
                self.send_json_response(400, {
                    "error": "Content-Type must be application/json"
                })
                return

            # Get content length
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length == 0:
                self.send_json_response(400, {
                    "error": "No content provided"
                })
                return

            if content_length > 10485760:  # 10MB limit
                self.send_json_response(413, {
                    "error": "Payload too large"
                })
                return

            # Read and parse JSON
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body.decode("utf-8"))
            except json.JSONDecodeError:
                self.send_json_response(400, {
                    "error": "Invalid JSON"
                })
                return

            # Validate ticket field
            ticket = data.get("ticket", "").strip()
            if not ticket:
                self.send_json_response(400, {
                    "error": "Missing or empty 'ticket' field"
                })
                return

            if len(ticket) > MAX_TICKET_LENGTH:
                self.send_json_response(400, {
                    "error": f"Ticket exceeds maximum length of {MAX_TICKET_LENGTH} characters"
                })
                return

            # Check if Bedrock client is available
            if not bedrock_client:
                self.send_json_response(503, {
                    "error": "Bedrock service unavailable"
                })
                return

            # Call Bedrock
            try:
                system_prompt = """You are a support ticket analyzer. Analyze the following support ticket and provide:
1. A brief summary (1-2 sentences)
2. Severity level (critical, high, medium, low)
3. Category (technical, billing, account, other)
4. Suggested response to send to the customer

Format your response as JSON with fields: summary, severity, category, suggested_response"""

                # Amazon Nova Pro format
                prompt = f"{system_prompt}\n\nSupport Ticket:\n{ticket}"

                response = bedrock_client.invoke_model(
                    modelId=MODEL_ID,
                    contentType="application/json",
                    accept="application/json",
                    body=json.dumps({
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"text": prompt}
                                ]
                            }
                        ],
                        "inferenceConfig": {
                            "max_new_tokens": 1024,
                            "temperature": 0.7
                        }
                    })
                )

                # Parse Bedrock response (Nova format)
                response_body = json.loads(response["body"].read().decode("utf-8"))
                assistant_message = response_body["output"]["message"]["content"][0]["text"]

                # Try to parse the response as JSON
                try:
                    analysis = json.loads(assistant_message)
                except json.JSONDecodeError:
                    # If not valid JSON, return raw text
                    analysis = {"analysis": assistant_message}

                self.send_json_response(200, {
                    "ticket_id": data.get("ticket_id", "N/A"),
                    "analysis": analysis
                })
                logger.info(f"Successfully analyzed ticket")

            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "")
                if "ThrottlingException" in error_code:
                    self.send_json_response(429, {
                        "error": "Service temporarily unavailable (throttled)"
                    })
                elif "AccessDeniedException" in error_code:
                    self.send_json_response(403, {
                        "error": "Access denied - check AWS credentials and permissions"
                    })
                else:
                    logger.error(f"Bedrock API error: {e}")
                    self.send_json_response(502, {
                        "error": "Bedrock service error"
                    })
            except BotoCoreError as e:
                logger.error(f"Boto3 error: {e}")
                self.send_json_response(502, {
                    "error": "AWS service error"
                })

        except Exception as e:
            logger.error(f"Unexpected error in do_POST: {e}")
            logger.error(traceback.format_exc())
            self.send_json_response(500, {
                "error": "Internal server error"
            })

    def log_message(self, format, *args):
        """Override to use logger instead of stderr"""
        try:
            logger.info(f"{self.client_address[0]} - {format % args}")
        except:
            pass


def run_server():
    """Start the HTTP server"""
    server_address = ("", PORT)
    httpd = HTTPServer(server_address, SupportTicketHandler)
    httpd.timeout = 30
    
    logger.info(f"Bedrock Support Assistant started on port {PORT}")
    logger.info(f"Endpoints: POST / (analyze ticket), GET /health")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
    except Exception as e:
        logger.error(f"Server error: {e}")
        logger.error(traceback.format_exc())
    finally:
        logger.info("Server shutting down...")
        httpd.server_close()
        sys.exit(0)


if __name__ == "__main__":
    run_server()
