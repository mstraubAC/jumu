#!/usr/bin/env python3
"""Quick test of scraper functionality"""
import sys
sys.path.insert(0, '/Users/marcel/projects/jumu')

from scraper import JugendMusiziertScraper

print("Testing scraper with API endpoints...")
print("=" * 60)

scraper = JugendMusiziertScraper("https://www.jugend-musiziert.org/wettbewerbe/regionalwettbewerbe/baden-wuerttemberg/esslingen-goeppingen-und-rems-murr/zeitplan")

# Test fetch seasons
print("\n1. Fetching seasons...")
seasons = scraper.fetch_seasons()
print(f"   Result: {type(seasons).__name__}")
if seasons:
    print(f"   Content sample: {str(seasons)[:200]}...")

# Test fetch timetable
print("\n2. Fetching timetable...")
timetable = scraper.fetch_timetable()
print(f"   Result: {type(timetable).__name__}")
if timetable:
    print(f"   Content sample: {str(timetable)[:200]}...")

print("\n" + "=" * 60)
print("Test complete!")
