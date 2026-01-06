# SEO Automation Tool

Automates Google searches with specific keywords and clicks on your website (https://shinonome.llc/) when it appears in search results. This helps increase click-through rates and potentially improve SEO rankings.

## Features

- 🔍 Automatically searches Google with multiple keywords
- 🎯 Detects when your website appears in search results
- 🖱️ Automatically clicks on your website when found
- ⏱️ Random delays between actions to appear more natural
- 🛡️ Anti-detection measures to reduce CAPTCHA triggers:
  - Stealth mode with realistic browser fingerprinting
  - Human-like typing and mouse movements
  - Persistent browser context (maintains cookies/session)
  - Random scrolling and delays
- 🚫 CAPTCHA detection and handling (manual solve or skip)
- 📊 Provides detailed summary of results

## Setup

### 1. Install Python

Make sure you have Python 3.8 or higher installed. **Note:** Python 3.13 may have compatibility issues. If you encounter errors, use Python 3.11 or 3.12 instead.

### 2. Install Dependencies

**Option A: Standard Installation**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Option B: If you're using Python 3.13 and get greenlet compilation errors:**

Try installing greenlet separately first:
```bash
pip install --upgrade pip
pip install greenlet --only-binary :all:
pip install -r requirements.txt
```

**Option C: Use Python 3.11 or 3.12 (Recommended if Option B fails)**

If you're using Python 3.13 and continue to have issues, consider using Python 3.11 or 3.12:
1. Download Python 3.12 from [python.org](https://www.python.org/downloads/)
2. Install it
3. Use it for this project

### 3. Install Playwright Browsers

```bash
playwright install chromium
```

## Configuration

Edit `config.json` to customize:

- **keywords**: List of keywords to search for
- **target_url**: Your website URL
- **max_results_to_check**: Number of search results to check per page
- **delay_between_searches**: Random delay range (in seconds) between searches (recommended: 5-12 seconds)
- **delay_between_clicks**: Random delay range (in seconds) after clicking (recommended: 3-8 seconds)
- **headless**: Set to `true` to run browser in background, `false` to see the browser
- **use_persistent_context**: Set to `true` to maintain cookies/session between runs (reduces CAPTCHA)
- **wait_for_captcha_manual**: Set to `true` to wait for you to manually solve CAPTCHA, `false` to skip searches with CAPTCHA

## Usage

### Basic Usage

```bash
python seo_automation.py
```

The script will:
1. Open a browser window
2. Search for each keyword on Google
3. Check if your website appears in results
4. Click on your website if found
5. Display a summary of results

### Running in Background

Edit `config.json` and set `"headless": true` to run without showing the browser window.

## Important Notes

⚠️ **Use Responsibly**: 
- This tool is for legitimate SEO testing purposes
- Google may detect automated behavior if used excessively
- Use appropriate delays between searches
- Don't run this too frequently (e.g., once per day is reasonable)

⚠️ **Legal Considerations**:
- Make sure your use of this tool complies with Google's Terms of Service
- This is for testing and legitimate SEO purposes only

## Troubleshooting

### Installation Errors (Python 3.13 / greenlet compilation error)

If you see errors about `greenlet` failing to build:

1. **Try installing greenlet with pre-built wheels:**
   ```bash
   pip install --upgrade pip
   pip install greenlet --only-binary :all:
   pip install -r requirements.txt
   ```

2. **Use Python 3.11 or 3.12 instead:**
   - Python 3.13 is very new and some packages don't have pre-built wheels yet
   - Download Python 3.12 from [python.org](https://www.python.org/downloads/)
   - Create a virtual environment with Python 3.12:
     ```bash
     py -3.12 -m venv venv
     .\venv\Scripts\Activate
     pip install -r requirements.txt
     ```

3. **Install Visual Studio Build Tools (if you must use Python 3.13):**
   - Download from: https://visualstudio.microsoft.com/downloads/
   - Install "Desktop development with C++" workload
   - This allows packages to compile from source

### Browser doesn't open
- Make sure Playwright browsers are installed: `playwright install chromium`
- Check if you have the latest version: `pip install --upgrade playwright`

### Website not found
- Your website might not be ranking for those keywords yet
- Try different keywords or wait for better rankings

### CAPTCHA Appears Frequently

If CAPTCHA appears too often:

1. **Increase delays** in `config.json`:
   - Set `delay_between_searches` to `[10, 20]` (longer delays)
   - Set `delay_between_clicks` to `[5, 15]`

2. **Use persistent context** (already enabled by default):
   - This maintains cookies and session between runs
   - Reduces CAPTCHA triggers over time

3. **Manual CAPTCHA solving**:
   - When CAPTCHA appears, the script will pause and wait for you to solve it
   - You have 60 seconds to solve it manually in the browser
   - After solving, the script continues automatically

4. **Reduce frequency**:
   - Don't run the script too often (once per day is recommended)
   - Space out your automation sessions

5. **Use a VPN or different IP** (if needed):
   - Sometimes IP-based detection triggers CAPTCHA

### Timeout errors
- Increase delays in `config.json`
- Check your internet connection
- Google might be blocking automated requests (try again later)

## Customization

You can modify `seo_automation.py` to:
- Add more keywords
- Change search engine (Bing, Yahoo, etc.)
- Add logging to a file
- Schedule automatic runs

## License

This tool is provided as-is for educational and legitimate SEO testing purposes.

