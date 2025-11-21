"""
Search Service Implementation
Supports Mock Google Search (free, simulated) and Real Google Custom Search API
"""

import os
import json
import time
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

import yaml

from .base import BaseSearchService


class MockGoogleSearchService(BaseSearchService):
    """Mock Google Search service with simulated results"""

    def __init__(self, config_path: str = "config/api_config.yaml"):
        """
        Initialize Mock Google Search service

        Args:
            config_path: Path to YAML configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self._setup_logging()

        # Get Mock Google Search configuration
        search_config = self.config.get('search_service', {})
        mock_config = search_config.get('mock_google_search', {})

        self.simulate_delay = mock_config.get('simulate_delay_seconds', 1)
        self.results_per_query = mock_config.get('results_per_query', 10)
        self.include_snippets = mock_config.get('include_snippets', True)

        # Settings
        settings = search_config.get('settings', {})
        self.retry_attempts = settings.get('retry_attempts', 3)
        self.timeout = settings.get('timeout_seconds', 10)
        self.cache_results = settings.get('cache_results', False)

    def _load_config(self) -> Dict:
        """Load configuration from YAML file"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config

    def _setup_logging(self):
        """Setup logging directory and file"""
        log_file = self.config.get('logging', {}).get('log_file', 'logs/api_call_log.jsonl')
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = log_file

    def _log(self, action: str, status: str, details: Dict[str, Any]):
        """Write log entry in JSONL format"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "module": "search_service",
            "provider": "MockGoogleSearch",
            "action": action,
            "status": status,
            "details": details
        }
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

    def search(self, query: str, num_results: int = 10,
              language: str = "en", region: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Perform a mock search query

        Args:
            query: Search query string
            num_results: Number of results to return
            language: Language code (e.g., "en", "zh")
            region: Region code for localized results (optional)

        Returns:
            List of search result dictionaries
        """
        self._log("search", "started", {
            "query": query,
            "num_results": num_results,
            "language": language,
            "region": region
        })

        try:
            # Simulate API delay
            time.sleep(self.simulate_delay)

            # Generate mock search results
            results = []
            actual_num_results = min(num_results, self.results_per_query)

            # Sample domains for variety
            domains = [
                "wikipedia.org", "github.com", "stackoverflow.com",
                "medium.com", "docs.python.org", "reddit.com",
                "youtube.com", "twitter.com", "news.ycombinator.com"
            ]

            for i in range(actual_num_results):
                domain = random.choice(domains)
                result = {
                    "title": f"Result {i+1}: {query} - {domain.split('.')[0].title()}",
                    "url": f"https://www.{domain}/search?q={query.replace(' ', '+')}&result={i+1}",
                    "display_url": f"{domain}",
                    "snippet": self._generate_snippet(query) if self.include_snippets else "",
                    "position": i + 1
                }
                results.append(result)

            self._log("search", "success", {
                "query": query,
                "results_count": len(results)
            })

            return results

        except Exception as e:
            self._log("search", "error", {
                "query": query,
                "error": str(e)
            })
            return []

    def _generate_snippet(self, query: str) -> str:
        """Generate a mock snippet based on query"""
        snippets = [
            f"Learn about {query} with comprehensive guides and tutorials...",
            f"Everything you need to know about {query}. Expert insights and analysis...",
            f"Discover {query} - detailed information, tips, and best practices...",
            f"A complete guide to {query}. Step-by-step instructions and examples...",
            f"Explore {query} in depth. Latest updates and trending topics...",
            f"Master {query} with our in-depth resources and community discussions...",
        ]
        return random.choice(snippets)

    def search_images(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search for mock images

        Args:
            query: Search query string
            num_results: Number of results to return

        Returns:
            List of image result dictionaries
        """
        self._log("search_images", "started", {
            "query": query,
            "num_results": num_results
        })

        try:
            # Simulate API delay
            time.sleep(self.simulate_delay)

            # Generate mock image results
            results = []
            actual_num_results = min(num_results, self.results_per_query)

            # Mock image dimensions
            dimensions = [
                (800, 600), (1024, 768), (1920, 1080),
                (640, 480), (1280, 720), (1600, 1200)
            ]

            for i in range(actual_num_results):
                width, height = random.choice(dimensions)
                result = {
                    "title": f"Image {i+1}: {query}",
                    "url": f"https://picsum.photos/id/{i+10}/{width}/{height}",
                    "thumbnail_url": f"https://picsum.photos/id/{i+10}/200/150",
                    "source_url": f"https://example.com/images/{query.replace(' ', '-')}-{i+1}",
                    "width": width,
                    "height": height,
                    "position": i + 1
                }
                results.append(result)

            self._log("search_images", "success", {
                "query": query,
                "results_count": len(results)
            })

            return results

        except Exception as e:
            self._log("search_images", "error", {
                "query": query,
                "error": str(e)
            })
            return []

    def search_news(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search for mock news articles

        Args:
            query: Search query string
            num_results: Number of results to return

        Returns:
            List of news result dictionaries
        """
        self._log("search_news", "started", {
            "query": query,
            "num_results": num_results
        })

        try:
            # Simulate API delay
            time.sleep(self.simulate_delay)

            # Generate mock news results
            results = []
            actual_num_results = min(num_results, self.results_per_query)

            news_sources = [
                "TechCrunch", "BBC News", "CNN", "Reuters",
                "The Verge", "Ars Technica", "Wired", "Bloomberg"
            ]

            for i in range(actual_num_results):
                source = random.choice(news_sources)
                result = {
                    "title": f"{query}: Latest Updates and Analysis",
                    "url": f"https://news.example.com/article/{query.replace(' ', '-').lower()}-{i+1}",
                    "source": source,
                    "published_date": datetime.now().isoformat(),
                    "snippet": f"Breaking news about {query}. {self._generate_snippet(query)}",
                    "thumbnail": f"https://picsum.photos/id/{i+20}/400/300",
                    "position": i + 1
                }
                results.append(result)

            self._log("search_news", "success", {
                "query": query,
                "results_count": len(results)
            })

            return results

        except Exception as e:
            self._log("search_news", "error", {
                "query": query,
                "error": str(e)
            })
            return []


class GoogleSearchService(BaseSearchService):
    """Real Google Custom Search API service"""

    def __init__(self, config_path: str = "config/api_config.yaml"):
        """
        Initialize Google Custom Search API service

        Args:
            config_path: Path to YAML configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self._setup_logging()

        # Get Google Search configuration
        search_config = self.config.get('search_service', {})
        google_config = search_config.get('google_search', {})

        self.api_key = self._resolve_env_var(google_config.get('api_key', ''))
        self.search_engine_id = self._resolve_env_var(google_config.get('search_engine_id', ''))

        if not self.api_key or not self.search_engine_id:
            raise ValueError("Google API Key and Search Engine ID are required. Check your .env file.")

        # Settings
        settings = search_config.get('settings', {})
        self.retry_attempts = settings.get('retry_attempts', 3)
        self.timeout = settings.get('timeout_seconds', 10)
        self.cache_results = settings.get('cache_results', False)

        # Import Google API client
        try:
            from googleapiclient.discovery import build
            self.build = build
        except ImportError:
            raise ImportError("google-api-python-client not installed. Run: pip install google-api-python-client")

    def _load_config(self) -> Dict:
        """Load configuration from YAML file"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config

    def _setup_logging(self):
        """Setup logging directory and file"""
        log_file = self.config.get('logging', {}).get('log_file', 'logs/api_call_log.jsonl')
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = log_file

    def _log(self, action: str, status: str, details: Dict[str, Any]):
        """Write log entry in JSONL format"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "module": "search_service",
            "provider": "GoogleSearch",
            "action": action,
            "status": status,
            "details": details
        }
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

    def _resolve_env_var(self, value: str) -> str:
        """Resolve environment variables in format ${ENV:VAR_NAME}"""
        if isinstance(value, str) and value.startswith('${ENV:') and value.endswith('}'):
            var_name = value[6:-1]
            return os.environ.get(var_name, '')
        return value

    def search(self, query: str, num_results: int = 10,
              language: str = "en", region: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Perform a real Google Custom Search query

        Args:
            query: Search query string
            num_results: Number of results to return (max 10 per request)
            language: Language code (e.g., "en", "zh")
            region: Region code for localized results (optional)

        Returns:
            List of search result dictionaries
        """
        self._log("search", "started", {
            "query": query,
            "num_results": num_results,
            "language": language,
            "region": region
        })

        try:
            # Build the service
            service = self.build("customsearch", "v1", developerKey=self.api_key)

            # Limit to 10 results per API request (Google's limit)
            num_results = min(num_results, 10)

            # Execute search
            result = service.cse().list(
                q=query,
                cx=self.search_engine_id,
                num=num_results,
                lr=f"lang_{language}" if language else None,
                gl=region if region else None
            ).execute()

            # Parse results
            search_results = []
            if 'items' in result:
                for idx, item in enumerate(result['items']):
                    # Extract thumbnail/image if available (from pagemap)
                    thumbnail_url = None
                    image_url = None

                    if 'pagemap' in item:
                        # Try to get thumbnail
                        if 'cse_thumbnail' in item['pagemap']:
                            thumbnails = item['pagemap']['cse_thumbnail']
                            if thumbnails and len(thumbnails) > 0:
                                thumbnail_url = thumbnails[0].get('src', '')

                        # Try to get full image
                        if 'cse_image' in item['pagemap']:
                            images = item['pagemap']['cse_image']
                            if images and len(images) > 0:
                                image_url = images[0].get('src', '')

                    # Extract additional metadata from pagemap
                    meta_description = ""
                    og_description = ""
                    og_image = ""

                    if 'pagemap' in item:
                        # Extract meta description
                        if 'metatags' in item['pagemap']:
                            metatags = item['pagemap']['metatags']
                            if metatags and len(metatags) > 0:
                                meta_description = metatags[0].get('og:description', '') or metatags[0].get('description', '')
                                og_image = metatags[0].get('og:image', '')

                        # Extract OpenGraph description
                        if 'webpage' in item['pagemap']:
                            webpages = item['pagemap']['webpage']
                            if webpages and len(webpages) > 0:
                                og_description = webpages[0].get('description', '')

                    search_result = {
                        "title": item.get('title', ''),
                        "url": item.get('link', ''),
                        "display_url": item.get('displayLink', ''),
                        "snippet": item.get('snippet', ''),
                        "html_snippet": item.get('htmlSnippet', ''),
                        "formatted_url": item.get('formattedUrl', ''),
                        "thumbnail_url": thumbnail_url,
                        "image_url": image_url,
                        "og_image": og_image,
                        "meta_description": meta_description,
                        "og_description": og_description,
                        "position": idx + 1
                    }
                    search_results.append(search_result)

            self._log("search", "success", {
                "query": query,
                "results_count": len(search_results)
            })

            return search_results

        except Exception as e:
            self._log("search", "error", {
                "query": query,
                "error": str(e)
            })
            return []

    def search_images(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search for images using Google Custom Search

        Args:
            query: Search query string
            num_results: Number of results to return

        Returns:
            List of image result dictionaries
        """
        self._log("search_images", "started", {
            "query": query,
            "num_results": num_results
        })

        try:
            service = self.build("customsearch", "v1", developerKey=self.api_key)
            num_results = min(num_results, 10)

            result = service.cse().list(
                q=query,
                cx=self.search_engine_id,
                num=num_results,
                searchType="image"
            ).execute()

            image_results = []
            if 'items' in result:
                for idx, item in enumerate(result['items']):
                    image_result = {
                        "title": item.get('title', ''),
                        "url": item.get('link', ''),
                        "thumbnail_url": item.get('image', {}).get('thumbnailLink', ''),
                        "source_url": item.get('image', {}).get('contextLink', ''),
                        "width": item.get('image', {}).get('width', 0),
                        "height": item.get('image', {}).get('height', 0),
                        "position": idx + 1
                    }
                    image_results.append(image_result)

            self._log("search_images", "success", {
                "query": query,
                "results_count": len(image_results)
            })

            return image_results

        except Exception as e:
            self._log("search_images", "error", {
                "query": query,
                "error": str(e)
            })
            return []

    def search_news(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search for news using Google Custom Search

        Args:
            query: Search query string
            num_results: Number of results to return

        Returns:
            List of news result dictionaries
        """
        # Google Custom Search doesn't have a dedicated news search type
        # Use regular search with news-related query modification
        news_query = f"{query} news"
        results = self.search(news_query, num_results)

        # Transform to news-like format
        news_results = []
        for result in results:
            news_result = {
                "title": result['title'],
                "url": result['url'],
                "source": result['display_url'],
                "published_date": datetime.now().isoformat(),  # API doesn't provide date
                "snippet": result['snippet'],
                "thumbnail": "",  # Would need additional API call
                "position": result['position']
            }
            news_results.append(news_result)

        return news_results


# Factory function to create search service based on config
def create_search_service(config_path: str = "config/api_config.yaml") -> BaseSearchService:
    """
    Factory function to create search service based on configuration

    Args:
        config_path: Path to configuration file

    Returns:
        Search service instance
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    provider = config.get('search_service', {}).get('provider', 'MockGoogleSearch')

    if provider == 'MockGoogleSearch':
        return MockGoogleSearchService(config_path)
    elif provider == 'GoogleSearch':
        return GoogleSearchService(config_path)
    else:
        raise ValueError(f"Unknown search service provider: {provider}")
