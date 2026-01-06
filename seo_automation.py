"""
SEO Automation Tool
Automates Google searches and clicks on your website when found in search results.
"""

import asyncio
import time
import random
import re
import urllib.parse
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from typing import List, Dict
import json
import os
from pathlib import Path

# Configuration - Load from config.json if available, otherwise use defaults
CONFIG_FILE = "config.json"
GOOGLE_URL = "https://www.google.com"

def load_config():
    """Load configuration from config.json or use defaults."""
    defaults = {
        "keywords": [
            "大阪 salesforce 導入支援",
            "大阪 salesforce",
            "salesforce 大阪",
            "Salesforce導入支援",
            "Salesforce伴走支援"
        ],
        "target_url": "https://shinonome.llc/",
        "max_results_to_check": 10,
        "delay_between_searches": [5, 12],
        "delay_between_clicks": [3, 8],
        "headless": False,
        "use_persistent_context": True,
        "wait_for_captcha_manual": True,
        "skip_captcha": False,
        "captcha_service": None,
        "captcha_api_key": None
    }
    
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Merge with defaults
                for key in defaults:
                    if key not in config:
                        config[key] = defaults[key]
                return config
        except Exception as e:
            print(f"⚠️  Error loading config.json: {e}. Using defaults.")
            return defaults
    else:
        return defaults

CONFIG = load_config()
KEYWORDS = CONFIG["keywords"]
TARGET_URL = CONFIG["target_url"]
MAX_RESULTS_TO_CHECK = CONFIG["max_results_to_check"]
DELAY_BETWEEN_SEARCHES = tuple(CONFIG["delay_between_searches"])
DELAY_BETWEEN_CLICKS = tuple(CONFIG["delay_between_clicks"])
HEADLESS = CONFIG["headless"]
USE_PERSISTENT_CONTEXT = CONFIG.get("use_persistent_context", True)
WAIT_FOR_CAPTCHA_MANUAL = CONFIG.get("wait_for_captcha_manual", True)
SKIP_CAPTCHA = CONFIG.get("skip_captcha", False)
CAPTCHA_SERVICE = CONFIG.get("captcha_service", None)  # Options: "2captcha", "anticaptcha", None
CAPTCHA_API_KEY = CONFIG.get("captcha_api_key", None)


class SEOAutomation:
    def __init__(self, keywords: List[str], target_url: str):
        self.keywords = keywords
        self.target_url = target_url
        self.results = []
        self.user_data_dir = Path.home() / ".playwright_seo_browser"
        
    async def human_type(self, page, element, text: str):
        """Type text in a human-like manner with random delays."""
        await element.click()
        await asyncio.sleep(random.uniform(0.2, 0.5))
        
        for char in text:
            await element.type(char, delay=random.randint(50, 150))
            if random.random() < 0.1:  # 10% chance of small pause
                await asyncio.sleep(random.uniform(0.1, 0.3))
    
    async def random_mouse_movement(self, page):
        """Perform random mouse movements to appear more human-like."""
        try:
            viewport = page.viewport_size
            if viewport:
                for _ in range(random.randint(1, 3)):
                    x = random.randint(100, viewport['width'] - 100)
                    y = random.randint(100, viewport['height'] - 100)
                    await page.mouse.move(x, y)
                    await asyncio.sleep(random.uniform(0.1, 0.3))
        except:
            pass
    
    async def check_for_captcha(self, page) -> bool:
        """Check if CAPTCHA is present on the page."""
        captcha_selectors = [
            "iframe[src*='recaptcha']",
            "div[id*='recaptcha']",
            "div[class*='captcha']",
            "iframe[title*='reCAPTCHA']",
            "div:has-text('I'm not a robot')",
            "div:has-text('ロボットではありません')"
        ]
        
        for selector in captcha_selectors:
            try:
                elements = page.locator(selector)
                count = await elements.count()
                if count > 0:
                    return True
            except:
                continue
        
        # Check page content for CAPTCHA indicators
        try:
            content = await page.content()
            if 'recaptcha' in content.lower() or 'captcha' in content.lower():
                # Check if it's visible
                if await page.locator("iframe[src*='recaptcha']").count() > 0:
                    return True
        except:
            pass
        
        return False
    
    async def solve_captcha_automatically(self, page) -> bool:
        """Attempt to solve CAPTCHA automatically using a service."""
        if not CAPTCHA_SERVICE or not CAPTCHA_API_KEY:
            return False
        
        try:
            # Get the site key from the page
            site_key = None
            try:
                recaptcha_iframe = page.locator("iframe[src*='recaptcha']").first
                if await recaptcha_iframe.count() > 0:
                    src = await recaptcha_iframe.get_attribute("src")
                    if src and "k=" in src:
                        site_key = src.split("k=")[1].split("&")[0]
            except:
                pass
            
            if not site_key:
                # Try to get from page content
                try:
                    content = await page.content()
                    import re
                    match = re.search(r'data-sitekey="([^"]+)"', content)
                    if match:
                        site_key = match.group(1)
                except:
                    pass
            
            if not site_key:
                print("   ⚠️  Could not extract reCAPTCHA site key")
                return False
            
            print(f"   🔧 Attempting automatic CAPTCHA solve using {CAPTCHA_SERVICE}...")
            
            if CAPTCHA_SERVICE.lower() == "2captcha":
                return await self._solve_with_2captcha(page, site_key)
            elif CAPTCHA_SERVICE.lower() == "anticaptcha":
                return await self._solve_with_anticaptcha(page, site_key)
            else:
                print(f"   ⚠️  Unknown CAPTCHA service: {CAPTCHA_SERVICE}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error in automatic CAPTCHA solving: {e}")
            return False
    
    async def _solve_with_2captcha(self, page, site_key: str) -> bool:
        """Solve CAPTCHA using 2Captcha service."""
        try:
            import aiohttp
            
            # Submit CAPTCHA to 2Captcha
            page_url = page.url
            async with aiohttp.ClientSession() as session:
                # Submit task
                submit_url = "http://2captcha.com/in.php"
                async with session.post(submit_url, data={
                    "key": CAPTCHA_API_KEY,
                    "method": "userrecaptcha",
                    "googlekey": site_key,
                    "pageurl": page_url,
                    "json": 1
                }) as resp:
                    result = await resp.json()
                    if result.get("status") != 1:
                        print(f"   ❌ 2Captcha error: {result.get('request', 'Unknown error')}")
                        return False
                    
                    task_id = result.get("request")
                    print(f"   ⏳ CAPTCHA submitted, task ID: {task_id}")
                
                # Wait for solution (poll every 5 seconds, max 2 minutes)
                for _ in range(24):  # 24 * 5 = 120 seconds
                    await asyncio.sleep(5)
                    check_url = f"http://2captcha.com/res.php?key={CAPTCHA_API_KEY}&action=get&id={task_id}&json=1"
                    async with session.get(check_url) as resp:
                        result = await resp.json()
                        if result.get("status") == 1:
                            token = result.get("request")
                            print(f"   ✅ CAPTCHA solved! Injecting token...")
                            
                            # Inject the token using multiple methods
                            try:
                                # Method 1: Set the response textarea value
                                await page.evaluate(f"""
                                    (function() {{
                                        var responseElement = document.getElementById('g-recaptcha-response');
                                        if (responseElement) {{
                                            responseElement.innerHTML = '{token}';
                                            responseElement.value = '{token}';
                                        }}
                                        
                                        // Try to find all recaptcha response elements
                                        var allElements = document.querySelectorAll('[name="g-recaptcha-response"]');
                                        allElements.forEach(function(el) {{
                                            el.innerHTML = '{token}';
                                            el.value = '{token}';
                                        }});
                                        
                                        // Trigger callback if available
                                        if (typeof ___grecaptcha_cfg !== 'undefined' && ___grecaptcha_cfg.clients) {{
                                            for (var i = 0; i < ___grecaptcha_cfg.clients.length; i++) {{
                                                if (___grecaptcha_cfg.clients[i].callback) {{
                                                    ___grecaptcha_cfg.clients[i].callback('{token}');
                                                }}
                                            }}
                                        }}
                                        
                                        // Also try window callback
                                        if (typeof window.grecaptcha !== 'undefined') {{
                                            try {{
                                                window.grecaptcha.getResponse = function() {{ return '{token}'; }};
                                            }} catch(e) {{
                                                console.log('Error setting grecaptcha response');
                                            }}
                                        }}
                                    }})();
                                """)
                                
                                await asyncio.sleep(2)
                                
                                # Try to submit the form if there's a submit button
                                try:
                                    submit_button = page.locator("button[type='submit'], input[type='submit'], button:has-text('Submit'), button:has-text('送信')")
                                    if await submit_button.count() > 0:
                                        await submit_button.first.click()
                                        await asyncio.sleep(2)
                                except:
                                    pass
                                
                                return True
                            except Exception as e:
                                print(f"   ⚠️  Error injecting token: {e}")
                                return False
                        elif result.get("request") != "CAPCHA_NOT_READY":
                            print(f"   ❌ 2Captcha error: {result.get('request', 'Unknown error')}")
                            return False
                
                print(f"   ⏰ Timeout waiting for 2Captcha solution")
                return False
        except ImportError:
            print(f"   ⚠️  aiohttp not installed. Install it with: pip install aiohttp")
            return False
        except Exception as e:
            print(f"   ❌ Error with 2Captcha: {e}")
            return False
    
    async def _solve_with_anticaptcha(self, page, site_key: str) -> bool:
        """Solve CAPTCHA using AntiCaptcha service."""
        print(f"   ⚠️  AntiCaptcha integration not yet implemented")
        return False
    
    async def handle_captcha(self, page, keyword: str) -> bool:
        """Handle CAPTCHA - solve automatically, wait for manual solve, or skip."""
        if await self.check_for_captcha(page):
            print(f"\n⚠️  CAPTCHA detected for keyword: '{keyword}'")
            
            # Option 1: Try automatic solving FIRST (if configured)
            if CAPTCHA_SERVICE and CAPTCHA_API_KEY:
                print(f"🤖 Attempting automatic CAPTCHA solving using {CAPTCHA_SERVICE}...")
                solved = await self.solve_captcha_automatically(page)
                if solved:
                    # Wait a bit and check if CAPTCHA is gone
                    await asyncio.sleep(3)
                    if not await self.check_for_captcha(page):
                        print("✅ CAPTCHA solved automatically! Continuing...")
                        return True
                    else:
                        print("⚠️  CAPTCHA still present after automatic solve")
                        # Try clicking the submit button if it exists
                        try:
                            submit_btn = page.locator("button[type='submit'], button:has-text('Submit'), button:has-text('送信')")
                            if await submit_btn.count() > 0:
                                await submit_btn.first.click()
                                await asyncio.sleep(2)
                        except:
                            pass
            
            # Option 2: Skip CAPTCHA but continue searching (if skip_captcha enabled)
            if SKIP_CAPTCHA:
                print("⏭️  CAPTCHA detected but continuing anyway (skip_captcha enabled).")
                print("   Attempting to continue search despite CAPTCHA...")
                # Wait a bit and try to continue
                await asyncio.sleep(random.uniform(2, 4))
                # Try to refresh the page to see if we can proceed
                try:
                    await page.reload(wait_until="domcontentloaded")
                    await asyncio.sleep(random.uniform(1, 2))
                    # Check if CAPTCHA is still there
                    if await self.check_for_captcha(page):
                        print("   ⚠️  CAPTCHA still present, but continuing search anyway...")
                    else:
                        print("   ✅ CAPTCHA cleared after refresh!")
                except:
                    pass
                # Return True to continue despite CAPTCHA
                return True
            
            # Option 3: Wait for manual solve (unlimited time)
            if WAIT_FOR_CAPTCHA_MANUAL:
                print("⏸️  Waiting for you to solve CAPTCHA manually...")
                print("   Please solve the CAPTCHA in the browser window.")
                print("   The script will wait UNLIMITED time until you solve it.")
                print("   (Press Ctrl+C to cancel if needed)")
                
                # Wait indefinitely for CAPTCHA to be solved
                check_count = 0
                while True:
                    await asyncio.sleep(2)  # Check every 2 seconds
                    check_count += 1
                    
                    if not await self.check_for_captcha(page):
                        print("✅ CAPTCHA appears to be solved! Continuing...")
                        await asyncio.sleep(2)
                        return True
                    
                    # Print status every 30 seconds (15 checks * 2 seconds)
                    if check_count % 15 == 0:
                        elapsed_minutes = (check_count * 2) // 60
                        print(f"   ⏳ Still waiting for manual CAPTCHA solve... ({elapsed_minutes} minute(s) elapsed)")
            else:
                print("⏭️  Skipping this search due to CAPTCHA.")
                return False
        
        return True
        
    async def check_page_for_target(self, page, domain: str, page_num: int = 1) -> tuple:
        """Check current page for target URL. Returns (found, link_element, position, total_on_page)."""
        # Multiple strategies to find search results
        selectors = [
            f"a[href*='{domain}']",  # Direct href match
            f"a[data-ved][href*='{domain}']",  # Google's data-ved attribute
            f"div.g a[href*='{domain}']",  # Inside Google result divs
        ]
        
        search_results = None
        for selector in selectors:
            try:
                results = page.locator(selector)
                count = await results.count()
                if count > 0:
                    search_results = results
                    break
            except:
                continue
        
        if search_results is None:
            # Fallback: get all links and check manually
            all_links = page.locator("a[href]")
            link_count = await all_links.count()
            
            for i in range(min(link_count, MAX_RESULTS_TO_CHECK * 3)):
                try:
                    link = all_links.nth(i)
                    href = await link.get_attribute("href")
                    if href and domain in href:
                        return (True, link, i + 1, link_count)
                except:
                    continue
        else:
            result_count = await search_results.count()
            for i in range(min(result_count, MAX_RESULTS_TO_CHECK)):
                try:
                    result_link = search_results.nth(i)
                    href = await result_link.get_attribute("href")
                    if href and (self.target_url in href or domain in href):
                        return (True, result_link, i + 1, result_count)
                except:
                    continue
        
        return (False, None, None, 0)
    
    async def click_on_result(self, page, link, position: int, page_num: int, context=None) -> tuple:
        """Open the found result in a new tab, wait, then return to search tab. Returns (success, new_page)."""
        new_page = None
        try:
            print(f"✅ Found your site on page {page_num}, position {position}!")
            
            # Scroll to the result to ensure it's visible
            await link.scroll_into_view_if_needed()
            await asyncio.sleep(random.uniform(0.5, 1))
            
            # Get the URL from the link
            href = await link.get_attribute("href")
            if not href:
                # Try to get it via JavaScript
                href = await link.evaluate("element => element.href")
            
            # Clean up the URL (Google sometimes adds tracking parameters)
            if href:
                # Remove Google's tracking parameters
                if href.startswith('/url?q='):
                    parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                    if 'q' in parsed:
                        href = parsed['q'][0]
                elif href.startswith('/url?'):
                    parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                    if 'url' in parsed:
                        href = parsed['url'][0]
                
                # Ensure it's a full URL
                if href and not href.startswith('http'):
                    if href.startswith('//'):
                        href = 'https:' + href
                    elif href.startswith('/'):
                        href = 'https://www.google.com' + href
                    else:
                        href = 'https://' + href
            
            if not href:
                print(f"⚠️  Could not extract URL from link, trying click method...")
                # Fallback: try clicking with Ctrl+Click to open in new tab
                try:
                    await link.click(modifiers=['Control'], timeout=5000)
                    print(f"🖱️  Opened in new tab (Ctrl+Click)!")
                    await asyncio.sleep(random.uniform(1, 2))
                    # Switch back to original page
                    await page.bring_to_front()
                    return (True, None)
                except:
                    try:
                        # Try with Cmd on Mac or just regular click
                        await link.click(timeout=5000)
                        print(f"🖱️  Clicked on link!")
                        await asyncio.sleep(random.uniform(1, 2))
                        return (True, None)
                    except Exception as e:
                        print(f"❌ Error clicking: {e}")
                        return (False, None)
            else:
                # Open URL in a new tab
                if context:
                    new_page = await context.new_page()
                    print(f"🆕 Opening {href} in new tab...")
                    await new_page.goto(href, wait_until="domcontentloaded", timeout=15000)
                    print(f"✅ Opened your site in new tab!")
                    
                    # Wait on the new page
                    try:
                        await new_page.wait_for_load_state("networkidle", timeout=10000)
                    except:
                        # If networkidle times out, just wait for domcontentloaded
                        await new_page.wait_for_load_state("domcontentloaded", timeout=5000)
                    
                    wait_time = random.uniform(*DELAY_BETWEEN_CLICKS)
                    print(f"⏳ Waiting {wait_time:.1f} seconds on your site...")
                    await asyncio.sleep(wait_time)
                    
                    # Switch back to the search results page
                    await page.bring_to_front()
                    print(f"↩️  Returned to search results tab")
                    await asyncio.sleep(random.uniform(0.5, 1))
                    
                    # Keep the new tab open (don't close it)
                    # The search results page is now active again
                else:
                    # If context is not available, try opening with JavaScript
                    await page.evaluate(f"window.open('{href}', '_blank')")
                    print(f"🆕 Opened {href} in new tab (via JavaScript)!")
                    await asyncio.sleep(random.uniform(1, 2))
                    # Focus back on the original page
                    await page.bring_to_front()
                    print(f"↩️  Returned to search results tab")
            
            return (True, new_page)
        except PlaywrightTimeoutError:
            print(f"❌ Timeout while opening URL")
            return (False, new_page)
        except Exception as e:
            print(f"❌ Error opening URL: {e}")
            return (False, new_page)
    
    async def go_to_next_page(self, page) -> bool:
        """Navigate to next page of search results. Returns True if successful."""
        try:
            # Look for "Next" button or page number links
            next_selectors = [
                "a#pnnext",  # Google's next button ID
                "a[aria-label*='Next']",
                "a[aria-label*='次へ']",
                "a:has-text('Next')",
                "a:has-text('次へ')",
                "td[style*='text-align:left'] a",  # Next button in pagination
            ]
            
            for selector in next_selectors:
                try:
                    next_button = page.locator(selector)
                    count = await next_button.count()
                    if count > 0:
                        # Check if it's actually the next button (not disabled)
                        is_visible = await next_button.first.is_visible()
                        # Check if it's not disabled (Google sometimes disables the next button)
                        is_enabled = await next_button.first.is_enabled()
                        if is_visible and is_enabled:
                            # Get href to verify it's a valid next link
                            href = await next_button.first.get_attribute("href")
                            if href and ('start=' in href or 'page=' in href or href != '#'):
                                await next_button.first.scroll_into_view_if_needed()
                                await asyncio.sleep(random.uniform(0.5, 1))
                                await next_button.first.click()
                                await page.wait_for_load_state("domcontentloaded")
                                await asyncio.sleep(random.uniform(2, 4))
                                return True
                except:
                    continue
            
            # Alternative: try clicking on page numbers
            try:
                # Get current page number from URL or pagination
                current_url = page.url
                if 'start=' in current_url:
                    # Extract current start value
                    match = re.search(r'start=(\d+)', current_url)
                    if match:
                        current_start = int(match.group(1))
                        next_start = current_start + 10
                        # Try to find link with next start value
                        next_link = page.locator(f"a[href*='start={next_start}']")
                        if await next_link.count() > 0:
                            await next_link.first.scroll_into_view_if_needed()
                            await asyncio.sleep(random.uniform(0.5, 1))
                            await next_link.first.click()
                            await page.wait_for_load_state("domcontentloaded")
                            await asyncio.sleep(random.uniform(2, 4))
                            return True
            except:
                pass
            
            # Check if we're at the last page by looking for "no results" or similar indicators
            try:
                no_results = page.locator("text=did not match any documents, text=一致するドキュメントはありませんでした")
                if await no_results.count() > 0:
                    return False
            except:
                pass
            
            return False
        except Exception as e:
            print(f"⚠️  Error navigating to next page: {e}")
            return False
    
    async def search_and_click(self, page, keyword: str, context=None) -> Dict:
        """Search for a keyword and click on target URL if found on any page."""
        result = {
            "keyword": keyword,
            "found": False,
            "page": None,
            "position": None,
            "clicked": False,
            "error": None
        }
        
        try:
            print(f"\n🔍 Searching for: '{keyword}'")
            
            # Navigate to Google
            await page.goto(GOOGLE_URL, wait_until="domcontentloaded")
            await asyncio.sleep(random.uniform(1, 2))
            
            # Random mouse movement
            await self.random_mouse_movement(page)
            
            # Accept cookies if present (common in some regions)
            try:
                accept_button = page.locator("button:has-text('Accept'), button:has-text('同意'), button:has-text('すべて同意'), button:has-text('I agree')")
                if await accept_button.count() > 0:
                    await accept_button.first.click(timeout=2000)
                    await asyncio.sleep(random.uniform(0.5, 1.5))
            except:
                pass
            
            # Check for CAPTCHA before searching
            if await self.check_for_captcha(page):
                captcha_handled = await self.handle_captcha(page, keyword)
                if not captcha_handled:
                    # Only skip if handle_captcha explicitly returns False (not skip mode)
                    result["error"] = "CAPTCHA detected and could not proceed"
                    print(f"⏭️  Skipping keyword '{keyword}' due to CAPTCHA")
                    return result
                # If skip_captcha is enabled, captcha_handled will be True and we continue
            
            # Find search box and enter keyword with human-like typing
            search_box = page.locator("textarea[name='q'], input[name='q']")
            await search_box.wait_for(state="visible", timeout=5000)
            
            # Human-like typing
            await self.human_type(page, search_box, keyword)
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Random mouse movement before submitting
            await self.random_mouse_movement(page)
            
            # Submit search
            await search_box.press("Enter")
            await page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(random.uniform(2, 4))
            
            # Check for CAPTCHA after search
            if await self.check_for_captcha(page):
                captcha_handled = await self.handle_captcha(page, keyword)
                if not captcha_handled:
                    # Only skip if handle_captcha explicitly returns False (not skip mode)
                    result["error"] = "CAPTCHA detected after search and could not proceed"
                    print(f"⏭️  Skipping keyword '{keyword}' due to CAPTCHA")
                    return result
                # If skip_captcha is enabled, captcha_handled will be True and we continue
            
            # Get domain for searching
            domain = self.target_url.replace("https://", "").replace("http://", "").split("/")[0]
            
            # Check if CAPTCHA is blocking the search results
            # If skip_captcha is enabled, try to proceed anyway
            if await self.check_for_captcha(page):
                if SKIP_CAPTCHA:
                    print("⚠️  CAPTCHA present on results page, but continuing search anyway...")
                    # Try to scroll past CAPTCHA or wait a bit
                    await asyncio.sleep(random.uniform(2, 3))
            
            # Search through all pages until found or no more pages
            current_page = 1
            no_more_pages = False
            
            while True:
                print(f"📄 Checking page {current_page}...")
                
                # Check for CAPTCHA on current page
                if await self.check_for_captcha(page):
                    if SKIP_CAPTCHA:
                        print("   ⚠️  CAPTCHA detected on this page, but continuing...")
                        await asyncio.sleep(random.uniform(1, 2))
                    else:
                        # If not in skip mode, handle normally
                        captcha_handled = await self.handle_captcha(page, keyword)
                        if not captcha_handled:
                            break
                
                # Random scroll to appear more human-like
                await page.evaluate("window.scrollTo(0, Math.random() * 300)")
                await asyncio.sleep(random.uniform(0.5, 1))
                
                # Check current page for target URL
                found, link, position, total_results = await self.check_page_for_target(page, domain, current_page)
                
                if found and link:
                    result["found"] = True
                    result["page"] = current_page
                    result["position"] = position
                    
                    # Click on the result - open in new tab
                    clicked, new_page = await self.click_on_result(page, link, position, current_page, context)
                    if clicked:
                        result["clicked"] = True
                        print(f"✅ Successfully opened your site in new tab!")
                        # Move to next keyword after finding and opening
                        print(f"➡️  Moving to next keyword...")
                        break
                    else:
                        # If click failed, continue searching
                        print(f"⚠️  Opening failed, continuing search...")
                
                # Not found on this page, try next page
                if not found:
                    print(f"   Not found on page {current_page}")
                
                # Try to go to next page
                if await self.go_to_next_page(page):
                    current_page += 1
                    await asyncio.sleep(random.uniform(1, 2))
                    
                    # Check for CAPTCHA on new page
                    if await self.check_for_captcha(page):
                        captcha_handled = await self.handle_captcha(page, keyword)
                        if not captcha_handled:
                            # Only skip if handle_captcha explicitly returns False (not skip mode)
                            result["error"] = f"CAPTCHA detected on page {current_page} and could not proceed"
                            print(f"⏭️  Skipping keyword '{keyword}' due to CAPTCHA on page {current_page}")
                            break
                        # If skip_captcha is enabled, captcha_handled will be True and we continue
                else:
                    # No more pages available
                    no_more_pages = True
                    print(f"   No more pages available (reached end of results)")
                    break
            
            if not result["found"]:
                print(f"❌ Your site not found in search results (searched {current_page} page(s))")
            else:
                if result["clicked"]:
                    print(f"✅ Successfully found and opened your site in new tab(s)!")
                else:
                    print(f"⚠️  Found but could not open")
            
        except Exception as e:
            result["error"] = str(e)
            print(f"❌ Error during search: {e}")
        
        return result
    
    async def run(self):
        """Run automation for all keywords."""
        print(f"🚀 Starting SEO Automation")
        print(f"📌 Target URL: {self.target_url}")
        print(f"🔑 Keywords: {len(self.keywords)}")
        print(f"{'='*60}\n")
        
        async with async_playwright() as p:
            # Enhanced browser arguments for stealth mode
            browser_args = [
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-site-isolation-trials',
                '--disable-infobars',
                '--window-size=1920,1080',
            ]
            
            # Context options with realistic settings
            context_options = {
                'viewport': {'width': 1920, 'height': 1080},
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                'locale': 'ja-JP',
                'timezone_id': 'Asia/Tokyo',
                'permissions': ['geolocation'],
                'geolocation': {'latitude': 34.6937, 'longitude': 135.5023},  # Osaka coordinates
                'color_scheme': 'light',
            }
            
            # Use persistent context to maintain cookies and session
            if USE_PERSISTENT_CONTEXT:
                # Create directory if it doesn't exist
                self.user_data_dir.mkdir(parents=True, exist_ok=True)
                
                # Use launch_persistent_context for persistent storage
                context = await p.chromium.launch_persistent_context(
                    user_data_dir=str(self.user_data_dir),
                    headless=HEADLESS,
                    args=browser_args,
                    **context_options
                )
            else:
                # Launch browser normally
                browser = await p.chromium.launch(
                    headless=HEADLESS,
                    args=browser_args
                )
                context = await browser.new_context(**context_options)
            
            # Add extra HTTP headers
            await context.set_extra_http_headers({
                'Accept-Language': 'ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            })
            
            # Override webdriver property
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Override plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                
                // Override languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['ja-JP', 'ja', 'en-US', 'en']
                });
            """)
            
            page = await context.new_page()
            
            try:
                for i, keyword in enumerate(self.keywords, 1):
                    print(f"\n{'='*60}")
                    print(f"Keyword {i}/{len(self.keywords)}")
                    
                    result = await self.search_and_click(page, keyword, context)
                    self.results.append(result)
                    
                    # Random delay between searches (except for last one)
                    if i < len(self.keywords):
                        delay = random.uniform(*DELAY_BETWEEN_SEARCHES)
                        print(f"⏳ Waiting {delay:.1f} seconds before next search...")
                        await asyncio.sleep(delay)
                
            finally:
                await context.close()
            
            # Print summary
            self.print_summary()
    
    def print_summary(self):
        """Print summary of results."""
        print(f"\n{'='*60}")
        print("📊 SUMMARY")
        print(f"{'='*60}")
        
        total_searches = len(self.results)
        found_count = sum(1 for r in self.results if r["found"])
        clicked_count = sum(1 for r in self.results if r["clicked"])
        
        print(f"Total searches: {total_searches}")
        print(f"Found: {found_count}")
        print(f"Clicked: {clicked_count}")
        print(f"\nDetailed results:")
        
        for result in self.results:
            status = "✅" if result["clicked"] else ("🔍" if result["found"] else "❌")
            print(f"{status} {result['keyword']}")
            if result["found"]:
                page_info = f"Page {result['page']}" if result.get("page") else "Unknown page"
                print(f"   Found on: {page_info}, Position: {result['position']}")
            if result["error"]:
                print(f"   Error: {result['error']}")


async def main():
    """Main entry point."""
    automation = SEOAutomation(KEYWORDS, TARGET_URL)
    await automation.run()


if __name__ == "__main__":
    asyncio.run(main())

