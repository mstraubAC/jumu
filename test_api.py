#!/usr/bin/env python3
"""Test API endpoints"""
import requests
import json

print("Testing Jugend musiziert API endpoints...")
print("=" * 60)

# Test seasons endpoint
print("\n[1] Testing seasons endpoint...")
try:
    response = requests.get("https://api.jugend-musiziert.org/api/seasons", timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Got response with {len(data) if isinstance(data, list) else 'dict'} items")
        if isinstance(data, list) and data:
            print(f"  First season: {data[0]}")
    else:
        print(f"✗ Error: {response.status_code}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test timetable endpoint
print("\n[2] Testing timetable endpoint...")
try:
    response = requests.get("https://api.jugend-musiziert.org/api/timetable", timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Got response")
        if isinstance(data, dict):
            print(f"  Keys: {list(data.keys())[:5]}")
        elif isinstance(data, list):
            print(f"  Items: {len(data)}")
    else:
        print(f"✗ Error: {response.status_code}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test main page for build ID
print("\n[3] Testing build ID extraction...")
try:
    response = requests.get("https://www.jugend-musiziert.org/wettbewerbe/regionalwettbewerbe/baden-wuerttemberg/esslingen-goeppingen-und-rems-murr/zeitplan", timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        import re
        match = re.search(r'/_next/data/([a-zA-Z0-9]+)/', response.text)
        if match:
            build_id = match.group(1)
            print(f"✓ Found build ID: {build_id}")
        else:
            print("⚠ Could not find build ID in page")
except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "=" * 60)
print("API test complete")
