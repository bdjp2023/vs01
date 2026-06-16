# Project Title: Browser Utilities

## Overview
This project provides low-level utilities for browser operations, designed to facilitate web scraping and automation tasks. It includes functionalities such as applying stealth to avoid detection, checking robots.txt for access permissions, simulating human-like behavior during interactions, and detecting blocks from services like Cloudflare.

## Features
- **Stealth Mode**: Apply stealth techniques to minimize detection by websites.
- **Robots.txt Checker**: Verify if a target URL is accessible based on the site's robots.txt file.
- **Human-like Behavior Simulation**: Introduce random delays and movements to mimic human interactions.
- **Block Detection**: Identify if a page is blocked by services like Cloudflare or DataDome.

## Setup Instructions
1. Clone the repository:
   ```
   git clone <repository-url>
   cd vs01
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Configure your environment as needed, including any necessary API keys or settings.

## Usage
To use the browser utilities, import the `browser_utils.py` module in your Python scripts. You can call the various functions provided to perform tasks such as web scraping or automation.

Example:
```python
from browser_utils import apply_stealth, check_robots

# Apply stealth to a page
apply_stealth(page)

# Check if a URL is allowed by robots.txt
is_allowed = check_robots(base_url, target_url, user_agent)
```

## Debugging
For debugging, use the provided `.vscode/launch.json` configuration to run Python scripts and Jupyter notebooks in agent mode.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.