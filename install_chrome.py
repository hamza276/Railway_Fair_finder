import os
import sys
import requests
import subprocess
from pathlib import Path

def download_file(url, filename):
    """Download file with progress"""
    print(f"Downloading {filename}...")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    with open(filename, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    print(f"Downloaded {filename}")

def install_chrome_windows():
    """Install Chrome on Windows"""
    try:
        print("Chrome install kar rahe hain Windows par...")
        
        # Download Chrome installer
        chrome_url = "https://dl.google.com/chrome/install/375.126/chrome_installer.exe"
        installer_path = "chrome_installer.exe"
        
        download_file(chrome_url, installer_path)
        
        # Run installer
        print("Chrome installer run kar rahe hain...")
        subprocess.run([installer_path, "/silent", "/install"], check=True)
        
        # Cleanup
        os.remove(installer_path)
        
        print("Chrome successfully install ho gaya!")
        return True
        
    except Exception as e:
        print(f"Chrome installation mein error: {str(e)}")
        return False

def check_chrome():
    """Check if Chrome is installed"""
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")
    ]
    
    for path in chrome_paths:
        if os.path.exists(path):
            print(f"Chrome found at: {path}")
            return True
    
    return False

def main():
    print("Chrome Installation Helper")
    print("=" * 40)
    
    if check_chrome():
        print("✅ Chrome already installed hai!")
    else:
        print("❌ Chrome nahi mila")
        
        if sys.platform == "win32":
            choice = input("Kya Chrome install karna chahte hain? (y/n): ")
            if choice.lower() in ['y', 'yes', 'han']:
                install_chrome_windows()
            else:
                print("Manual se Chrome install kariye: https://www.google.com/chrome/")
        else:
            print("Manual se Chrome install kariye: https://www.google.com/chrome/")

if __name__ == "__main__":
    main()