#!/usr/bin/env python3
"""
Basic Medical-Spytool Usage Example
Demonstrates simple author search and export
"""

import subprocess
import sys
from pathlib import Path

def run_medical_spytool(args):
    """Run Medical-Spytool with given arguments"""
    cmd = [sys.executable, "-m", "dnb_spytool"] + args
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("✅ Success!")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        print(e.stderr)
        return False

def main():
    """Main example function"""
    print("Medical-Spytool Basic Usage Examples")
    print("=" * 40)
    
    # Example 1: Simple author search
    print("\n1. Simple author search (validation only)")
    run_medical_spytool([
        "--author", "Johann Wolfgang von Goethe",
        "--max-results", "5",
        "--validate-only"
    ])
    
    # Example 2: Multiple authors with Excel export
    print("\n2. Multiple authors with Excel export")
    run_medical_spytool([
        "--authors", "Goethe,Schiller",
        "--format", "xlsx",
        "--output", "german_authors.xlsx",
        "--max-results", "10"
    ])
    
    # Example 3: PubMed search with analytics
    print("\n3. PubMed search with analytics")
    run_medical_spytool([
        "--author", "Einstein",
        "--database", "pubmed", 
        "--analytics",
        "--max-results", "20"
    ])
    
    print("\n✅ Examples completed!")
    print("Check the output files for results.")

if __name__ == "__main__":
    main()
