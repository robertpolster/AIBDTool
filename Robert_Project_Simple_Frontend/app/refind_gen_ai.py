import pandas as pd
import os
import time
import logging
import re
import openai
from dotenv import load_dotenv
from app.proposal_chatbot import get_pdf_content
import docx2txt

load_dotenv()
openai.api_key = os.environ.get("OPENAI_API_KEY")


def read_docs(filename):
        text = docx2txt.process(filename)
        # Split the text by lines, filter out empty lines, and join them back together
        cleaned_text = '\n'.join(line for line in text.split('\n') if line.strip())

        return cleaned_text

def split_projects(response):
    # Old pattern
    old_pattern = r"(Project \(\d+-?\d*\):.*?f\) Investment Title: [^\n]+)"
    # New pattern
    new_pattern = r"(Project \d+:.*?f\) Investment Title: [^\n]+)"
    # Additional pattern
    additional_pattern = r"(Project \(\d+-\d+\):.*?f\) Investment Title: [^\n]+)"
    
    projects = re.findall(old_pattern, response, re.DOTALL)  # Using re.DOTALL to make '.' match newlines
    
    # If no matches with the old pattern, try the new pattern
    if not projects:
        projects = re.findall(new_pattern, response, re.DOTALL)

    # If no matches with the new pattern, try the additional pattern
    if not projects:
        projects = re.findall(additional_pattern, response, re.DOTALL)

    return projects

class Chatbot:
    def __init__(self):
        self.messages = self.Initial_prompt()

    def Initial_prompt(self):
        df=pd.read_csv("app/files/merged.csv")
        df_new = df[['agencyCode(Investment)', 'agencyName(Investment)','parentUII','parentInvestmentTitle','budgetAccountCode','fundingAmount','agencyCode','investmentType','agencyProjectId','projectName','projectGoal','softwareProject']]
        # df.to_csv("custom_merged.csv")

        try:
            docs = read_docs("app/files/past_project.docx")
        except FileNotFoundError:
            try:
                docs = get_pdf_content("app/files/past_project.pdf")
            except FileNotFoundError:
                return "file_error"
        except Exception as e:
            # Handle other exceptions differently if you want
            print(f"An unexpected error occurred: {e}")


        

        prompt = [
            {
                "role": "system",
                "content": f""" You are an expert business analyst for a company. I will provide you with the two things a dataframe that contains information about the 50 future projects and a file that contains the information of projects your company has done.
                You main role is to analyze the projects file which contains information about which projects your company has done and then look at the future projects in the dataframe and find out which projects your company can do based on the projects your company has already done.
                After looking at both the files return the list of five projects that the company can do. 
                1) You won't have any more information about the future projects that will be provided to you, you are restricted to tell by analyzing only this provided information. 
                2) Don't provide the projects which have almost identical or repeating information in their columns, provide only one from those. Exclude the repeating one from your list and choose some other one.
                3) Prefer to pick the project's which are closely related to previous that company has done and have some high funding amount.
                Here is the Company's Project File which company has done:
                {docs}.
                4) Their Row Number explicitly as "Row# number from their respective Row number in dataframe".
                5) Please return these Projects details seperately from the given dataframe after analyzing as in the format given below:
                Project (1):
                    a) Row#:
                    b) Funding Amount:
                    c) Agency:
                    d) Investment Type:
                    e) parent UUI:
                    f) Investment Title:
                Project (2):
                    a) Row#:
                    b) Funding Amount:
                    c) Agency:
                    d) Investment Type:
                    e) parent UUI:
                    f) Investment Title:
                """,
            },
            {
                "role":"user",
                "content":f""" Here is the Future Projects Dataframe:
                {df_new}.
                Please return these Projects details seperately from the given dataframe after analyzing as in the format given below:
                Project (1-5):
                    a) Row#:
                    b) Funding Amount:
                    c) Agency:
                    d) Investment Type:
                    e) parent UUI:
                    f) Investment Title:
                """
                
            }
        ]
        return prompt

    def create_chat_completion(self):

        if self.messages=="file_error":
            return "file_error"

        retry_attempts = 3
        retry_delay = 5  # delay in seconds

        for attempt in range(retry_attempts):
            try:
                chat_completion_resp = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo-16k",
                    messages=self.messages,
                    temperature=0.2,  # noqa
                )
                # if request is successful, break out of loop
                break
            except Exception as e:
                if attempt + 1 == retry_attempts:
                    print("Exception: ",str(e))
                    logging.info("Attempt failed due to openai server")
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

        return message_content


def extract_row_numbers(response_text):
    pattern = r"(?i)row\s*#?:?\s*(\d+)"
    matches = re.findall(pattern, response_text)
    return [int(match) for match in matches]


def extract_parentUUI():
    
    df=pd.read_csv("app/files/merged.csv")

    bot=Chatbot()
    message=bot.create_chat_completion()

    # print(message)

    if message=="file_error":
        return "Please Upload Past Project File First"

    project=split_projects(message)

    if project:

        try:
            row_numbers = extract_row_numbers(message)
        except:
            return "Could Not extract row Numbers from chatgpt response"

        parent_uui=[]

        try:
            for row_number in row_numbers:
                parent_uui.append(df["parentUII"][row_number])
        except:
            return "Could Not extract ParentUUI from the merged.csv file. Issue in extracted row numbers"

        if parent_uui:
            return parent_uui,project
        else:
            return "empty"
    else:
        return "Could Not Split The Projects "

# print(extract_parentUUI())