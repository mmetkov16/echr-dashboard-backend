#!/usr/bin/env python3
"""Test script to understand echr-extractor data format"""

from echr_extractor import get_echr, get_echr_extra
import json

print("=" * 80)
print("Testing echr-extractor data format")
print("=" * 80)

# Get sample data
print("\n1. Testing get_echr()...")
try:
    data = get_echr()
    print(f"✓ get_echr() returned: {type(data).__name__}")
    
    if isinstance(data, (list, tuple)):
        print(f"  - Length: {len(data)}")
        
        if len(data) > 0:
            first = data[0]
            print(f"  - First item type: {type(first).__name__}")
            
            if isinstance(first, dict):
                print(f"  - First item keys: {list(first.keys())}")
                print(f"  - First item (partial): {json.dumps(first, indent=2, default=str)[:500]}")
            else:
                print(f"  - First item value (first 300 chars): {str(first)[:300]}")
except Exception as e:
    print(f"✗ Error calling get_echr(): {e}")

print("\n" + "=" * 80)
