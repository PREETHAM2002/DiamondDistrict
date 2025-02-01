from fastapi import APIRouter,HTTPException
import config
from Utils.Utils import Utils
from fastapi.responses import StreamingResponse

LeagueRouter=APIRouter(tags=["League"])


@LeagueRouter.get("/team/{team_id}/logo")
def get_team_logo(team_id: int):
    """Fetch and return the logo of a specific team."""
    url = f"{config.BASE_LOGO_URL}/{team_id}.svg"
    image = Utils.fetch_image(url)
    return StreamingResponse(image, media_type="image/svg+xml")

@LeagueRouter.get("/player/{player_id}/headshot")
def get_player_headshot(player_id: int):
    """Fetch and return the headshot of a specific player."""
    url = f"{config.BASE_HEADSHOT_URL}/{player_id}.jpg"
    image = Utils.fetch_image(url)
    return StreamingResponse(image, media_type="image/png")







@LeagueRouter.get("/sports")
def get_sports():
    """Fetch all sports."""
    endpoint = f"{config.BASE_URL}/sports"
    data = Utils.fetch_data(endpoint)
    return data.get("sports", [])

@LeagueRouter.get("/leagues")
def get_leagues(sport_id: int = None):
    """Fetch leagues, optionally filtered by sport ID."""
    endpoint = f"{config.BASE_URL}/league"
    if sport_id:
        endpoint += f"?sportId={sport_id}"
    data = Utils.fetch_data(endpoint)
    return data.get("leagues", [])

@LeagueRouter.get("/seasons")
def get_seasons(sport_id: int = None):
    """Fetch all seasons."""
    endpoint = f"{config.BASE_SEASON_URL}/all?sportId={sport_id}"
    data = Utils.fetch_data(endpoint)
    return data.get("seasons", [])

@LeagueRouter.get("/teams")
def get_teams(sport_id: int = None):
    """Fetch teams, optionally filtered by sport ID."""
    endpoint = f"{config.BASE_URL}/teams"
    if sport_id:
        endpoint += f"?sportId={sport_id}"
    data = Utils.fetch_data(endpoint)
    return data.get("teams", [])

@LeagueRouter.get("/team/{team_id}/logo")
def get_team_logo(team_id: int):
    """Fetch the logo URL for a specific team."""
    logo_url = f"https://www.mlbstatic.com/team-logos/{team_id}.svg"
    return {"team_id": team_id, "logo_url": logo_url}

@LeagueRouter.get("/team/{team_id}/roster")
def get_team_roster(team_id: int, season: int):
    """Fetch the roster of a specific team for a given season."""
    endpoint = f"{config.BASE_URL}/teams/{team_id}/roster?season={season}"
    data = Utils.fetch_data(endpoint)
    return data.get("roster", [])

@LeagueRouter.get("/players")
def get_players(season: int):
    """Fetch all players for a specific season."""
    endpoint = f"{config.BASE_URL}/players?season={season}"
    data = Utils.fetch_data(endpoint)
    return data.get("players", [])


@LeagueRouter.get("/player/{player_id}")
def get_player(player_id: int):
    """Fetch a specific player by ID."""
    endpoint = f"{config.BASE_PLAYER_URL}/{player_id}"
    data = Utils.fetch_data(endpoint)
    return data