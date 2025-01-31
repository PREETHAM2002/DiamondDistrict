from fastapi import FastAPI, HTTPException
import pandas as pd

app = FastAPI()

# Load Excel file
EXCEL_FILE = "teams.xlsx"

def get_whatsapp_link(name: str):
    """Read Excel file and get WhatsApp link for the given team/player."""
    try:
        df = pd.read_excel(EXCEL_FILE)
        match = df[df["Team/Player"].str.lower() == name.lower()]
        if not match.empty:
            return match.iloc[0]["WhatsApp Link"]
        else:
            return None
    except Exception as e:
        print(f"Error reading Excel: {e}")
        return None

@app.get("/")
def home():
    return {"message": "Welcome to FanPage API!"}

@app.get("/get_whatsapp_link/{name}")
def get_link(name: str):
    """Fetch WhatsApp link for a team or player."""
    link = get_whatsapp_link(name)
    if link:
        return {"team/player": name, "whatsapp_link": link}
    else:
        raise HTTPException(status_code=404, detail="Team or Player not found")
