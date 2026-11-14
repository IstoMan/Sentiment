#!/usr/bin/env python3
"""Capture screenshots of the Sentiment Analyzer UI"""
import os
import time
import sys

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
except ImportError:
    print("Error: selenium not installed. Run: pip install selenium")
    sys.exit(1)

# Create docs directory if it doesn't exist
os.makedirs('docs/screenshots', exist_ok=True)

# Try Chrome first, then Firefox
driver = None
try:
    # Try headless Chrome
    chrome_options = ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    driver = webdriver.Chrome(options=chrome_options)
    print("Using Chrome")
except:
    try:
        # Try headless Firefox
        firefox_options = FirefoxOptions()
        firefox_options.add_argument('--headless')
        firefox_options.add_argument('--width=1920')
        firefox_options.add_argument('--height=1080')
        driver = webdriver.Firefox(options=firefox_options)
        print("Using Firefox")
    except Exception as e:
        print(f"Error: Could not initialize browser: {e}")
        print("Try installing chrome or firefox")
        sys.exit(1)

try:
    # Navigate to the application
    url = 'http://127.0.0.1:8000'
    print(f"Loading {url}...")
    driver.get(url)
    
    # Wait for page to load
    time.sleep(2)
    
    # Capture main page
    print("Capturing main page...")
    driver.save_screenshot('docs/screenshots/01-main-page.png')
    
    # Fill in a review
    print("Filling in review form...")
    textarea = driver.find_element(By.ID, 'reviewText')
    textarea.send_keys("This product is absolutely amazing! Best purchase I've ever made. Highly recommended!")
    
    # Take screenshot of filled form
    print("Capturing filled form...")
    driver.save_screenshot('docs/screenshots/02-review-input.png')
    
    # Submit the form
    print("Submitting form...")
    submit_btn = driver.find_element(By.ID, 'submitBtn')
    submit_btn.click()
    
    # Wait for result
    time.sleep(2)
    
    # Capture result
    print("Capturing analysis result...")
    driver.save_screenshot('docs/screenshots/03-positive-result.png')
    
    # Add another review (negative)
    print("Adding negative review...")
    textarea = driver.find_element(By.ID, 'reviewText')
    textarea.clear()
    textarea.send_keys("Terrible product! Complete waste of money. Very disappointed.")
    submit_btn.click()
    time.sleep(2)
    
    # Scroll down to see statistics
    driver.execute_script("window.scrollTo(0, 400);")
    time.sleep(1)
    
    # Capture statistics
    print("Capturing statistics...")
    driver.save_screenshot('docs/screenshots/04-statistics.png')
    
    # Scroll to see recent reviews
    driver.execute_script("window.scrollTo(0, 800);")
    time.sleep(1)
    
    # Capture recent reviews
    print("Capturing recent reviews...")
    driver.save_screenshot('docs/screenshots/05-recent-reviews.png')
    
    print("\n✓ Screenshots captured successfully!")
    print("  - docs/screenshots/01-main-page.png")
    print("  - docs/screenshots/02-review-input.png")
    print("  - docs/screenshots/03-positive-result.png")
    print("  - docs/screenshots/04-statistics.png")
    print("  - docs/screenshots/05-recent-reviews.png")
    
finally:
    if driver:
        driver.quit()
