from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import time
import os
from selenium.webdriver.common.keys import Keys

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

def move_and_replace(src, dest):
    """
    Move file from src to dest, replacing it if it already exists.
    """
    if os.path.exists(dest):
        os.remove(dest)
    os.rename(src, dest)


def scrape_business_cases(uuid):
    driver = initialize_driver()
    try:
        driver.get("https://www.itdashboard.gov/search-advanced")
        # Searching for the UUID
        search = driver.find_element(By.XPATH, "/html/body/div[1]/main/div/div[4]/div/div/div/div/form/div[1]/input")
        search.send_keys(uuid)
        search.send_keys(Keys.ENTER)  # Use ENTER key to initiate search
        time.sleep(3)
        try:
            # Try to find and click the "Download Business Case" button
            download_link = driver.find_element(By.XPATH, f"//a[contains(@href, '{uuid}') and text()='Download Business Case']")
            download_link.click()
            time.sleep(3)
            driver.execute_script('window.print();')
        except NoSuchElementException:
            # If "Download Business Case" button not found, try to find the heading
            time.sleep(1)
            heading_link = driver.find_element(By.XPATH, f"//a[contains(@href, '{uuid}')]")
            heading_link.click()
            time.sleep(3)

            expand_investment=driver.find_element(By.XPATH, "/html/body/div[1]/main/div/div[4]/div/div/div/ul[1]/li/button").click()
            expand_historic=driver.find_element(By.XPATH, "/html/body/div[1]/main/div/div[4]/div/div/div/ul[2]/li/button").click()
            expand_contratcs=driver.find_element(By.XPATH, "/html/body/div[1]/main/div/div[4]/div/div/div/ul[3]/li/button").click()
            download_investment=driver.find_element(By.XPATH, "/html/body/div[1]/main/div/div[4]/div/div/div/ul[1]/li/div/div[3]/a").click()
            download_investment2=driver.find_element(By.XPATH, "/html/body/div[1]/main/div/div[4]/div/div/div/ul[2]/li/div/div[2]/a").click()
            
            time.sleep(2)

            driver.execute_script('window.print();')
            time.sleep(3)
            count=0
            downloaded_files = os.listdir("/home/aimen/Downloads/")
            for file_name in downloaded_files:
                if (file_name.startswith("investment")) and file_name.endswith(".xlsx"):
                    stripped_file_name = file_name.replace(".xlsx", "")
                    new_file_name = f"{stripped_file_name}_{uuid}.xlsx"
                    move_and_replace(os.path.join("/home/aimen/Downloads/", file_name), os.path.join("/home/aimen/Robert_Business_Analyst_Project/Robert_Simple_UI/robert_simple/app/files", new_file_name))
                    count += 1
                    if count == 2:
                        break
                    
        # Rename the downloaded file based on the UUID
        downloaded_files = os.listdir("/home/aimen/Downloads/")
        for file_name in downloaded_files:
            if (file_name.startswith("Business") or file_name.startswith("Investment")) and file_name.endswith(".pdf"):
                new_file_name = f"Business_case_{uuid}.pdf"
                move_and_replace(os.path.join("/home/aimen/Downloads/", file_name), os.path.join("/home/aimen/Robert_Business_Analyst_Project/Robert_Simple_UI/robert_simple/app/files", new_file_name))
                break
        
    except NoSuchElementException:
        print(f"Neither button nor heading found for UUID: {uuid}")

    driver.quit()

# scrape_business_cases(["018-000000199", "020-000000066","024-000005253","005-000002223","015-000200137","021-002703942","006-000805100"])
