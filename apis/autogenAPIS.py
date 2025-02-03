import pandas as pd
from fastapi import File, UploadFile,HTTPException,APIRouter
from Utils.Utils import Utils
from Utils.Constants import Constants
from Utils.promptUtils import PromptsConfig
from autogenUtils.Agents import Agents
from autogenUtils.chatUtils import *
from datetime import datetime, timedelta
from fastapi import Query
from tools.ExtractTools import *
autogenapisrouter=APIRouter(tags=["Question and Extract"])



@autogenapisrouter.post("/answer")
async def agent(question:str,context:str):
    """Ask a question to the AI model."""
    accumulator={}
    agentSetup=Agents(user_proxy_args=PromptsConfig.userProxyArgs,assistant_proxy_args=PromptsConfig.assistantProxyArgs)
    response=agentSetup.agentChat(tools=[get_team_logo_internal,get_player_headshot_internal,get_sports_internal,get_leagues_internal,get_seasons_internal,get_teams_internal],question=question,accumulator=accumulator)
    chatHistory=response.chat_history
    cost=response.cost
    chatHistory,response=chatUtils.extract_thought_process(chatHistory)
    return {"thoughts":chatHistory,"cost":cost,"response":response,"accumulated_content":accumulator}

