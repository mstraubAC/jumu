#!/usr/bin/env python3
"""
Advanced scraper using Selenium to capture actual API calls
This version renders the page with JavaScript and monitors network requests
"""

import json
import logging
from typing import Dict, List, Any, Optional
import time

# Optional: For advanced browser automation with network inspection
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

logger = logging.getLogger(__name__)


class SeleniumScraper:
    """Advanced scraper using Selenium to capture JavaScript-rendered content"""
    
    def __init__(self, url: str):
        """
        Initialize Selenium scraper
        
        Args:
            url: The page URL to scrape
        """
        if not SELENIUM_AVAILABLE:
            raise ImportError("Selenium not installed. Install with: pip install selenium")
        
        self.url = url
        self.driver = None
        self.collected_data = []
    
    def setup_driver(self):
        """Setup Chrome driver with preferences"""
        options = webdriver.ChromeOptions()
        # Uncomment for headless mode
        # options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # Enable network logging
        options.add_argument("--enable-logging")
        options.add_argument("--v=1")
        
        self.driver = webdriver.Chrome(options=options)
    
    def extract_window_data(self) -> List[Dict[str, Any]]:
        """Extract data from window object"""
        script = """
        return {
            keys: Object.keys(window),
            globalData: {
                // Common data variable patterns
                dataInjections: {},
            }
        }
        """
        
        try:
            result = self.driver.execute_script(script)
            return [{'source': 'window_object', 'data': result}]
        except Exception as e:
            logger.error(f"Error extracting window data: {e}")
            return []
    
    def extract_all_json(self) -> List[Dict[str, Any]]:
        """Extract all JSON data from the page"""
        collected = []
        
        # Get all script tags content
        scripts = self.driver.find_elements(By.TAG_NAME, "script")
        
        for idx, script in enumerate(scripts):
            try:
                text = script.get_attribute('innerHTML')
                if not text or len(text) < 5:
                    continue
                
                # Try to parse as JSON
                try:
                    data = json.loads(text)
                    collected.append({
                        'source': f'script_tag_{idx}',
                        'data': data
                    })
                except json.JSONDecodeError:
                    # Check for common JSON patterns
                    import re
                    
                    # Look for __NEXT_DATA__, __data, etc.
                    patterns = [
                        r'window\.__(\w+)\s*=\s*({.*?});',
                        r'var\s+(\w+)\s*=\s*({.*?});',
                    ]
                    
                    for pattern in patterns:
                        matches = re.finditer(pattern, text, re.DOTALL)
                        for match in matches:
                            try:
                                var_name = match.group(1)
                                json_str = match.group(2)
                                data = json.loads(json_str)
                                collected.append({
                                    'source': f'embedded_json_{var_name}',
                                    'data': data
                                })
                            except:
                                continue
            except Exception as e:
                logger.debug(f"Error processing script {idx}: {e}")
        
        return collected
    
    def scrape(self, wait_time: int = 5) -> List[Dict[str, Any]]:
        """
        Scrape the page
        
        Args:
            wait_time: Time to wait for JavaScript to load
            
        Returns:
            List of collected data
        """
        try:
            self.setup_driver()
            
            logger.info(f"Loading {self.url}")
            self.driver.get(self.url)
            
            # Wait for page to load
            logger.info(f"Waiting {wait_time} seconds for page load...")
            time.sleep(wait_time)
            
            # Extract data
            logger.info("Extracting data from window object...")
            window_data = self.extract_window_data()
            self.collected_data.extend(window_data)
            
            logger.info("Extracting JSON from script tags...")
            json_data = self.extract_all_json()
            self.collected_data.extend(json_data)
            
            # Try to find participant tables or lists
            logger.info("Searching for participant data elements...")
            try:
                # Common patterns for participant data
                tables = self.driver.find_elements(By.TAG_NAME, "table")
                logger.info(f"Found {len(tables)} tables")
                
                divs = self.driver.find_elements(By.CLASS_NAME, "participant")
                logger.info(f"Found {len(divs)} divs with 'participant' class")
            except:
                pass
            
            logger.info(f"Total data blocks collected: {len(self.collected_data)}")
            return self.collected_data
            
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            return self.collected_data
        finally:
            if self.driver:
                self.driver.quit()


def main():
    """Main execution for Selenium scraper"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    if not SELENIUM_AVAILABLE:
        print("Selenium is not installed.")
        print("Install with: pip install selenium")
        print("Also download ChromeDriver: https://chromedriver.chromium.org/")
        return 1
    
    url = "https://www.jugend-musiziert.org/wettbewerbe/regionalwettbewerbe/baden-wuerttemberg/esslingen-goeppingen-und-rems-murr/zeitplan"
    
    print("="*60)
    print("Jugend musiziert - Selenium Scraper")
    print("="*60)
    
    try:
        scraper = SeleniumScraper(url)
        data = scraper.scrape(wait_time=5)
        
        # Save collected data
        output_file = 'jugend_musiziert_selenium.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'url': url,
                'total_blocks': len(data),
                'data': data
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Data saved to {output_file}")
        print(f"✓ Collected {len(data)} data blocks")
        
        return 0
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
