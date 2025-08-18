[From Zero to Fully Automated: My 48-Hour Playwright Challenge](https://medium.com/gitconnected/from-zero-to-fully-automated-my-48-hour-playwright-challenge-379996088063)

```python
# main.py
# This script automates web testing using Playwright as described in the article.
# It logs in to a test site, navigates through three workflows, captures screenshots in a timestamped folder,
# and logs structured JSON events to a file.

import json
import time
import os
from playwright.sync_api import sync_playwright

# Function to log events in structured JSON format
def log_event(event, details):
    with open("run_log.json", "a") as f:
        f.write(json.dumps({
            "timestamp": time.time(),
            "event": event,
            "details": details
        }) + "\n")

# Main automation function
def run_automation():
    # Create a timestamp for this run
    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
    # Create a directory for screenshots named by timestamp
    screenshot_dir = f"screenshots/{timestamp}"
    os.makedirs(screenshot_dir, exist_ok=True)
    
    # Start logging
    log_event("start", {"run_timestamp": timestamp})
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Set headless=True for production
        page = browser.new_page()
        
        # Step 0: Navigate to the test site (assuming a placeholder URL; replace with actual)
        page.goto("https://example.com/login")  # Replace with actual test site URL
        page.screenshot(path=f"{screenshot_dir}/step_0_login_page.png")
        log_event("navigated_to_login", {"url": page.url})
        
        # Step 1: Log in using semantic selectors
        page.fill("input[name='username']", "test_user")
        page.fill("input[name='password']", "secure_pass")
        page.click("button[type='submit']")
        # Wait for dashboard to load to make it bulletproof
        page.wait_for_selector("div.dashboard-loaded")  # Assuming this selector exists; adjust as needed
        page.screenshot(path=f"{screenshot_dir}/step_1_logged_in.png")
        log_event("logged_in", {"username": "test_user"})
        
        # Step 2: Navigate through three workflows
        # Workflow 1: Assuming navigation to a page, waiting for load, etc. (placeholders)
        page.click("a[href='/workflow1']")  # Adjust selector
        page.wait_for_selector("div.workflow1-loaded")  # Adjust selector
        page.screenshot(path=f"{screenshot_dir}/step_2_workflow1.png")
        log_event("completed_workflow1", {"details": "Navigated to workflow 1"})
        
        # Workflow 2
        page.click("a[href='/workflow2']")  # Adjust selector
        page.wait_for_selector("div.workflow2-loaded")  # Adjust selector
        page.screenshot(path=f"{screenshot_dir}/step_3_workflow2.png")
        log_event("completed_workflow2", {"details": "Navigated to workflow 2"})
        
        # Workflow 3
        page.click("a[href='/workflow3']")  # Adjust selector
        page.wait_for_selector("div.workflow3-loaded")  # Adjust selector
        page.screenshot(path=f"{screenshot_dir}/step_4_workflow3.png")
        log_event("completed_workflow3", {"details": "Navigated to workflow 3"})
        
        # End logging
        log_event("end", {"run_timestamp": timestamp, "status": "success"})
        
        browser.close()

if __name__ == "__main__":
    run_automation()
```

```python
# scheduler.py
# This is a separate lightweight scheduler script to run the main automation every hour,
# as described in the article.

import subprocess
import time

while True:
    print("Starting automation run...")
    subprocess.run(["python", "main.py"])
    print("Automation run completed. Waiting 1 hour...")
    time.sleep(3600)  # Run every hour
```
