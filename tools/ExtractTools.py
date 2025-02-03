import requests


from fastapi import HTTPException
import config
from Utils.Utils import Utils

def get_team_logo_internal(team_id: int, accumulator: dict = None):
    """
    Internal function to fetch the logo of a specific team.
    
    Args:
        team_id (int): The ID of the team whose logo is to be fetched.
        accumulator (dict, optional): A dictionary to accumulate data or logs across requests.
        
    Returns:
        dict: A dictionary containing the logo URL or error information.
    """
    if accumulator is None:
        accumulator = {}

    try:
        url = f"{config.BASE_LOGO_URL}/{team_id}.svg"
        image = Utils.fetch_image(url)
        
        # Optionally, accumulate the logo URL for logging or other purposes
        accumulator["last_fetched_logo"] = image
        
        return {"team_id": team_id, "logo_url": url}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching team logo: {str(e)}")

def get_player_headshot_internal(player_id: int, accumulator: dict = None):
    """
    Internal function to fetch the headshot of a specific player.
    
    Args:
        player_id (int): The ID of the player whose headshot is to be fetched.
        accumulator (dict, optional): A dictionary to accumulate data or logs across requests.
        
    Returns:
        dict: A dictionary containing the headshot URL or error information.
    """
    if accumulator is None:
        accumulator = {}

    try:
        url = f"{config.BASE_HEADSHOT_URL}/{player_id}.jpg"
        image = Utils.fetch_image(url)
        
        # Optionally, accumulate the headshot URL for logging or other purposes
        accumulator["last_fetched_headshot"] = url
        
        return {"player_id": player_id, "headshot_url": url}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching player headshot: {str(e)}")

def get_sports_internal(accumulator: dict = None):
    """
    Internal function to fetch all sports.
    
    Args:
        accumulator (dict, optional): A dictionary to accumulate data or logs across requests.
        
    Returns:
        list: A list of sports.
    """
    if accumulator is None:
        accumulator = {}

    try:
        endpoint = f"{config.BASE_URL}/sports"
        data = Utils.fetch_data(endpoint)
        
        # Optionally, accumulate sports data for logging or other purposes
        accumulator["sports_data_fetched"] = data.get("sports", [])
        
        return data.get("sports", [])
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching sports data: {str(e)}")

def get_leagues_internal(sport_id: int = None, accumulator: dict = None):
    """
    Internal function to fetch all leagues, optionally filtered by sport ID.
    
    Args:
        sport_id (int, optional): The sport ID to filter leagues by.
        accumulator (dict, optional): A dictionary to accumulate data or logs across requests.
        
    Returns:
        list: A list of leagues.
    """
    if accumulator is None:
        accumulator = {}

    try:
        endpoint = f"{config.BASE_URL}/league"
        if sport_id:
            endpoint += f"?sportId={sport_id}"
        
        data = Utils.fetch_data(endpoint)
        
        # Optionally, accumulate leagues data for logging or other purposes
        accumulator["leagues_data_fetched"] = data.get("leagues", [])
        
        return data.get("leagues", [])
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching leagues data: {str(e)}")

def get_seasons_internal(sport_id: int = None, accumulator: dict = None):
    """
    Internal function to fetch all seasons, optionally filtered by sport ID.
    
    Args:
        sport_id (int, optional): The sport ID to filter seasons by.
        accumulator (dict, optional): A dictionary to accumulate data or logs across requests.
        
    Returns:
        list: A list of seasons.
    """
    if accumulator is None:
        accumulator = {}

    try:
        endpoint = f"{config.BASE_SEASON_URL}/all?sportId={sport_id}"
        data = Utils.fetch_data(endpoint)
        
        # Optionally, accumulate seasons data for logging or other purposes
        accumulator["seasons_data_fetched"] = data.get("seasons", [])
        
        return data.get("seasons", [])
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching seasons data: {str(e)}")

def get_teams_internal(sport_id: int = None, accumulator: dict = None):
    """
    Internal function to fetch all teams, optionally filtered by sport ID.
    
    Args:
        sport_id (int, optional): The sport ID to filter teams by.
        accumulator (dict, optional): A dictionary to accumulate data or logs across requests.
        
    Returns:
        list: A list of teams.
    """
    if accumulator is None:
        accumulator = {}

    try:
        endpoint = f"{config.BASE_URL}/teams"
        if sport_id:
            endpoint += f"?sportId={sport_id}"
        
        data = Utils.fetch_data(endpoint)
        
        # Optionally, accumulate teams data for logging or other purposes
        accumulator["teams_data_fetched"] = data.get("teams", [])
        
        return data.get("teams", [])
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching teams data: {str(e)}")

def get_team_roster_internal(team_id: int, season: int, accumulator: dict = None):
    """
    Internal function to fetch the roster of a specific team for a given season.
    
    Args:
        team_id (int): The ID of the team whose roster is to be fetched.
        season (int): The season year.
        accumulator (dict, optional): A dictionary to accumulate data or logs across requests.
        
    Returns:
        list: A list of team members (roster).
    """
    if accumulator is None:
        accumulator = {}

    try:
        endpoint = f"{config.BASE_URL}/teams/{team_id}/roster?season={season}"
        data = Utils.fetch_data(endpoint)
        
        # Optionally, accumulate roster data for logging or other purposes
        accumulator["team_roster_data_fetched"] = data.get("roster", [])
        
        return data.get("roster", [])
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching team roster: {str(e)}")

def get_players_internal(season: int, accumulator: dict = None):
    """
    Internal function to fetch all players for a specific season.
    
    Args:
        season (int): The season year.
        accumulator (dict, optional): A dictionary to accumulate data or logs across requests.
        
    Returns:
        list: A list of players.
    """
    if accumulator is None:
        accumulator = {}

    try:
        endpoint = f"{config.BASE_URL}/players?season={season}"
        data = Utils.fetch_data(endpoint)
        
        # Optionally, accumulate player data for logging or other purposes
        accumulator["players_data_fetched"] = data.get("players", [])
        
        return data.get("players", [])
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching players data: {str(e)}")
