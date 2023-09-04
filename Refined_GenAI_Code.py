#!/usr/bin/env python
# coding: utf-8

# In[14]:


import pandas as pd
import docx
import os
import time
import logging
import openai
from dotenv import load_dotenv

load_dotenv()
# openai.api_key = os.environ.get("OPENAI_API_KEY")
openai.api_key= "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"
def read_docs(filename):
    doc = docx.Document(filename)
    fullText = []
    for para in doc.paragraphs:
        fullText.append(para.text)
    return '\n'.join(fullText)

def Initial_prompt():

    df=pd.read_csv("./merged.csv")
    df = df[['agencyCode(Investment)', 'agencyName(Investment)','parentUII','parentInvestmentTitle','budgetAccountCode','fundingAmount','agencyCode','investmentType','agencyProjectId','projectName','projectGoal','softwareProject']]
    # df.to_csv("chk.csv")

    docs=read_docs("Project.docx")
    prompt = [
        {
            "role": "system",
            "content": f""" You are a business analyst for a company. I will provide you with the two things a dataframe that contains information about the 50 future projects and a file that contains the information of projects your company has done.
            You role is to analyze the projects file which contains information about which projects your company has done and then look at the future projects in the dataframe and find out which projects your company can do based on the projects your company has already done.
            After looking at both the files return the list of five projects that company can do. 
            i) You won't have any more information about the future projects that will be provided to you, you are restricted to tell by analyzing only this provided information. 
            ii) If some projects have repeating information in their columns then choose from them which will have the highest fundingAmount.
            iii) Don't provide the projects which have almost identical or repeating information in their columns, provide only one from those. Exclude the repeating one from your list and choose some other one.
            Here is the Company's Project File which company has done:
            {docs}.
            Provide the row number of returned projects and their details seperately including parentUII number.
            """,
        },
        {
            "role":"user",
            "content":f""" Here is the Future Projects Dataframe:
            {df}.
            """
            
        }
    ]
    return prompt

class Chatbot:
    def __init__(self):
        self.messages = Initial_prompt()

    def create_chat_completion(self):

        retry_attempts = 3
        retry_delay = 5  # delay in seconds

        for attempt in range(retry_attempts):
            try:
                chat_completion_resp = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=self.messages,
                    temperature=0.3,  # noqa
                )
                # if request is successful, break out of loop
                break
            except:  # noqa
                if attempt + 1 == retry_attempts:
                    logging.info("Attempt failed due to openai server")
                    return {
                        "role": "assistant",
                        "content": "Open Attempt Failed",
                    }
                time.sleep(retry_delay)  # wait before retrying

        message_content = chat_completion_resp["choices"][0]["message"][
            "content"
        ]  # noqa
        role = chat_completion_resp["choices"][0]["message"]["role"]


        response_dict = {"role": role, "content": message_content}

        return message_content

                                                                                 

bot=Chatbot()

message=bot.create_chat_completion()
print(message)


# In[ ]:




