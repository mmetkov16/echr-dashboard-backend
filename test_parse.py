#!/usr/bin/env python3
"""Test date parsing"""

from datetime import datetime

def test_parse():
    test_dates = [
        "11/03/1993 00:00:00",
        "15/02/1995 00:00:00",
        "04/02/1997 00:00:00",
        "",
        None,
    ]
    
    for date_str in test_dates:
        print(f"\nTesting: '{date_str}' (type: {type(date_str).__name__})")
        
        if not date_str:
            print("  -> Skipped (empty/None)")
            continue
        
        date_str = str(date_str).strip()
        
        # Try DD/MM/YYYY HH:MM:SS
        try:
            result = datetime.strptime(date_str, "%d/%m/%Y %H:%M:%S")
            print(f"  ✓ Parsed: {result}")
            print(f"    Year: {result.year}")
        except ValueError as e:
            print(f"  ✗ Error: {e}")

if __name__ == "__main__":
    test_parse()
