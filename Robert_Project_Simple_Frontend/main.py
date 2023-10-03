from app.scrape_req import projects,funding_sources
from app.csv_analysis import final_merged_sorted_df_50_tocsv
from app.scrape_business import scrape_business_cases
from app.refind_gen_ai import extract_parentUUI
from app.proposal_chatbot import write_proposals
# from app.google_search import google_search_results
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request
import os, re
import json
import redis

app=FastAPI()

templates = Jinja2Templates(directory="templates")
# Serve static files like CSS or JS if you have any
# app.mount("/static", StaticFiles(directory="static"), name="static")


# Set up Redis connection
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

@app.get("/reset_upload_status/")
async def reset_upload_status():
    redis_client.set("file_uploaded", "false")
    return {"status": "Upload status reset"}

# Utility function to check if a file has been uploaded
def check_file_uploaded():
    return redis_client.get("file_uploaded") == b"true"


@app.post("/upload/")
async def upload_file(file: UploadFile):
    # Check for valid file extensions
    if file.filename.endswith(".pdf"):
        extension = ".pdf"
    elif file.filename.endswith(".docx"):
        extension = ".docx"
    else:
        raise HTTPException(status_code=400, detail="Invalid file type")

    # Save the file with the new filename
    new_filename = "past_project" + extension
    file_path = os.path.join("app/files", new_filename)

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    redis_client.set("file_uploaded", "true")
    return "File Saved Successfully"


@app.post("/download_projects")
async def download_projects_endpoint():
    if not check_file_uploaded():
        return "Please upload a Past Project file first."
    try:
        projects()
        return {"status": projects()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/download_funding")
async def download_funding_endpoint():
    if not check_file_uploaded():
        return "Please upload a Past Project file first."
    try:
        return {"status": funding_sources()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/make_top_project_list_csv")
async def make_merged_csv():
    if not check_file_uploaded():
        return "Please upload a Past Project file first."
    try:
        final_merged_sorted_df_50_tocsv()
        return {"status": "Top Projects File Created Successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


    
@app.post("/get_relevent_five_projects")
async def get_relevent_five_projects():
    if not check_file_uploaded():
        return "Please upload a Past Project file first."
    try:
        parentUUI, projectss = extract_parentUUI()
    except:
        return extract_parentUUI()

    # Serialize the data as JSON
    data = json.dumps({
        "parentUUI": parentUUI,
        "projectss": projectss
    })
    # Store the serialized string in Redis with an expiry of 2 hours (7200 seconds)
    redis_client.set("projectss_key", data, ex=7200)
    return projectss


def retrieve_from_redis():
    # Get the serialized data from Redis
    serialized_data = redis_client.get("projectss_key")
    
    # If there's no data under the given key, return None values
    if serialized_data is None:
        return None, None

    # Deserialize the data
    data = json.loads(serialized_data)
    
    # Extract the parentUUI list and projectss string
    parentUUI = data.get("parentUUI", None)
    projectss = data.get("projectss", None)
    
    return parentUUI, projectss


@app.get("/write_proposal")
def write_proposal(choice:int):
    if not check_file_uploaded():
        return "Please upload a Past Project file first."
    parentUUI, projectss = retrieve_from_redis()

    if  len(projectss)==5:
        while True:
            try:
                # choice = int(choiceut("\nPlease tell which project proposal you want. Choose a number 1-5: "))
                if 1 <= choice <= 5:
                    break
                else:
                    print("Invalid choice. Please choose a number between 1 and 5.")
            except ValueError:
                print("Please enter a valid integer.")
        choice=choice-1
        print(f"\nYou Have Chosen Project:\n {projectss[choice]}.\n Parent UUI: {parentUUI[choice]}")

        scrape_business_cases(parentUUI[choice])
        text= write_proposals(parentUUI[choice])

        # Using regular expression to split the text based on the pattern "n)"
        headings = re.split(r'\d+\)\s*(?=[A-Z])', text)[1:] # [1:] because the first item in the split list will be empty

        # Strip whitespace from each heading and store them in a cleaned list
        cleaned_headings = [heading.strip() for heading in headings]
        # print("\nok",f"\n{cleaned_headings}")
        return cleaned_headings


    else:
        # print(f"PArentUUI list is empty or Projects Split Failed: {len(projectss)}")
        return f"PArentUUI list is empty or Projects Split Failed: {len(projectss)}"


@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})