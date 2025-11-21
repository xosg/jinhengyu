"""
Web Scraper Module
Supports static sites (requests) and dynamic sites (Selenium)
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

import yaml
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService


class WebScraper:
    """Web scraper supporting both static and dynamic sites"""

    def __init__(self, config_path: str = "config/collection_config.yaml"):
        """
        Initialize web scraper with configuration

        Args:
            config_path: Path to YAML configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.session = requests.Session()
        self.driver = None
        self._setup_logging()

    def _load_config(self) -> Dict:
        """Load configuration from YAML file"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config

    def _setup_logging(self):
        """Setup logging directory and file"""
        log_file = self.config.get('logging', {}).get('log_file', 'logs/collection_log.jsonl')
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = log_file

    def _log(self, action: str, status: str, details: Dict[str, Any]):
        """Write log entry in JSONL format"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "module": "web_scraper",
            "action": action,
            "status": status,
            "details": details
        }
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

    def scrape_static_sites(self) -> Dict[str, Any]:
        """
        Scrape all enabled static sites from config

        Returns:
            Dictionary with scraping results
        """
        static_sites = self.config.get('web_scraping', {}).get('static_sites', [])
        results = {"total_sites": 0, "successful": 0, "failed": 0, "details": []}

        for site_config in static_sites:
            if not site_config.get('enabled', True):
                continue

            results["total_sites"] += 1
            try:
                site_result = self.scrape_static_site(
                    url=site_config['url'],
                    name=site_config.get('name', 'Unknown'),
                    extract_elements=site_config.get('extract_elements', []),
                    output_dir=site_config.get('output_dir', 'collected_data/web/static')
                )
                results["successful"] += 1
                results["details"].append(site_result)
            except Exception as e:
                results["failed"] += 1
                self._log("scrape_static_site", "error", {
                    "site": site_config.get('name'),
                    "url": site_config['url'],
                    "error": str(e)
                })

        return results

    def scrape_static_site(self, url: str, name: str = "Unknown",
                          extract_elements: List[Dict] = None,
                          output_dir: str = "collected_data/web/static") -> Dict[str, Any]:
        """
        Scrape a static website using requests

        Args:
            url: Website URL
            name: Site name for logging
            extract_elements: List of elements to extract (CSS selectors)
            output_dir: Directory to save results

        Returns:
            Dictionary with scraping results
        """
        self._log("scrape_static_site", "started", {"url": url, "name": name})

        try:
            # Send GET request with proper headers to avoid blocking
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            response = self.session.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract elements
            extracted_data = {}
            if extract_elements:
                for element_config in extract_elements:
                    selector = element_config.get('selector')
                    element_type = element_config.get('type', 'text')

                    if element_type == 'list':
                        elements = soup.select(selector)
                        extracted_data[selector] = [elem.get_text(strip=True) for elem in elements]
                    elif element_type == 'table':
                        tables = soup.select(selector)
                        extracted_data[selector] = self._parse_tables(tables)
                    else:
                        element = soup.select_one(selector)
                        extracted_data[selector] = element.get_text(strip=True) if element else None

            # Extract main text content
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Get page title
            title = soup.title.string if soup.title else name

            # Extract text from main content areas (try multiple common selectors)
            main_content = None
            for selector in ['main', 'article', '[role="main"]', '#content', '.content', 'body']:
                main_content = soup.select_one(selector)
                if main_content:
                    break

            # Get text content
            if main_content:
                text_content = main_content.get_text(separator='\n\n', strip=True)
            else:
                text_content = soup.get_text(separator='\n\n', strip=True)

            # Clean up excessive whitespace
            lines = [line.strip() for line in text_content.split('\n') if line.strip()]
            text_content = '\n\n'.join(lines)

            # Save results
            output_path = self._save_static_results(url, name, soup, extracted_data, output_dir)

            result = {
                "name": name,
                "url": url,
                "title": title,
                "text": text_content,
                "status": "success",
                "output_path": str(output_path),
                "extracted_elements": len(extracted_data)
            }

            self._log("scrape_static_site", "success", result)
            return result

        except Exception as e:
            error_result = {
                "name": name,
                "url": url,
                "status": "error",
                "error": str(e)
            }
            self._log("scrape_static_site", "error", error_result)
            raise

    def _parse_tables(self, tables) -> List[List[str]]:
        """Parse HTML tables into 2D arrays"""
        parsed_tables = []
        for table in tables:
            rows = []
            for tr in table.find_all('tr'):
                cells = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
                rows.append(cells)
            parsed_tables.append(rows)
        return parsed_tables

    def _save_static_results(self, url: str, name: str, soup: BeautifulSoup,
                            extracted_data: Dict, output_dir: str) -> Path:
        """Save scraping results to files"""
        # Create output directory with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        site_dir = Path(output_dir) / f"{name.replace(' ', '_')}_{timestamp}"
        site_dir.mkdir(parents=True, exist_ok=True)

        # Save full HTML
        html_file = site_dir / "page.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(str(soup))

        # Save extracted data as JSON
        if extracted_data:
            json_file = site_dir / "extracted_data.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(extracted_data, f, indent=2, ensure_ascii=False)

        # Save metadata
        metadata = {
            "url": url,
            "name": name,
            "scraped_at": timestamp,
            "html_file": str(html_file.name),
            "json_file": "extracted_data.json" if extracted_data else None
        }
        metadata_file = site_dir / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

        return site_dir

    def scrape_with_selenium(self, url: str, wait_time: float = 3.0) -> Dict[str, Any]:
        """
        Scrape website using Selenium (better for JavaScript-heavy sites)

        Args:
            url: URL to scrape
            wait_time: Time to wait for page to load

        Returns:
            Dictionary with title and text content
        """
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager

        driver = None
        try:
            # Setup Chrome driver
            chrome_options = ChromeOptions()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)

            # Load page
            driver.get(url)

            # Wait for page to be ready
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            time.sleep(wait_time)

            # Get title
            title = driver.title

            # Get text content from body
            try:
                # Try to get main content first
                main_selectors = ['main', 'article', '[role="main"]', '#content', '.content']
                text_content = None

                for selector in main_selectors:
                    try:
                        element = driver.find_element(By.CSS_SELECTOR, selector)
                        text_content = element.text
                        if text_content and len(text_content) > 100:
                            break
                    except:
                        continue

                # Fallback to body
                if not text_content:
                    text_content = driver.find_element(By.TAG_NAME, 'body').text

                # Clean up text
                lines = [line.strip() for line in text_content.split('\n') if line.strip()]
                text_content = '\n\n'.join(lines)

            except Exception as e:
                text_content = ""

            return {
                "status": "success",
                "url": url,
                "title": title,
                "text": text_content
            }

        except Exception as e:
            return {
                "status": "error",
                "url": url,
                "error": str(e),
                "title": "",
                "text": ""
            }
        finally:
            if driver:
                driver.quit()

    def scrape_dynamic_sites(self) -> Dict[str, Any]:
        """
        Scrape all enabled dynamic sites from config

        Returns:
            Dictionary with scraping results
        """
        dynamic_sites = self.config.get('web_scraping', {}).get('dynamic_sites', [])
        results = {"total_sites": 0, "successful": 0, "failed": 0, "details": []}

        for site_config in dynamic_sites:
            if not site_config.get('enabled', True):
                continue

            results["total_sites"] += 1
            try:
                site_result = self.scrape_dynamic_site(site_config)
                results["successful"] += 1
                results["details"].append(site_result)
            except Exception as e:
                results["failed"] += 1
                self._log("scrape_dynamic_site", "error", {
                    "site": site_config.get('name'),
                    "url": site_config['url'],
                    "error": str(e)
                })
            finally:
                if self.driver:
                    self.driver.quit()
                    self.driver = None

        return results

    def scrape_dynamic_site(self, site_config: Dict) -> Dict[str, Any]:
        """
        Scrape a dynamic website using Selenium

        Args:
            site_config: Site configuration dictionary

        Returns:
            Dictionary with scraping results
        """
        name = site_config.get('name', 'Unknown')
        url = site_config['url']

        self._log("scrape_dynamic_site", "started", {"url": url, "name": name})

        try:
            # Initialize browser
            self._init_driver()

            # Navigate to URL
            self.driver.get(url)

            # Handle login if required
            if site_config.get('requires_login'):
                self._handle_login(site_config.get('login_config', {}))

            # Wait for page to load
            wait_element = site_config.get('wait_for_element')
            if wait_element:
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, wait_element))
                )

            # Extract data (with pagination if enabled)
            all_data = []
            page_count = 0
            pagination_config = site_config.get('pagination', {})
            max_pages = pagination_config.get('max_pages', 1) if pagination_config.get('enabled') else 1

            while page_count < max_pages:
                page_count += 1

                # Extract elements from current page
                extracted = self._extract_elements_selenium(
                    site_config.get('extract_elements', [])
                )
                all_data.append(extracted)

                # Try to go to next page
                if pagination_config.get('enabled') and page_count < max_pages:
                    next_button = pagination_config.get('next_button_selector')
                    if not self._click_next_page(next_button):
                        break  # No more pages
                    time.sleep(2)  # Wait for page to load
                else:
                    break

            # Save results
            output_dir = site_config.get('output_dir', 'collected_data/web/dynamic')
            output_path = self._save_dynamic_results(url, name, all_data, output_dir)

            result = {
                "name": name,
                "url": url,
                "status": "success",
                "pages_scraped": page_count,
                "output_path": str(output_path)
            }

            self._log("scrape_dynamic_site", "success", result)
            return result

        except Exception as e:
            error_result = {
                "name": name,
                "url": url,
                "status": "error",
                "error": str(e)
            }
            self._log("scrape_dynamic_site", "error", error_result)
            raise

    def _init_driver(self):
        """Initialize Selenium WebDriver"""
        browser_config = self.config.get('web_scraping', {}).get('browser', {})
        driver_type = browser_config.get('driver', 'chrome').lower()
        headless = browser_config.get('headless', True)

        if driver_type == 'chrome':
            options = ChromeOptions()
            if headless:
                options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            service = ChromeService(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
        else:  # firefox
            options = FirefoxOptions()
            if headless:
                options.add_argument('--headless')
            service = FirefoxService(GeckoDriverManager().install())
            self.driver = webdriver.Firefox(service=service, options=options)

    def _handle_login(self, login_config: Dict):
        """Handle login form submission"""
        if not login_config:
            return

        # Fill username
        username_field = self.driver.find_element(By.CSS_SELECTOR, login_config['username_field'])
        username_field.send_keys(self._resolve_env_var(login_config['username']))

        # Fill password
        password_field = self.driver.find_element(By.CSS_SELECTOR, login_config['password_field'])
        password_field.send_keys(self._resolve_env_var(login_config['password']))

        # Click submit
        submit_button = self.driver.find_element(By.CSS_SELECTOR, login_config['submit_button'])
        submit_button.click()

        time.sleep(3)  # Wait for login to complete

    def _resolve_env_var(self, value: str) -> str:
        """Resolve environment variables in format ${ENV:VAR_NAME}"""
        if isinstance(value, str) and value.startswith('${ENV:') and value.endswith('}'):
            var_name = value[6:-1]
            return os.environ.get(var_name, '')
        return value

    def _extract_elements_selenium(self, extract_elements: List[Dict]) -> Dict:
        """Extract elements using Selenium"""
        extracted = {}
        for element_config in extract_elements:
            selector = element_config.get('selector')
            element_type = element_config.get('type', 'text')

            try:
                if element_type == 'list':
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    extracted[selector] = [elem.text for elem in elements]
                else:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    extracted[selector] = element.text
            except NoSuchElementException:
                extracted[selector] = None

        return extracted

    def _click_next_page(self, next_button_selector: str) -> bool:
        """Click next page button, return False if button not found"""
        try:
            next_button = self.driver.find_element(By.CSS_SELECTOR, next_button_selector)
            next_button.click()
            return True
        except NoSuchElementException:
            return False

    def _save_dynamic_results(self, url: str, name: str, all_data: List[Dict],
                             output_dir: str) -> Path:
        """Save dynamic scraping results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        site_dir = Path(output_dir) / f"{name.replace(' ', '_')}_{timestamp}"
        site_dir.mkdir(parents=True, exist_ok=True)

        # Save all extracted data
        data_file = site_dir / "extracted_data.json"
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump({
                "url": url,
                "name": name,
                "pages": all_data,
                "total_pages": len(all_data)
            }, f, indent=2, ensure_ascii=False)

        # Take screenshot
        if self.driver:
            screenshot_file = site_dir / "screenshot.png"
            self.driver.save_screenshot(str(screenshot_file))

        return site_dir

    def capture_screenshot(self, url: str, output_path: str,
                          width: int = 1920, height: int = 1080,
                          full_page: bool = True) -> str:
        """
        Capture a screenshot of a website using Selenium

        Args:
            url: Website URL to capture
            output_path: Path to save screenshot (e.g., "screenshot.png")
            width: Browser width (default: 1920)
            height: Browser height (default: 1080)
            full_page: If True, capture full page; if False, capture viewport only

        Returns:
            Path to saved screenshot
        """
        self._log("capture_screenshot", "started", {"url": url, "output_path": output_path})

        try:
            # Initialize browser if not already done
            if not self.driver:
                self._init_driver()

            # Set window size
            self.driver.set_window_size(width, height)

            # Navigate to URL
            self.driver.get(url)

            # Wait for page to load completely
            # 1. Wait for document.readyState to be "complete"
            for _ in range(20):  # Wait up to 10 seconds
                ready_state = self.driver.execute_script("return document.readyState")
                if ready_state == "complete":
                    break
                time.sleep(0.5)

            # 2. Additional wait for JavaScript to execute and render
            time.sleep(3)  # Give dynamic content time to load

            # 3. Scroll to bottom and back to top to trigger lazy-loading
            try:
                # Scroll to bottom
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                # Scroll back to top
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(1)
            except Exception:
                pass  # If scroll fails, continue anyway

            # Create output directory if needed
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            if full_page:
                # Get full page dimensions (wait for final dimensions)
                time.sleep(0.5)
                total_width = self.driver.execute_script("return document.body.scrollWidth")
                total_height = self.driver.execute_script("return document.body.scrollHeight")

                # Resize window to capture full page
                self.driver.set_window_size(total_width, total_height)
                time.sleep(2)  # Wait for resize and content reflow

            # Take screenshot
            self.driver.save_screenshot(str(output_file))

            self._log("capture_screenshot", "success", {
                "url": url,
                "output_path": str(output_file),
                "size": f"{width}x{height}",
                "full_page": full_page
            })

            return str(output_file)

        except Exception as e:
            self._log("capture_screenshot", "error", {
                "url": url,
                "error": str(e)
            })
            raise

    def close(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
            self.driver = None
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
