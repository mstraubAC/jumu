#!/usr/bin/env python3
"""
Example usage of the Jugend musiziert scraper
Shows how to use the scraper in your own code
"""

from scraper import JugendMusiziertScraper
from data_processor import DataProcessor
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_1_basic_scraping():
    """Example 1: Basic scraping and saving"""
    print("\n" + "="*60)
    print("Example 1: Basic Scraping")
    print("="*60)
    
    url = "https://www.jugend-musiziert.org/wettbewerbe/regionalwettbewerbe/baden-wuerttemberg/esslingen-goeppingen-und-rems-murr/zeitplan"
    
    # Create scraper
    scraper = JugendMusiziertScraper(url)
    
    # Extract schedule data
    schedule_data = scraper.scrape_schedule()
    
    print(f"\nCollected {len(schedule_data)} data blocks")
    print("\nSample data block sources:")
    for idx, block in enumerate(schedule_data[:3]):
        print(f"  {idx+1}. {block.get('source', 'unknown')}")
    
    # Save the data
    scraper.save_data([{
        'url': url,
        'data_blocks': schedule_data
    }], 'example_output_1.json')
    
    print("\nData saved to example_output_1.json")


def example_2_processing_data():
    """Example 2: Processing and analyzing saved data"""
    print("\n" + "="*60)
    print("Example 2: Processing Saved Data")
    print("="*60)
    
    try:
        processor = DataProcessor('example_output_1.json')
        
        # Print summary
        processor.print_summary()
        
        # Extract participants
        participants = processor.extract_participants()
        print(f"Extracted {len(participants)} participant records")
        
        # Export to CSV
        processor.export_to_csv(participants, 'example_participants.csv')
        
    except FileNotFoundError:
        print("Note: Run example_1_basic_scraping() first to generate data")


def example_3_custom_extraction():
    """Example 3: Custom data extraction and filtering"""
    print("\n" + "="*60)
    print("Example 3: Custom Extraction and Filtering")
    print("="*60)
    
    # Load raw data
    try:
        with open('example_output_1.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Custom processing
        print(f"\nTotal data blocks collected: {len(data)}")
        
        # Look for specific data patterns
        print("\nAnalyzing data structure:")
        for block in data[0].get('data_blocks', [])[:2]:
            block_data = block.get('data', {})
            print(f"\nData Block: {block.get('source')}")
            print(f"  Type: {type(block_data).__name__}")
            print(f"  Size: {len(str(block_data))} characters")
            
            if isinstance(block_data, dict):
                print(f"  Top-level keys: {list(block_data.keys())[:5]}")
                if len(block_data.keys()) > 5:
                    print(f"    ... and {len(block_data.keys())-5} more keys")
        
    except FileNotFoundError:
        print("Note: Run example_1_basic_scraping() first to generate data")


def example_4_batch_scraping():
    """Example 4: Scraping multiple URLs"""
    print("\n" + "="*60)
    print("Example 4: Batch Scraping (Template)")
    print("="*60)
    
    # Multiple tournament URLs (example template)
    tournament_urls = [
        "https://www.jugend-musiziert.org/wettbewerbe/regionalwettbewerbe/baden-wuerttemberg/esslingen-goeppingen-und-rems-murr/zeitplan",
        # Add more URLs here:
        # "https://www.jugend-musiziert.org/wettbewerbe/regionalwettbewerbe/...",
    ]
    
    all_results = []
    
    for idx, url in enumerate(tournament_urls, 1):
        print(f"\n[{idx}/{len(tournament_urls)}] Scraping {url.split('/')[-2]}...")
        
        try:
            scraper = JugendMusiziertScraper(url)
            data = scraper.scrape_schedule()
            
            all_results.append({
                'url': url,
                'status': 'success',
                'data_blocks': len(data)
            })
            
            print(f"  ✓ Collected {len(data)} data blocks")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            all_results.append({
                'url': url,
                'status': 'error',
                'error': str(e)
            })
    
    # Summary
    print(f"\n\nBatch Scraping Summary:")
    print(f"  Total URLs: {len(tournament_urls)}")
    print(f"  Successful: {sum(1 for r in all_results if r['status'] == 'success')}")
    print(f"  Failed: {sum(1 for r in all_results if r['status'] == 'error')}")


def example_5_continuous_monitoring():
    """Example 5: Template for continuous monitoring"""
    print("\n" + "="*60)
    print("Example 5: Continuous Monitoring (Template)")
    print("="*60 + "\n")
    
    template_code = '''#!/usr/bin/env python3
"""Template for continuous monitoring of tournament data"""

import json
import time
from datetime import datetime
from scraper import JugendMusiziertScraper

url = "https://www.jugend-musiziert.org/wettbewerbe/..."
check_interval = 3600  # Check every hour

last_data = None

while True:
    print(f"[{datetime.now()}] Checking for updates...")
    
    scraper = JugendMusiziertScraper(url)
    current_data = scraper.scrape_schedule()
    
    # Compare with previous data
    if last_data != current_data:
        print(f"✓ Data updated! {len(current_data)} blocks found")
        scraper.save_data([{'data': current_data}], f'data_{datetime.now().isoformat()}.json')
        last_data = current_data
    else:
        print("✓ No changes detected")
    
    print(f"Next check in {check_interval} seconds...")
    time.sleep(check_interval)
'''
    
    print("Example continuous monitoring script:\n")
    print(template_code)
    print("\nTo use this, save as 'monitor.py' and run: python monitor.py")


def main():
    """Run all examples"""
    import sys
    
    print("\n" + "="*60)
    print("Jugend musiziert Scraper - Usage Examples")
    print("="*60)
    
    examples = {
        '1': ('Basic Scraping', example_1_basic_scraping),
        '2': ('Process Data', example_2_processing_data),
        '3': ('Custom Extraction', example_3_custom_extraction),
        '4': ('Batch Scraping', example_4_batch_scraping),
        '5': ('Monitoring Template', example_5_continuous_monitoring),
    }
    
    print("\nAvailable Examples:")
    for key, (name, _) in examples.items():
        print(f"  {key}. {name}")
    print("  0. Run all examples")
    print("  q. Quit")
    
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        choice = input("\nChoose an example (0-5, q): ").strip().lower()
    
    if choice == 'q':
        print("Goodbye!")
        return
    
    if choice == '0':
        for key in sorted(examples.keys()):
            examples[key][1]()
    elif choice in examples:
        examples[choice][1]()
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
