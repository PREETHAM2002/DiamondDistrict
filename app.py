from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from io import BytesIO
import os
from dotenv import load_dotenv, dotenv_values 
import google.generativeai as genai
from pathlib import Path
import uvicorn
import time
import traceback
import logging
from BaseModels import  *

load_dotenv() 

# accessing and printing value
api_key=os.getenv("API_KEY")
genai.configure(api_key=api_key)
app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Welcome to the Diamond District"}




# Define the directory to save uploaded files
UPLOAD_DIRECTORY = Path("uploaded_videos")
UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)

@app.post("/upload-files/")
async def upload_video(files: List[UploadFile] = File(...)):
    uploaded_files_info = []

    for file in files:
        file_path = UPLOAD_DIRECTORY / file.filename
        try:
            # Save the file to the server might not be needed first draft
            with open(file_path, "wb") as buffer:
                buffer.write(await file.read())
            
            print(f"Uploading file: {file.filename}")
            video_file = genai.upload_file(path=file_path)  # Assuming genai is the client for uploading
            
            print(f"Completed upload: {video_file.uri}")

            while video_file.state.name == "PROCESSING":
                print('.', end='')
                time.sleep(10)
                video_file = genai.get_file(video_file.name)

            if video_file.state.name == "FAILED":
                raise ValueError(f"Upload failed for file {file.filename}: {video_file.state.name}")
            
            # Collect file info
            uploaded_files_info.append({
                "filename": video_file.name,
                "uri": video_file.uri
            })

        except Exception as e:
            # Return a failure response for the current file and move to the next one
            uploaded_files_info.append({
                "filename": file.filename,
                "error": f"Error: {str(e)}"
            })

    # Return a JSON response with information about all files
    return JSONResponse(
        content={
            "message": "Files upload process completed.",
            "uploaded_files": uploaded_files_info
        },
        status_code=200
    )

@app.delete("/delete/{filename}")
async def delete_file(filename:str):
    try:
        genai.delete_file(filename)
        print(f'Deleted file {filename}')
        return JSONResponse(content={"message":f"The file {filename} deleted successfully"},status_code=200)
    except Exception as e:
        logging.exception(str(traceback.format_exc()))
        return JSONResponse(content={"message":f"There were issues while deleting the file {filename}"},status_code=221)
    

@app.post("/generate/")
async def generate_content(files:FileNames,model:Model,prompt:str=None):
    try:
        files=files.model_dump()['files']
        # Set the model to Gemini 1.5 Pro.
        model=model.model_dump()['model_name']
        contents=[]
        if files:
            for i in files:
                contents.append(genai.get_file(i))
        if prompt:
            contents.append(prompt)
        model = genai.GenerativeModel(model_name=f"models/{model}")
        
        # Make the LLM request.
        print("Making LLM inference request...")
        response = model.generate_content(contents,
                                        request_options={"timeout": 600})
        print(response.text)   

        return JSONResponse(content={"message":f"{response.text}"},status_code=200) 
    except Exception as e:
        logging.exception(str(traceback.format_exc()))
        return JSONResponse(content={"message":f"There were issues while generating the response "},status_code=222)

@app.post("/delete/all/")
async def delete_all():
    try:

        docs=list(genai.list_files())
        for i in docs:
            genai.delete_file(i)
        return JSONResponse(content={"message":f"All the files were successfully deleted"},status_code=200)
    
    except Exception as e:
        return JSONResponse(content={"message":f"There were some issues while deleting the files"},status_code=223)
    
@app.get("/files/all")
async def get_all():
    try:

        docs=list(genai.list_files())
        return JSONResponse(content={"message":docs},status_code=200)
    except Exception as e:
        logging.exception(str(traceback.format_exc()))
        return JSONResponse(content={"message":"There were some issues while retrieving the file names"},status_code=224)
    

    




    

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
