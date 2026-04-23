#!/usr/bin/env python3
"""Inspect echr-extractor DataFrame structure"""

from echr_extractor import get_echr
import json

print("=" * 80)
print("Inspecting echr-extractor DataFrame")
print("=" * 80)

try:
    data = get_echr()
    print(f"\n✓ Retrieved data type: {type(data).__name__}")
    print(f"  Shape: {data.shape if hasattr(data, 'shape') else 'N/A'}")
    
    if hasattr(data, 'columns'):
        print(f"\nColumn Names ({len(data.columns)}):")
        for i, col in enumerate(data.columns):
            print(f"  {i+1}. {col}")
        
        print(f"\nFirst row (dict format):")
        first_row = data.iloc[0].to_dict()
        for key, val in first_row.items():
            val_str = str(val)[:100]
            print(f"  {key}: {val_str}")
        
        # Check for date columns
        print(f"\nLooking for date columns...")
        for col in data.columns:
            if 'date' in col.lower() or 'time' in col.lower():
                print(f"  Found: {col}")
                print(f"    Sample values: {data[col].head(3).tolist()}")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
