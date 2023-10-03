import pandas as pd
import os
import time
import docx2txt
import logging
import openai
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
    def __init__(self,pdf_file_path,uuid_value):
        self.pdf_file_path=pdf_file_path
        self.uuid=uuid_value
        self.messages = self.Initial_prompt()

    def Initial_prompt(self):

        business_case=get_pdf_content(self.pdf_file_path)
        # docss=self.read_docs("app/files/project.docx")
        # doks=self.read_docs("app/files/project2.docx")
        
        # docs=f"\nProject 1: {docss}.\n Project 2: {doks}.\n"

        try:
            docs = self.read_docs("app/files/past_project.docx")
        except FileNotFoundError:
            try:
                docs = get_pdf_content("app/files/past_project.pdf")
            except FileNotFoundError:
                return "file_error"
        except Exception as e:
            # Handle other exceptions differently if you want
            print(f"An unexpected error occurred: {e}")

        # print(doks)
        try:
            investment_historic = pd.read_excel(f'app/files/investment-spending-historic_{self.uuid}.xlsx')
            investment_spending = pd.read_excel(f'app/files/investment-spending_{self.uuid}.xlsx')
            business_case=business_case+f"Investment Spending Details:\n {investment_spending}\n"+f"Historic Investment Spending: \n {investment_historic}\n"
            # print(future_project)
            # print(f"Excel file for uuid: {self.uuid} Loaded")
        except:
            pass
        prompt = [
            {
            "role": "system",
            "content": f"""You are a business analyst for a highly adaptable and innovative company. You will be provided with two files: one containing information about past projects your company has successfully completed and the other containing potential future project.
            Your primary objective is to carefully analyze both sets of information. Identify the projects from the future project file that align with your company's strengths and expertise. Focus on creating proposals for projects where your company can excel.
            Even in cases where your company may not have prior domain-specific experts, emphasize our adaptability and commitment to finding solutions. Avoid mentioning limitations and instead focus on the positive aspects of our approach that we will use to complete the future project.
            Please structure your response with the following headings and format:
            1) Name of Agency
            2) Name of project 
            3) Mission purpose of Agency.  (What must this agency accomplish for citizens or other stakeholders?)
            4) Mission purpose of project (How does this project help the Agency accomplish its mission?)
            5) Specific result your company could produce for the project (Not an activity description. This should be a particular mission-related result)
            6) Government budget document (indicate allocated budget)
            7) Reason to not worry about incumbent contractor

            8) How might you add value to the upcoming project? What will be your role?
            9) What similar project have you supported in the past where you added value in a similar way?
            10) What smart stuff did you do on that prior project?  (Make a list)
            11) For each of those smart things you did, what would have gone wrong if you had not done them? (List for each smart thing you did.)
            12) What might go wrong in future project if you don't do the same smart stuff? (List for each smart thing you did.)
            13) What mission goal might not be attained in the future project if you don't do your smart stuff? (List for each smart thing you did.)
            14) Formulate a value assertion based on this model:  If the XYZ agency does not use our smart stuff, they risk not attaining Mission Goal A.
            15) Potential problem. What problem might the project have if you are not involved?
            16) New Project Stakeholders. Who are the stakeholders who will depend on the new project results?
            17) New Project Senior Executive officer. Which government executives officer are most reliant on good project results?
            18) New Project Problem Stakeholder Impact. How will stakeholders and senior executives be affected if the problem occurs?
            19) Past Project. In what past project have you solved or prevented a similar problem?
            20) Past Problem. Had the problem occurred, what exactly would have happened?
            21) Past project villain. What caused this problem?
            22) Past Solution. What solution solved or prevented that problem?
            23) Past project senior executive officer. Who was the most senior executive officer who would have been negatively impacted? 
            24) Past project stakeholders. What stakeholders would have been affected by the problem?
            25) Past project complication. What severe complication might this problem have caused for the senior executive?
	    26) Pain Point. Identify the organizational group that will feel pain if the problem you identified occurs. An organizational chart might help you identify that group.
            27) Phone Number. Find a phone number you might call to get connected to the leader of the Pain Point organization.  This could well be the main switchboard for the organization.  The idea is to speak to a live person who will understand the mission problem you’ve identified, and will help you get connected with someone who can solve it.
            28) Phone Script. Draft the words you will say when someone answers the phone.  
            Always provide brief and detailed answers for all of the questions mentioned above. While Providing responses avoid to tell the risks related to the limited resources, resource constraints or anything related to resources and time.
            Here is the Company's Project File, showcasing our history of past successful projects:
            {docs}.
            """,
      },
      {
        "role": "user",
        "content": f"""Here is the Future Project File:
         {business_case}.
         While Providing responses please avoid to tell the risks related to the limited resources, resource constraints, budget constraints or anything related to resources, skills lack and time constraint.
         """
      }
            ]

        # print(num_tokens_from_string(str(prompt)))

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
                    model="gpt-3.5-turbo-16k",
                    messages=self.messages,
                    temperature=0.7,  # noqa
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

        return message_content


def pick_top_uuids(uuids):
    df = pd.read_csv("app/files/merged.csv")
    
    # Extract unique UUIDs from the dataframe in the order they appear
    unique_uuids_in_df = df[df['parentUII'].isin(uuids)]['parentUII'].drop_duplicates().tolist()

    # Sort uuids based on their appearance order in the dataframe
    sorted_uuids = sorted(uuids, key=lambda x: unique_uuids_in_df.index(x) if x in unique_uuids_in_df else float('inf'))

    return sorted_uuids

def write_proposals(uuid_value):
    # df = pd.read_csv("test/merged.csv")
    # index=1

    # sorted_uuids=pick_top_uuids(uuids)

    filename = f"app/files/Business_case_{uuid_value}.pdf"
    
    # title = df[df['parentUII'] == uuid_value]['parentInvestmentTitle'].iloc[0]
    # filename2 = f"test/files/{title}.pdf"

    # Check if the file exists
    if os.path.exists(filename):

        bot=Chatbot(filename,uuid_value)
        # print(f"\n<<<<<<<<<<<<<<<<<<<<<<<<<<<< Here Is The Project Below >>>>>>>>>>>>>>>>>>>>>>>>>>>>\n")
        message=bot.create_chat_completion()

        if message=="file_error":
            return "Please Upload Past Project File First"

        # print(message,"\n")
        return message
    else:
        # print(f"uuid: {filename} file Not found")
        return f"uuid: {filename} file Not found"
        


write_proposals("015-000200137")
