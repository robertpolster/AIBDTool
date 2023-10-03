from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import time
from pdf2image import convert_from_path
import pytesseract
import pandas as pd
import os
import re
import shutil
import requests
from requests_html import HTMLSession
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
FUNCTION_COMPLETED = False

s = HTMLSession()
headers = {
    'authority': 'www.google.com',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'accept-language': 'en-US,en;q=0.5',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'sec-gpc': '1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
}

# Function to initialize the driver
def initialize_driver():
    # Define the current directory
    current_directory = os.getcwd()
    service = Service("app/chromedriver-linux64/chromedriver")
    options = Options()
    options.add_argument("--incognito")
    options.add_argument("--kiosk-printing")
    options.add_argument(f"--download.default_directory={current_directory}")  # Set the download directory
    return webdriver.Chrome(service=service, options=options)


# Function to check if the button with the specific UUID exists and click on it

def get_titles(parentuui):

    df = pd.read_csv("test/merged.csv")

    title = df[df['parentUII'] == parentuui]['parentInvestmentTitle'].unique()
    
    if title.size > 0:  # Ensure that title exists
        return f"""{title[0]} "{parentuui}" """
    else:
        print(f"No title found for {parentuui}")
        return f""" "{parentuui}" """  # return only the uui if no title is found




def get_pdf_content(pdf_path):
    # Convert PDF to list of images
    images = convert_from_path(pdf_path)

    all_text = ""
    for image in images:
        # Extract text from image using OCR
        text = pytesseract.image_to_string(image, lang='eng')
        all_text += text

    # Post-processing: Reduce multiple spaces to single space
    processed_text = ' '.join(all_text.split())
    
    # Convert multiple newlines to a single newline
    processed_text = '\n'.join(line.strip() for line in processed_text.splitlines() if line.strip())
    print(processed_text)
    return processed_text

def save_as_pdf(link,uuid_value):
    # Check if the link is a PDF link
    if link.endswith('.pdf'):
        download_pdf(link,uuid_value)
    else:
        driver = initialize_driver()
        time.sleep(1)
        # Navigate to the specific link
        driver.get(link)
        time.sleep(4)  # Give time for the page to load
        
        # Use the browser's print option and save as PDF
        driver.execute_script('window.print();')
        time.sleep(4)
        driver.quit()

def download_pdf(link,uuid_value):
    '''Function to download a PDF directly.'''
    r = requests.get(link, stream=True)
    with open(f"test/files/{uuid_value}.pdf", 'wb') as pdf:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                pdf.write(chunk)
    # print(f"PDF downloaded from: {link}")
def clean_links(links):
    
    # Define a list of patterns that we want to exclude
    exclude_patterns = [
        r'google\.com/search.*tbm=isch',      # Google Images
        r'google\.com/search.*tbm=nws',       # Google News
        r'google\.com/search.*tbm=bks',       # Google Books
        r'google\.com/search.*tbm=vid',       # Google Videos
        r'google\.com/search.*tbm=shop',      # Google Shopping
        r'google\.com/search\?',              # General Google Search
        r'google\.com/webhp',                 # Google Homepage
        r'itdashboard\.gov',                  # IT Dashboard link
        r'support\.google\.com',              # Google Support
        r'policies\.google\.com',             # Google Policies/Terms
        r'google\.com/intl/.+/policies',      # Google Intl Policies/Terms
        r'google\.com/advanced_search',       # Google Advanced Search
        r'google\.com/settings',              # Google Settings
        r'accounts\.google\.com/.*',          # Any URL starting with accounts.google.com
        r'\.pdf$',                            # Links that end with .pdf
        r'\.csv$',                            # Links that end with .csv
        r'ads\.google\.com/intl/.+/home',     # Google Ads Intl Home
        r'maps\.google\.com',                 # Google Maps
        r'https?://www-datosperu-org\.translate\.goog/.*', # The provided URL to exclude
        r'https?://www\.datosperu\.org/.*'  # Exclude all URLs from www.datosperu.org
    ]


    filtered_links = [link for link in links if not any(re.search(pattern, link) for pattern in exclude_patterns)]

    return filtered_links

def check_and_click_button(uuid_value):
    try:
        params = {
            'q': uuid_value,
            'num': 10,
        }

        response = s.get('https://www.google.com/search', params=params)

        if 'did not match any documents' in response.text:
            print(f'No Results Found for {uuid_value}')
        elif 'Our systems have detected unusual traffic from your computer' in response.text:
            exit('Captcha Triggered!\nUse Vpn Or Try After Sometime.')
        else:
            links = list(response.html.absolute_links)

            links = clean_links(links)

            highergov_found = False  # Initialize the flag as False

            for link in links:
                if "www.highergov.com" in link:
                    time.sleep(3)
                    save_as_pdf(link,uuid_value)
                    print(f"found for: {uuid_value}")
                    highergov_found = True  # Update the flag to True when "highergov" is found
                    break

            if highergov_found==False:
                print(f"Not found for {uuid_value}")
            

    except NoSuchElementException:
        print(f"No button found for UUID: {uuid_value}")

class MovePDFHandler(FileSystemEventHandler):
    def __init__(self, dest_folder):
        self.dest_folder = dest_folder

    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith('.pdf'):
            time.sleep(2)  # Ensure the file write completes, adjust this if needed
            shutil.move(event.src_path, os.path.join(self.dest_folder, os.path.basename(event.src_path)))


def monitor_and_move_files(src_folder, dest_folder, observer):
    event_handler = MovePDFHandler(dest_folder)
    observer.schedule(event_handler, path=src_folder, recursive=False)
    observer.start()

    global FUNCTION_COMPLETED
    try:
        while True:
            time.sleep(1)
            if FUNCTION_COMPLETED:
                observer.stop()
                break
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

# Define the function to run the monitor in a separate thread
def start_monitoring(src_folder, dest_folder):
    import threading
    observer = Observer() # Create an instance of the Observer here
    t = threading.Thread(target=monitor_and_move_files, args=(src_folder, dest_folder, observer))
    t.start()


def google_search_results(uuid_values):
    # Start monitoring the downloads directory
    DOWNLOADS_FOLDER = os.path.join(os.getcwd(), "/home/aqib/Downloads")  # Adjust this to your downloads folder path
    DESTINATION_FOLDER = os.path.join(os.getcwd(), "app/files")  # Adjust this to your desired folder path

    start_monitoring(DOWNLOADS_FOLDER, DESTINATION_FOLDER)
    uuid_values=get_titles(uuid_values)

    check_and_click_button(uuid_values)

    print("Google Search Done")

    # Set the FUNCTION_COMPLETED flag to True after the check_and_click_button function completes
    global FUNCTION_COMPLETED
    FUNCTION_COMPLETED = True

google_search_results("024-000005253")