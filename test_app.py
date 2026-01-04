#!/usr/bin/env python3
"""
Test script for the Bedrock Support Assistant
"""

import json
import threading
import time
import urllib.request
import urllib.error
import sys
from datetime import datetime

import app


def start_server():
    """Start the server in a thread"""
    app.run_server()


def test_health():
    """Test the health endpoint"""
    time.sleep(2)  # Give server time to start
    
    try:
        url = "http://localhost:8080/health"
        print(f"\nTesting: {url}")
        response = urllib.request.urlopen(url)
        data = json.loads(response.read().decode('utf-8'))
        
        print(f"Status Code: {response.status}")
        print(f"Response: {json.dumps(data, indent=2)}")
        
        if data.get("status") == "healthy":
            print("✅ PASS: Health check returned healthy status")
            return True
        else:
            print("❌ FAIL: Health check did not return healthy status")
            return False
            
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False


def test_ticket_analysis():
    """Test the ticket analysis endpoint"""
    try:
        url = "http://localhost:8080/"
        payload = {
            "ticket": "I cannot login to my account. I keep getting 'Invalid credentials' error even though I know my password is correct.",
            "ticket_id": "TICKET-001"
        }
        
        print(f"\nTesting: POST {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            url,
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        response = urllib.request.urlopen(req)
        result = json.loads(response.read().decode('utf-8'))
        
        print(f"Status Code: {response.status}")
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status == 200 and "analysis" in result:
            print("✅ PASS: Ticket analysis succeeded")
            return True
        else:
            print("❌ FAIL: Ticket analysis did not return expected response")
            return False
            
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Bedrock Support Assistant - Local Testing")
    print("=" * 60)
    
    # Start server in a background thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Run tests
    health_ok = test_health()
    ticket_ok = test_ticket_analysis()
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print(f"Health Check: {'PASS' if health_ok else 'FAIL'}")
    print(f"Ticket Analysis: {'PASS' if ticket_ok else 'FAIL'}")
    print("=" * 60)
    
    sys.exit(0 if (health_ok and ticket_ok) else 1)
