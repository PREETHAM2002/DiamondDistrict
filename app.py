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
from google.cloud import texttospeech
import subprocess  # NEW IMPORT

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("Please provide a valid Google Gemini API key.")

# Initialize the GenAI client
client = genai.Client(api_key=GOOGLE_API_KEY)
MODEL_ID = "gemini-2.0-flash-exp"

# Initialize TTS client
if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
    raise ValueError("Please set GOOGLE_APPLICATION_CREDENTIALS environment variable for Text-to-Speech.")
TTS_CLIENT = texttospeech.TextToSpeechClient()

# Initialize FastAPI app
app = FastAPI()

# Folders for videos
INPUT_FOLDER = "./input_videos"
OUTPUT_FOLDER = "./output_videos"

# Ensure folders exist
os.makedirs(INPUT_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


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
    first_chunk = cv2.VideoCapture(chunks[0])
    ret, frame = first_chunk.read()
    if not ret:
        raise ValueError("Failed to read the first chunk of the video.")
    height, width, _ = frame.shape
    writer = cv2.VideoWriter(output_file, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))
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


def generate_video_commentary(file_upload):
    """Generate interactive friendly  commentary for  the given video"""
    try:
        print("\n=== STARTING COMMENTARY GENERATION ===")
        
        # Generate the response
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_uri(
                            file_uri=file_upload.uri,
                            mime_type=file_upload.mime_type
                        ),
                        types.Part.from_text(
                            "Generate interactive friendly  commentary for  the given video(analysing with players name  and wow moments)"
                            "Return ONLY a JSON array with time_seconds (float) and text (string) fields. "
                            "Format example: [{\"time_seconds\": 0.0, \"text\": \"...\"}, ...]"
                        )
                    ]
                )
            ],
            config=types.GenerateContentConfig(temperature=0.7),
        )
        
        # Get and log raw response
        raw_text = response.text
        print(f"\n=== RAW GENAI RESPONSE ===\n{raw_text}\n{'-'*50}")
        
        # Clean response with multiple fallbacks
        cleaned = raw_text.strip()
        clean_attempts = [
            lambda t: t.replace("```json", "").replace("```", ""),
            lambda t: t[t.find('['):t.rfind(']')+1],
            lambda t: t.replace("'", '"'),
            lambda t: t.replace("\\", "")
        ]
        
        for attempt in clean_attempts:
            try:
                cleaned = attempt(cleaned)
                commentary = json.loads(cleaned)
                break
            except json.JSONDecodeError:
                continue
        
        # Final validation
        if not isinstance(commentary, list):
            raise ValueError("Top-level structure should be a list")
            
        for i, entry in enumerate(commentary):
            if not isinstance(entry, dict):
                raise ValueError(f"Entry {i} is not a dictionary")
            missing = [k for k in ['time_seconds', 'text'] if k not in entry]
            if missing:
                raise ValueError(f"Entry {i} missing fields: {missing}")
                
        print("\n=== VALID COMMENTARY ===")
        print(json.dumps(commentary, indent=2, ensure_ascii=False))
        
        return commentary
        
    except Exception as e:
        print(f"\n=== CRITICAL ERROR ===")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        print(f"Cleaned Text Length: {len(cleaned) if 'cleaned' in locals() else 0}")
        print(f"Partial Cleaned Text (500 chars): {cleaned[:500] if 'cleaned' in locals() else ''}")
        
        raise ValueError(f"Commentary generation failed: {str(e)}\n"
                        f"Partial Response: {cleaned[:500] if 'cleaned' in locals() else 'N/A'}")
    

def generate_commentary_audio(commentary, output_path, language: str = "en", gender: str = "female"):
    """Convert commentary text to audio using Google TTS with language and gender options"""
    try:
        # NEW: Language and voice mapping
        voice_config = {
            "en": {
                "female": "en-US-Standard-C",
                "male": "en-US-Standard-B"
            },
            "ja": {
                "female": "ja-JP-Standard-A",
                "male": "ja-JP-Standard-B"
            },
            "es": {
                "female": "es-ES-Standard-A",
                "male": "es-ES-Standard-B"
            }
        }

        # Validate language input
        lang_code = language.lower()[:2]
        if lang_code not in voice_config:
            raise ValueError(f"Unsupported language: {language}. Supported options: en, ja, es")

        # Validate gender input
        gender = gender.lower()
        if gender not in ["male", "female"]:
            raise ValueError("Gender must be 'male' or 'female'")

        # Get voice parameters
        voice_name = voice_config[lang_code][gender]
        language_code = {
            "en": "en-US",
            "ja": "ja-JP",
            "es": "es-ES"
        }[lang_code]

        # Combine commentary text
        full_text = " ".join([entry['text'] for entry in commentary])

        # Generate audio
        synthesis_input = texttospeech.SynthesisInput(text=full_text)
        voice = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            name=voice_name,
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE if gender == "female" else texttospeech.SsmlVoiceGender.MALE
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        response = TTS_CLIENT.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )

        with open(output_path, "wb") as out:
            out.write(response.audio_content)
            
        return output_path
            
    except Exception as e:
        raise ValueError(f"Audio generation failed: {str(e)}")

# NEW FUNCTION: Merge audio and video using ffmpeg
def merge_audio_with_video(video_path: str, audio_path: str, output_path: str):
    try:
        command = [
            'ffmpeg',
            '-y',  # overwrite output file if it exists
            '-i', video_path,
            '-i', audio_path,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-strict', 'experimental',
            '-shortest',
            output_path
        ]
        subprocess.run(command, check=True, capture_output=True)
        return output_path
    except subprocess.CalledProcessError as e:
        raise ValueError(f"FFmpeg error: {e.stderr.decode()}")


@app.post("/analyze")
async def analyze_endpoint(
    player_name: str = Form(None),
    team_name: Optional[str] = Form(None),
    genre: Optional[str] = Form(None),
    video_filename: str = Form(...),
    language: str = Form("en"),  # NEW PARAMETER
    gender: str = Form("female")  # NEW PARAMETER
):
    video_path = os.path.join(INPUT_FOLDER, video_filename)
    if not os.path.exists(video_path):
        return JSONResponse({"error": f"Video '{video_filename}' not found in input folder."}, status_code=404)

    try:
        # Existing video processing logic
        uploaded_file = upload_video(video_path)
        SYSTEM_PROMPT = (
            "Analyze the video to identify key or wow  moments of only the given player, team, or genre. "
            "Return a JSON object with moments containing start and end timestamps. "
            "Example: { \"moments\": [{ \"moment\": \"At bat, hits one on the ground\", \"start_time\": \"0:40\", \"end_time\": \"0:48\" }]}"
        )
        USER_PROMPT = (
            f"Identify key moments for player '{player_name or 'N/A'}', "
            f"team '{team_name or 'N/A'}', and genre '{genre or 'N/A'}'. "
        )
        timestamps = analyze_video(uploaded_file, USER_PROMPT, SYSTEM_PROMPT)
        
        output_chunks_folder = os.path.join(OUTPUT_FOLDER, video_filename.split('.')[0])
        chunks = split_video(video_path, timestamps, output_chunks_folder)
        
        output_merged_file = os.path.join(OUTPUT_FOLDER, f"{video_filename.split('.')[0]}_merged.mp4")
        video = cv2.VideoCapture(chunks[0])
        fps = video.get(cv2.CAP_PROP_FPS)
        merge_videos(chunks, output_merged_file, fps)
        video.release()

        # Generate commentary and audio
        merged_upload = upload_video(output_merged_file)
        commentary = generate_video_commentary(merged_upload)
        
        # Generate audio with language and gender options
        audio_filename = f"{video_filename.split('.')[0]}_commentary.mp3"
        audio_path = os.path.join(OUTPUT_FOLDER, audio_filename)
        generate_commentary_audio(commentary, audio_path, language, gender)

        # NEW: Merge audio with video
        final_output = os.path.join(OUTPUT_FOLDER, f"{video_filename.split('.')[0]}_final.mp4")
        merge_audio_with_video(output_merged_file, audio_path, final_output)

        # Cleanup intermediate files
        for chunk in chunks:
            if os.path.exists(chunk):
                os.remove(chunk)
        if os.path.exists(audio_path):
            os.remove(audio_path)
        if os.path.exists(output_merged_file):
            os.remove(output_merged_file)

        return {
        "message": "Video processed successfully with audio commentary",
        "timestamps": timestamps,
        "commentary": commentary,
        "merged_video": output_merged_file,  # Video without audio
        "commentary_audio": audio_path,      # Separate audio file
        "final_video": final_output          # Combined video+audio
}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/upload")
async def upload_endpoint(video: UploadFile):
    video_path = os.path.join(INPUT_FOLDER, video.filename)
    with open(video_path, "wb") as f:
        f.write(await video.read())
    return {"message": f"Video {video.filename} uploaded successfully to {INPUT_FOLDER}"}

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

