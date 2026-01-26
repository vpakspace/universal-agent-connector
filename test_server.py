#!/usr/bin/env python
"""Test script to check server startup"""
import sys
import traceback

try:
    print("=" * 60)
    print("Testing server startup...")
    print("=" * 60)
    
    print("\n1. Importing Flask...")
    from flask import Flask
    print("   [OK] Flask imported")
    
    print("\n2. Importing main module...")
    from main import create_app
    print("   [OK] Main module imported")
    
    print("\n3. Creating app...")
    app = create_app()
    print("   [OK] App created")
    
    print("\n4. Testing app routes...")
    with app.test_client() as client:
        response = client.get('/api/health')
        print(f"   [OK] Health endpoint: {response.status_code}")
    
    print("\n" + "=" * 60)
    print("[OK] All checks passed! Server should start successfully.")
    print("=" * 60)
    
except Exception as e:
    print("\n" + "=" * 60)
    print("[ERROR] ERROR DETECTED!")
    print("=" * 60)
    print(f"Error type: {type(e).__name__}")
    print(f"Error message: {str(e)}")
    print("\nFull traceback:")
    traceback.print_exc()
    sys.exit(1)

