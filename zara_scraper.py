from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import random
from bs4 import BeautifulSoup
import pandas as pd
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
load_dotenv()
import os

TARGET_ITEM = "linen blend"
USER_EMAIL = os.getenv("EMAIL_ADDRESS")
APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")

chrome_options = Options()
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36")

driver = webdriver.Chrome(options=chrome_options)

# === OPEN ZARA PAGE ===
url = 'https://www.zara.com/in/en/woman-dresses-l1066.html?v1=2113500'
driver.get(url)
time.sleep(random.uniform(3, 6))  # mimic human delay

# === SCROLL TO LOAD MORE ===
SCROLL_PAUSE = 2
last_height = driver.execute_script("return document.body.scrollHeight")
for _ in range(5):
    if not driver.window_handles:
        print("❌ Browser closed early.")
        exit()
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(SCROLL_PAUSE)
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        break
    last_height = new_height

# === PARSE HTML ===
print("🧪 Preview of HTML (first 2000 chars):")
print(driver.page_source[:2000])
soup = BeautifulSoup(driver.page_source, 'lxml')
driver.quit()

# === EXTRACT DATA ===
names = []
prices = []

items = soup.select('a.product-link._item')  # Zara uses dynamic class names
for item in items:
    name = item.get_text(strip=True)
    price = item.find_next('span')
    names.append(name)
    prices.append(price.text.strip() if price else "")

df = pd.DataFrame({'product_name': names, 'price': prices})
print("✅ Scraped Data:")
print(df.head())

# === SAVE TO CSV ===
df.to_csv('fashion.csv', index=False)
print("📁 Data saved to fashion.csv")

# === OPTIONAL: EMAIL ALERT IF ITEM FOUND ===
matched_items = df[df['product_name'].astype(str).str.contains(TARGET_ITEM, case=False)]
if not matched_items.empty:
    email_content = f"🎯 Price match found for '{TARGET_ITEM}':\n\n{matched_items.to_string(index=False)}"
    msg = EmailMessage()
    msg['Subject'] = f"Zara Price Alert for '{TARGET_ITEM}'"
    msg['From'] = USER_EMAIL
    msg['To'] = USER_EMAIL
    msg.set_content(email_content)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(USER_EMAIL, APP_PASSWORD)
        smtp.send_message(msg)

    print(f"📧 Email sent to {USER_EMAIL}")
else:
    print("🔍 No matching item found for alert.")
