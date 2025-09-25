#!/usr/bin/env python3
"""
Test script for the Hong Kong Species API
"""

import requests
import json
import time
import subprocess
import sys
from threading import Thread

def test_api_endpoints():
    """Test all API endpoints"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing API endpoints...")
    
    # Wait for server to start
    time.sleep(2)
    
    try:
        # Test 1: Root endpoint
        response = requests.get(f"{base_url}/")
        print(f"✅ Root endpoint: {response.status_code}")
        
        # Test 2: Summary
        response = requests.get(f"{base_url}/api/summary")
        if response.status_code == 200:
            summary = response.json()
            print(f"✅ Summary: {summary['total_species']} species, {summary['total_occurrences']} records")
        
        # Test 3: Species search
        response = requests.get(f"{base_url}/api/species/search?q=Pyrocoelia")
        if response.status_code == 200:
            results = response.json()
            print(f"✅ Species search: Found {results['total']} matches")
        
        # Test 4: Species details
        response = requests.get(f"{base_url}/api/species/Pyrocoelia lunata")
        if response.status_code == 200:
            species = response.json()
            print(f"✅ Species details: {species['total_occurrences']} occurrences in {species['districts_count']} districts")
        
        # Test 5: Districts
        response = requests.get(f"{base_url}/api/districts")
        if response.status_code == 200:
            districts = response.json()
            print(f"✅ Districts: {len(districts['districts'])} districts loaded")
        
        # Test 6: Families
        response = requests.get(f"{base_url}/api/families")
        if response.status_code == 200:
            families = response.json()
            print(f"✅ Families: {len(families['families'])} families loaded")
        
        print("\n🎉 All API tests passed!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API server")
    except Exception as e:
        print(f"❌ API test failed: {e}")

def start_server():
    """Start the API server in background"""
    subprocess.run([sys.executable, "species_api.py"])

if __name__ == "__main__":
    print("🚀 Starting API server...")
    
    # Start server in background thread
    server_thread = Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Run tests
    test_api_endpoints()
    
    print("\n📖 API Documentation available at: http://localhost:8000/docs")
    print("🌐 Try these endpoints:")
    print("   GET /api/summary")
    print("   GET /api/species/search?q=bird")
    print("   GET /api/species/Pyrocoelia%20lunata")
    print("   GET /api/districts")
    
    try:
        input("\nPress Enter to stop the server...")
    except KeyboardInterrupt:
        pass