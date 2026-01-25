#!/usr/bin/env python3
"""
Utility script for processing and analyzing scraped data
Provides functions to parse, filter, and export participant data
"""

import json
import csv
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataProcessor:
    """Process and analyze scraped tournament data"""
    
    def __init__(self, json_file: str):
        """
        Initialize with a scraped data file
        
        Args:
            json_file: Path to the JSON file from scraper
        """
        self.json_file = json_file
        self.data = self._load_data()
    
    def _load_data(self) -> Dict[str, Any]:
        """Load JSON data from file"""
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"File not found: {self.json_file}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON: {e}")
            return {}
    
    def extract_participants(self) -> List[Dict[str, str]]:
        """
        Extract participant information from scraped data
        
        Returns:
            List of participant dictionaries
        """
        participants = []
        
        if not self.data:
            return participants
        
        # Parse embedded data blocks
        embedded_data = self.data.get('embedded_data', [])
        
        for block in embedded_data:
            data = block.get('data', {})
            
            # Different data structures might contain participants
            # Try common keys
            for key in ['participants', 'entries', 'schedule', 'data', 'items']:
                if key in data:
                    items = data[key]
                    if isinstance(items, list):
                        participants.extend(items)
                    elif isinstance(items, dict):
                        participants.extend(items.values() if isinstance(v := list(items.values()), list) else [])
        
        logger.info(f"Extracted {len(participants)} participant records")
        return participants
    
    def filter_by_category(self, participants: List[Dict], category: str) -> List[Dict]:
        """
        Filter participants by competition category
        
        Args:
            participants: List of participants
            category: Category name to filter
            
        Returns:
            Filtered list of participants
        """
        return [p for p in participants 
                if p.get('category') == category or p.get('Kategorie') == category]
    
    def filter_by_age_group(self, participants: List[Dict], age_group: str) -> List[Dict]:
        """
        Filter participants by age group
        
        Args:
            participants: List of participants
            age_group: Age group (e.g., 'Ia', 'II', 'VI')
            
        Returns:
            Filtered list of participants
        """
        return [p for p in participants 
                if p.get('age_group') == age_group or p.get('Altersgruppe') == age_group]
    
    def group_by_category(self, participants: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Group participants by category
        
        Args:
            participants: List of participants
            
        Returns:
            Dictionary with categories as keys and participant lists as values
        """
        grouped = {}
        
        for participant in participants:
            category = participant.get('category') or participant.get('Kategorie') or 'Unknown'
            
            if category not in grouped:
                grouped[category] = []
            
            grouped[category].append(participant)
        
        logger.info(f"Grouped into {len(grouped)} categories")
        return grouped
    
    def export_to_csv(self, participants: List[Dict], output_file: str):
        """
        Export participants to CSV file
        
        Args:
            participants: List of participants
            output_file: Output CSV file path
        """
        if not participants:
            logger.warning("No participants to export")
            return
        
        try:
            # Get all unique keys from all participants
            all_keys = set()
            for p in participants:
                all_keys.update(p.keys() if isinstance(p, dict) else [])
            
            fieldnames = sorted(list(all_keys))
            
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for participant in participants:
                    if isinstance(participant, dict):
                        writer.writerow({k: v for k, v in participant.items()})
            
            logger.info(f"Exported {len(participants)} participants to {output_file}")
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
    
    def print_summary(self):
        """Print a summary of the scraped data"""
        print("\n" + "="*60)
        print("DATA SUMMARY")
        print("="*60)
        
        print(f"\nURL: {self.data.get('url', 'N/A')}")
        
        endpoints = self.data.get('endpoints_discovered', [])
        print(f"API Endpoints Discovered: {len(endpoints)}")
        if endpoints:
            for ep in endpoints[:3]:
                print(f"  - {ep}")
            if len(endpoints) > 3:
                print(f"  ... and {len(endpoints) - 3} more")
        
        embedded = self.data.get('embedded_data', [])
        print(f"\nEmbedded Data Blocks: {len(embedded)}")
        
        for idx, block in enumerate(embedded[:3]):
            source = block.get('source', 'unknown')
            data = block.get('data', {})
            
            if isinstance(data, dict):
                print(f"\n  Block {idx+1}: {source}")
                print(f"    Keys: {list(data.keys())[:5]}")
                print(f"    Size: {len(str(data))} bytes")
        
        print("\n" + "="*60 + "\n")


def main():
    """Example usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Process scraped tournament data')
    parser.add_argument('input_file', help='Input JSON file from scraper')
    parser.add_argument('--csv', help='Export to CSV file', metavar='FILE')
    parser.add_argument('--summary', action='store_true', help='Print data summary')
    parser.add_argument('--category', help='Filter by category', metavar='NAME')
    parser.add_argument('--age-group', help='Filter by age group', metavar='GROUP')
    
    args = parser.parse_args()
    
    processor = DataProcessor(args.input_file)
    
    if args.summary:
        processor.print_summary()
    
    participants = processor.extract_participants()
    
    if args.category:
        participants = processor.filter_by_category(participants, args.category)
        print(f"Filtered to {len(participants)} participants in category '{args.category}'")
    
    if args.age_group:
        participants = processor.filter_by_age_group(participants, args.age_group)
        print(f"Filtered to {len(participants)} participants in age group '{args.age_group}'")
    
    if args.csv:
        processor.export_to_csv(participants, args.csv)
    
    if participants and not args.csv:
        print(f"\nFound {len(participants)} participants")
        # Print first 3 as preview
        for idx, p in enumerate(participants[:3]):
            print(f"\n[Participant {idx+1}]")
            for key, value in list(p.items())[:5]:
                print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
