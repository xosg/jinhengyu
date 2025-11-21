"""
Screenshot Service using Selenium WebDriver
Captures webpage screenshots after content is fully loaded
"""

import time
from pathlib import Path
from typing import Dict, Any, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager


class ScreenshotService:
    """Service for capturing webpage screenshots"""

    def __init__(self, headless: bool = True, window_size: tuple = (1920, 1080)):
        """
        Initialize screenshot service

        Args:
            headless: Run browser in headless mode
            window_size: Browser window size (width, height)
        """
        self.headless = headless
        self.window_size = window_size

    def _create_driver(self):
        """Create and configure Chrome WebDriver"""
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument('--headless')

        chrome_options.add_argument(f'--window-size={self.window_size[0]},{self.window_size[1]}')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

        # Use webdriver-manager to automatically download and manage ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        return driver

    def capture_screenshot(self,
                          url: str,
                          output_path: str,
                          wait_for_load: float = 3.0,
                          full_page: bool = False) -> Dict[str, Any]:
        """
        Capture screenshot of a webpage

        Args:
            url: URL to capture
            output_path: Path to save screenshot
            wait_for_load: Seconds to wait for page to load completely
            full_page: Capture full page height (not just viewport)

        Returns:
            Dictionary with capture result
        """
        driver = None

        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Create driver
            driver = self._create_driver()

            # Navigate to URL
            driver.get(url)

            # Wait for document.readyState to be complete
            WebDriverWait(driver, 15).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )

            # Wait for images to start loading
            time.sleep(2)

            # Scroll through page to trigger lazy-loaded images (even if not full_page)
            total_height = driver.execute_script("return document.body.scrollHeight")
            viewport_height = driver.execute_script("return window.innerHeight")

            # Scroll down progressively to load all lazy images
            for i in range(0, total_height, viewport_height // 2):
                driver.execute_script(f"window.scrollTo(0, {i});")
                time.sleep(0.5)

            # Scroll back to top
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(0.5)

            # Wait for all images to complete loading (with timeout handling)
            try:
                WebDriverWait(driver, 15).until(
                    lambda d: d.execute_script("""
                        var images = document.getElementsByTagName('img');
                        var loaded = 0;
                        var total = images.length;
                        for (var i = 0; i < total; i++) {
                            if (images[i].complete && images[i].naturalHeight > 0) {
                                loaded++;
                            }
                        }
                        // Consider loaded if 90% of images are ready
                        return total === 0 || (loaded / total) >= 0.9;
                    """)
                )
            except TimeoutException:
                # Some images may have failed to load, but continue anyway
                pass

            # Additional wait for animations and dynamic content
            time.sleep(wait_for_load)

            # Handle full page screenshots
            if full_page:
                total_height = driver.execute_script("return document.body.scrollHeight")
                viewport_height = driver.execute_script("return window.innerHeight")

                for i in range(0, total_height, viewport_height):
                    driver.execute_script(f"window.scrollTo(0, {i});")
                    time.sleep(0.5)

                # Scroll back to top
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(0.5)

                # Set window size to full page height
                driver.set_window_size(self.window_size[0], total_height)

            # Capture screenshot
            driver.save_screenshot(str(output_path))

            # Get page info
            page_title = driver.title
            final_url = driver.current_url

            return {
                "status": "success",
                "screenshot_path": str(output_path),
                "url": url,
                "final_url": final_url,
                "page_title": page_title,
                "file_size": output_path.stat().st_size
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "url": url
            }

        finally:
            if driver:
                driver.quit()

    def capture_multiple(self,
                        urls: list,
                        output_dir: str,
                        wait_for_load: float = 3.0) -> Dict[str, Any]:
        """
        Capture screenshots of multiple URLs

        Args:
            urls: List of URLs to capture
            output_dir: Directory to save screenshots
            wait_for_load: Seconds to wait for each page

        Returns:
            Dictionary with capture results
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        results = {
            "total": len(urls),
            "successful": 0,
            "failed": 0,
            "screenshots": []
        }

        for idx, url in enumerate(urls, 1):
            output_path = output_dir / f"screenshot_{idx}.png"

            result = self.capture_screenshot(
                url=url,
                output_path=str(output_path),
                wait_for_load=wait_for_load
            )

            if result["status"] == "success":
                results["successful"] += 1
            else:
                results["failed"] += 1

            results["screenshots"].append(result)

        results["status"] = "success" if results["failed"] == 0 else "partial"
        return results
