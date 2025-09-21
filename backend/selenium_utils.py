from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Helper for stable headless Chrome in containers
def make_headless_chrome():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1280,800")
    return webdriver.Chrome(options=opts)
