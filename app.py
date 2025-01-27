from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
from typing import List, Optional
import os
import time
import json
import cv2
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("Please provide a valid Google Gemini API key.")

# Initialize the GenAI client
client = genai.Client(api_key=GOOGLE_API_KEY)
MODEL_ID = "gemini-2.0-flash-exp"

# Initialize FastAPI app
app = FastAPI()

# Folders for videos
INPUT_FOLDER = "./input_videos"
OUTPUT_FOLDER = "./output_videos"

# Ensure folders exist
os.makedirs(INPUT_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


# Helper Functions
def upload_video(file_path: str):
    video_path = Path(file_path)

    if not video_path.exists():
        raise FileNotFoundError(f"File not found: {video_path}")

    file_upload = client.files.upload(path=video_path)

    while file_upload.state == "PROCESSING":
        time.sleep(10)
        file_upload = client.files.get(name=file_upload.name)

    if file_upload.state == "FAILED":
        raise ValueError("Video processing failed.")

    return file_upload


def clean_and_save_json(raw_response: str):
    try:
        cleaned_response = raw_response.strip("```").strip()
        if cleaned_response.startswith("json"):
            cleaned_response = cleaned_response[4:].strip()

        result = json.loads(cleaned_response)

        if not isinstance(result, dict) or "moments" not in result:
            raise ValueError("Invalid JSON structure. Expected a dictionary with a 'moments' key.")

        return result
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON parsing error: {e}")


def analyze_video(file_upload, user_prompt: str, system_prompt: str):
    response = client.models.generate_content(
        model=MODEL_ID,
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part.from_uri(
                        file_uri=file_upload.uri,
                        mime_type=file_upload.mime_type
                    )
                ]
            ),
            user_prompt,
        ],
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.5,
        ),
    )

    return clean_and_save_json(response.text)


def convert_time_to_seconds(time_str):
    minutes, seconds = time_str.split(":")
    return int(minutes) * 60 + float(seconds)


def split_video(input_video_path, timestamps, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    if not isinstance(timestamps, dict) or "moments" not in timestamps:
        raise ValueError("Invalid timestamps structure. Expected a dictionary with a 'moments' key.")

    moments = timestamps["moments"]
    if not isinstance(moments, list):
        raise ValueError("'moments' should be a list of timestamp dictionaries.")

    video = cv2.VideoCapture(input_video_path)
    fps = video.get(cv2.CAP_PROP_FPS)
    chunks = []

    for i, segment in enumerate(moments):
        start_time = segment['start_time']
        end_time = segment['end_time']

        start_time_seconds = convert_time_to_seconds(start_time)
        end_time_seconds = convert_time_to_seconds(end_time)

        start_frame = int(start_time_seconds * fps)
        end_frame = int(end_time_seconds * fps)

        output_file = os.path.join(output_folder, f"chunk_{i + 1}.mp4")
        chunks.append(output_file)

        video.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        writer = None

        for frame_number in range(start_frame, end_frame):
            ret, frame = video.read()
            if not ret:
                break
            if writer is None:
                height, width, _ = frame.shape
                writer = cv2.VideoWriter(
                    output_file,
                    cv2.VideoWriter_fourcc(*'mp4v'),
                    fps,
                    (width, height)
                )
            writer.write(frame)

        if writer:
            writer.release()

    video.release()
    return chunks


def merge_videos(chunks, output_file, fps):
    # Initialize the video writer with the first chunk to get dimensions
    first_chunk = cv2.VideoCapture(chunks[0])
    ret, frame = first_chunk.read()

    if not ret:
        raise ValueError("Failed to read the first chunk of the video.")

    height, width, _ = frame.shape
    writer = cv2.VideoWriter(output_file, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))

    # Write frames from each chunk into the output file
    for chunk in chunks:
        video = cv2.VideoCapture(chunk)
        while True:
            ret, frame = video.read()
            if not ret:
                break
            writer.write(frame)
        video.release()

    writer.release()
    first_chunk.release()


@app.post("/upload")
async def upload_endpoint(video: UploadFile):
    # Save uploaded video to the input folder
    video_path = os.path.join(INPUT_FOLDER, video.filename)
    with open(video_path, "wb") as f:
        f.write(await video.read())
    return {"message": f"Video {video.filename} uploaded successfully to {INPUT_FOLDER}"}


@app.post("/analyze")
async def analyze_endpoint(
    player_name: str = Form(None),
    team_name: Optional[str] = Form(None),
    genre: Optional[str] = Form(None),
    video_filename: str = Form(...)
):
    # Get video path from input folder
    video_path = os.path.join(INPUT_FOLDER, video_filename)

    if not os.path.exists(video_path):
        return JSONResponse({"error": f"Video '{video_filename}' not found in input folder."}, status_code=404)

    # Construct prompts
    SYSTEM_PROMPT = (
        "Analyze the video to identify key moments for the given player, team, and genre. "
        "Return a JSON object with moments containing start and end timestamps. "
        "Example: { \"moments\": [{ \"moment\": \"At bat, hits one on the ground\", \"start_time\": \"0:40\", \"end_time\": \"0:48\" }]}"
    )
    USER_PROMPT = (
        f"Identify key moments for player '{player_name or 'N/A'}', "
        f"team '{team_name or 'N/A'}', and genre '{genre or 'N/A'}'. "
    )

    try:
        uploaded_file = upload_video(video_path)
        timestamps = analyze_video(uploaded_file, USER_PROMPT, SYSTEM_PROMPT)

        # Split video
        output_chunks_folder = os.path.join(OUTPUT_FOLDER, video_filename.split('.')[0])
        chunks = split_video(video_path, timestamps, output_chunks_folder)

        # Merge the chunks into one video
        output_merged_file = os.path.join(OUTPUT_FOLDER, f"{video_filename.split('.')[0]}_merged.mp4")
        video = cv2.VideoCapture(chunks[0])  # Get FPS from the first chunk
        fps = video.get(cv2.CAP_PROP_FPS)
        merge_videos(chunks, output_merged_file, fps)

        # Optionally remove the chunks after merging
        for chunk in chunks:
            os.remove(chunk)

        return {
            "message": "Video analyzed, processed, and merged successfully.",
            "timestamps": timestamps,
            "chunks": chunks,
            "output_merged_file": output_merged_file
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/videos")
async def list_videos():
    videos = os.listdir(INPUT_FOLDER)
    return {"videos": videos}


@app.delete("/videos/{filename}")
async def delete_video(filename: str):
    video_path = os.path.join(INPUT_FOLDER, filename)
    if os.path.exists(video_path):
        os.remove(video_path)
        return {"message": f"Video '{filename}' deleted successfully from input folder."}
    else:
        return JSONResponse({"error": f"Video '{filename}' not found."}, status_code=404)


@app.get("/download/{file_path}")
async def download_file(file_path: str):
    full_path = os.path.join(OUTPUT_FOLDER, file_path)
    if os.path.exists(full_path):
        return FileResponse(full_path, media_type='application/octet-stream', filename=file_path)
    else:
        return JSONResponse({"error": f"File '{file_path}' not found."}, status_code=404)


# from fastapi import FastAPI, UploadFile, Form
# from fastapi.responses import FileResponse, JSONResponse
# from pathlib import Path
# from typing import List
# import os
# import time
# import json
# import cv2
# from google import genai
# from google.genai import types
# from dotenv import load_dotenv

# # Load environment variables
# load_dotenv()
# GOOGLE_API_KEY = os.getenv("API_KEY")
# if not GOOGLE_API_KEY:
#     raise ValueError("Please provide a valid Google Gemini API key.")

# # Initialize the GenAI client
# client = genai.Client(api_key=GOOGLE_API_KEY)
# MODEL_ID = "gemini-2.0-flash-exp"

# # Initialize FastAPI app
# app = FastAPI()

# # Helper Functions
# def upload_video(file_path: str):
#     video_path = Path(file_path)

#     if not video_path.exists():
#         raise FileNotFoundError(f"File not found: {video_path}")

#     file_upload = client.files.upload(path=video_path)

#     while file_upload.state == "PROCESSING":
#         time.sleep(10)
#         file_upload = client.files.get(name=file_upload.name)

#     if file_upload.state == "FAILED":
#         raise ValueError("Video processing failed.")

#     return file_upload

# def clean_and_save_json(raw_response: str):
#     try:
#         cleaned_response = raw_response.strip("```").strip()
#         if cleaned_response.startswith("json"):
#             cleaned_response = cleaned_response[4:].strip()

#         return json.loads(cleaned_response)
#     except json.JSONDecodeError as e:
#         raise ValueError(f"Invalid JSON format: {e}")

# def analyze_video(file_upload, user_prompt: str, system_prompt: str):
#     response = client.models.generate_content(
#         model=MODEL_ID,
#         contents=[
#             types.Content(
#                 role="user",
#                 parts=[
#                     types.Part.from_uri(
#                         file_uri=file_upload.uri,
#                         mime_type=file_upload.mime_type
#                     )
#                 ]
#             ),
#             user_prompt,
#         ],
#         config=types.GenerateContentConfig(
#             system_instruction=system_prompt,
#             temperature=0.5,
#         ),
#     )

#     return clean_and_save_json(response.text)

# def convert_time_to_seconds(time_str):
#     minutes, seconds = time_str.split(":")
#     return int(minutes) * 60 + float(seconds)

# def split_video(input_video_path, timestamps, output_folder):
#     if not os.path.exists(output_folder):
#         os.makedirs(output_folder)

#     video = cv2.VideoCapture(input_video_path)
#     fps = video.get(cv2.CAP_PROP_FPS)
#     chunks = []

#     for i, segment in enumerate(timestamps["moments"]):
#         start_time = segment['start_time']
#         end_time = segment['end_time']

#         start_time_seconds = convert_time_to_seconds(start_time)
#         end_time_seconds = convert_time_to_seconds(end_time)

#         start_frame = int(start_time_seconds * fps)
#         end_frame = int(end_time_seconds * fps)

#         output_file = os.path.join(output_folder, f"chunk_{i + 1}.mp4")
#         chunks.append(output_file)

#         video.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
#         writer = None

#         for frame_number in range(start_frame, end_frame):
#             ret, frame = video.read()
#             if not ret:
#                 break
#             if writer is None:
#                 height, width, _ = frame.shape
#                 writer = cv2.VideoWriter(
#                     output_file,
#                     cv2.VideoWriter_fourcc(*'mp4v'),
#                     fps,
#                     (width, height)
#                 )
#             writer.write(frame)

#         if writer:
#             writer.release()

#     video.release()
#     return chunks

# def merge_videos(chunks, output_file, fps):
#     writer = None
#     for chunk in chunks:
#         video = cv2.VideoCapture(chunk)

#         while True:
#             ret, frame = video.read()
#             if not ret:
#                 break
#             if writer is None:
#                 height, width, _ = frame.shape
#                 writer = cv2.VideoWriter(
#                     output_file,
#                     cv2.VideoWriter_fourcc(*'mp4v'),
#                     fps,
#                     (width, height)
#                 )
#             writer.write(frame)

#         video.release()

#     if writer:
#         writer.release()

# # API Endpoints
# @app.post("/analyze")
# async def analyze_endpoint(video: UploadFile, player_name: str = Form(...)):
#     # Save uploaded video locally
#     input_video_path = f"./{video.filename}"
#     with open(input_video_path, "wb") as f:
#         f.write(await video.read())

#     # Set prompts
#     SYSTEM_PROMPT = (
#         "Given a baseball match video and a player's name, identify the key moments of that player. "
#         "Extract and return the **start and end timestamps** of that moment. "
#         "Example: { \"player\": \"Marte\", \"moments\": [{ \"moment\": \"At bat, hits one on the ground\", \"start_time\": \"0:40\" ,\"end_time\": \"0:48\"}]}"
#     )
#     USER_PROMPT = f"Identify all key highlight moments for the player '{player_name}' in the video. "
#     USER_PROMPT += "Return a JSON object with the player's name, moment and the **start and end timestamps** of their activity."

#     try:
#         uploaded_file = upload_video(input_video_path)

#         # Analyze video
#         timestamps = analyze_video(uploaded_file, USER_PROMPT, SYSTEM_PROMPT)

#         # Split video
#         output_folder = "./video_chunks"
#         chunks = split_video(input_video_path, timestamps, output_folder)

#         # Merge video
#         output_merged_file = "merged_video.mp4"
#         video = cv2.VideoCapture(input_video_path)
#         fps = video.get(cv2.CAP_PROP_FPS)
#         merge_videos(chunks, output_merged_file, fps)

#         # Return response
#         return JSONResponse({
#             "message": "Video analyzed and processed successfully.",
#             "timestamps": timestamps,
#             "merged_video_path": output_merged_file,
#             "chunks": chunks
#         })

#     except Exception as e:
#         return JSONResponse({"error": str(e)}, status_code=500)

# @app.get("/download/{file_path}")
# async def download_file(file_path: str):
#     return FileResponse(file_path, media_type='application/octet-stream', filename=file_path)
