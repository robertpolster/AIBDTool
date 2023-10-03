import pandas as pd
import os
import time
import docx2txt
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import time
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import openai, re
from dotenv import load_dotenv
from pdf2image import convert_from_path
import pytesseract
import tiktoken

load_dotenv()
openai.api_key = os.environ.get("OPENAI_API_KEY")


def num_tokens_from_string(string: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding("cl100k_base")
    num_tokens = len(encoding.encode(string))
    return num_tokens

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

    return processed_text


class Chatbot:
    def __init__(self):
        self.messages = self.Initial_prompt()

    def Initial_prompt(self):

        try:
            docs = self.read_docs("app/files/past_project.docx")
        except FileNotFoundError:
            try:
                docs = get_pdf_content("app/files/hud_fy2024.pdf")
            except FileNotFoundError:
                return "file_error"
        except Exception as e:
            # Handle other exceptions differently if you want
            print(f"An unexpected error occurred: {e}")

        print(num_tokens_from_string(docs))
        # print(docs)
        prompt = [
            {
            "role": "system",
            "content": f"""You will be provided with a file that will contain information about past projects our company has successfully completed.
            Your objective is to carefully analyze the past project information and then I will provide you a list of departments and you will identify from that list and will return a department name that closely align with our past project and also tell the reason why are you selecting that department.
            Please provide the reason too why are you choosing this project.
            Also structure your response with the following headings and format:
            - Department Name 
            - Reason

            Please return three department names.
            Here is the Company's Project File, showcasing our history of past successful projects:
            {docs}.
            """,
      },
      {
        "role": "user",
        "content": f""" can you tell me to which department this past project closely aligns with here is the list:
        1) Department of Health
        2) Department of Housing and Urban Development

 
        PLease provide the reason too why are you selecting this department. Also tell in which part of the document the reason is mentioned that you are providing.
        """
      }
            ]

        return prompt
    
    def read_docs(self,filename):
        text = docx2txt.process(filename)
        # Split the text by lines, filter out empty lines, and join them back together
        cleaned_text = '\n'.join(line for line in text.split('\n') if line.strip())

        return cleaned_text


    def create_chat_completion(self):

        if self.messages=="file_error":
            return "file_error"
        
        retry_attempts = 3
        retry_delay = 5  # delay in seconds

        for attempt in range(retry_attempts):
            try:
                chat_completion_resp = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=self.messages,
                    temperature=0,  # noqa
                )
                # if request is successful, break out of loop
                break
            except Exception as e:
                if attempt + 1 == retry_attempts:
                    logging.info("Attempt failed due to openai server")
                    print("Exception: ",str(e))
                    return {
                        "role": "assistant",
                        "content": "OpenAI Attempt Failed",
                    }
                time.sleep(retry_delay)  # wait before retrying

        message_content = chat_completion_resp["choices"][0]["message"][
            "content"
        ]  # noqa
        role = chat_completion_resp["choices"][0]["message"]["role"]


        response_dict = {"role": role, "content": message_content}
        match = re.search(r'- (.+)', message_content)
        if match:
            result = match.group(1)
            return result

        return message_content

# Function to initialize the driver
def initialize_driver():
    # Define the current directory
    current_directory = os.getcwd()
    service = Service("app/chromedriver-linux64/chromedriver")
    options = Options()
    options.add_argument("--incognito")
    prefs = {
        "download.default_directory": os.path.join(current_directory, "app/files"),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True  # To automatically download the PDF files
    }
    options.add_experimental_option('prefs', prefs)
    return webdriver.Chrome(service=service, options=options)

def all_downloads_complete(driver):
    if not driver.current_url.startswith("chrome://downloads"):
        driver.get("chrome://downloads/")
    return driver.execute_script("""
        return document.querySelector('downloads-manager')
               .shadowRoot.querySelector('#downloadsList')
               .items.filter(item => item.state === 'IN_PROGRESS').length === 0;
    """)

def scrape_appendix(button_content):
    driver = initialize_driver()

    try:
        driver.get("https://www.whitehouse.gov/omb/budget/appendix/")

        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, f"//a[contains(text(), '{button_content}')]"))
        )

        driver.execute_script("arguments[0].scrollIntoView();", element)
        element.click()

        # Wait until all downloads are complete
        WebDriverWait(driver, 3600).until(all_downloads_complete)  # 1 hour timeout just in case
    except TimeoutException:
        print(f"Could not find a link containing '{button_content}' within 10 seconds.")
    except NoSuchElementException:
        print(f"No element with text '{button_content}' found.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        driver.quit()



bot=Chatbot()

# filename=bot.create_chat_completion()
# print(filename)
# scrape_appendix(filename)

