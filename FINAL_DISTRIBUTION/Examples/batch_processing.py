#!/usr/bin/env python3
"""
Batch Processing Example
Demonstrates how to process multiple authors efficiently
"""

import subprocess
import sys
import csv
from pathlib import Path
import time

def create_author_list():
    """Create a sample author list file"""
    authors = [
        "Johann Wolfgang von Goethe",
        "Friedrich Schiller", 
        "Heinrich Heine",
        "Thomas Mann",
        "Franz Kafka"
    ]
    
    authors_file = Path("sample_authors.txt")
    with open(authors_file, 'w', encoding='utf-8') as f:
        for author in authors:
            f.write(f"{author}\n")
    
    print(f"✅ Created author list: {authors_file}")
    return authors_file

def process_authors_individually(authors_file):
    """Process each author individually"""
    print("\n📚 Processing authors individually...")
    
    with open(authors_file, 'r', encoding='utf-8') as f:
        authors = [line.strip() for line in f if line.strip()]
    
    results_dir = Path("batch_results")
    results_dir.mkdir(exist_ok=True)
    
    for i, author in enumerate(authors, 1):
        print(f"\n{i}/{len(authors)}: Processing {author}")
        
        output_file = results_dir / f"{author.replace(' ', '_').replace(',', '')}.csv"
        
        cmd = [
            sys.executable, "-m", "dnb_spytool",
            "--author", author,
            "--max-results", "10",
            "--output", str(output_file),
            "--format", "csv"
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"  ✅ Results saved to {output_file}")
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Failed to process {author}: {e}")
        
        # Be nice to the servers
        time.sleep(2)
    
    print(f"\n✅ Batch processing completed. Results in {results_dir}/")

def process_authors_combined(authors_file):
    """Process all authors in a single search"""
    print("\n📚 Processing authors combined...")
    
    with open(authors_file, 'r', encoding='utf-8') as f:
        authors = [line.strip() for line in f if line.strip()]
    
    authors_string = ",".join(authors)
    output_file = "combined_authors_results.xlsx"
    
    cmd = [
        sys.executable, "-m", "dnb_spytool",
        "--authors", authors_string,
        "--max-results", "20",
        "--output", output_file,
        "--format", "xlsx",
        "--analytics"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"✅ Combined results saved to {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Combined processing failed: {e}")

def main():
    """Main batch processing example"""
    print("Medical-Spytool Batch Processing Example")
    print("=" * 45)
    
    # Create sample author list
    authors_file = create_author_list()
    
    # Method 1: Individual processing
    process_authors_individually(authors_file)
    
    # Method 2: Combined processing
    process_authors_combined(authors_file)
    
    print("\n🎉 Batch processing examples completed!")
    print("\nTips:")
    print("- Individual processing: Better for detailed analysis per author")
    print("- Combined processing: Faster, good for overview analysis")
    print("- Always include delays between requests to be respectful to servers")

if __name__ == "__main__":
    main()
