import pandas as pd
from fastapi import File, UploadFile,HTTPException,APIRouter
from Utils.Utils import Utils
from Utils.Constants import Constants

from datetime import datetime, timedelta
from fastapi import Query

contentAPIRouter=APIRouter(tags=["Content Analytics"])


@contentAPIRouter.get("/most-followed-players-interactions")
def get_most_followed_players_by_interactions():
    """Fetch most followed players based on interaction data."""
    if Constants.fan_favourites_df is None:
        raise HTTPException(status_code=400, detail="Data not loaded")

    # Exploding the fan_favourites_df to have one row per interaction
    fan_interactions_expanded_df = (Constants.fan_favourites_df
                                     .explode('followed_player_ids')
                                     .reset_index(drop=True))

    # Convert interaction player IDs to integer format (if needed)
    fan_interactions_expanded_df['followed_player_ids'] = (
        fan_interactions_expanded_df['followed_player_ids'].astype('Int64'))

    # Get player interaction counts
    player_interactions = (pd.merge(
        fan_interactions_expanded_df['followed_player_ids']
        .value_counts()
        .reset_index()
        .rename(columns={"followed_player_ids": "player_id", "count": "num_interactions"}),
        Constants.players[['id', 'nameFirstLast']].rename(columns={"id": "player_id", "nameFirstLast": "player_name"}),
        on='player_id',
        how='left'
    )[['player_id', 'player_name', 'num_interactions']])

    # Return top 10 players by interactions
    return player_interactions.nlargest(10, 'num_interactions').to_dict(orient="records")



@contentAPIRouter.get("/most-followed-teams-interactions")
def get_most_followed_teams_by_interactions():
    """Fetch most followed teams based on interaction data."""
    if Constants.fan_favourites_df is None:
        raise HTTPException(status_code=400, detail="Data not loaded")

    # Explode the 'followed_team_ids' column to create 1 row for each followed team
    team_interactions_expanded_df = (Constants.fan_favourites_df
                                      .explode('followed_team_ids')
                                      .reset_index(drop=True))

    # Convert followed team IDs to integer format
    team_interactions_expanded_df['followed_team_ids'] = team_interactions_expanded_df['followed_team_ids'].astype('Int64')

    # Merge to get team follower counts
    most_followed_teams = (pd.merge(
        team_interactions_expanded_df['followed_team_ids'].value_counts().reset_index().
            rename(columns={"count": "num_followers"}),
        Constants.teams[['id', 'name']].rename(columns={"id": "team_id", "name": "team_name"}),
        left_on='followed_team_ids',
        right_on='team_id',
        how='left'
    )[['team_id', 'team_name', 'num_followers']])

    return most_followed_teams.head(10).to_dict(orient="records")



@contentAPIRouter.get("/top-interacted-content")
def get_top_interacted_content(
    from_date: str = Query(
        default=(datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d"), 
        description="Filter content interactions from this date (YYYY-MM-DD)"
    ),
    to_date: str = Query(
        default=datetime.now().strftime("%Y-%m-%d"), 
        description="Filter content interactions up to this date (YYYY-MM-DD)"
    )
):
    """
    Fetch content pieces with the most fan interactions within a date range.
    """
    if Constants.fan_content_interaction_df is None:
        raise HTTPException(status_code=400, detail="Data not loaded")
    
    # Convert dates to datetime objects
    try:
        from_date_obj = datetime.strptime(from_date, "%Y-%m-%d")
        to_date_obj = datetime.strptime(to_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
    
    # Ensure the date column is in datetime format
    if Constants.fan_content_interaction_df["date_time_date"].dtype == "object":
        Constants.fan_content_interaction_df["date_time_date"] = pd.to_datetime(
            Constants.fan_content_interaction_df["date_time_date"]
        )
    
    # Filter the data based on the date range
    filtered_data = Constants.fan_content_interaction_df[
        (Constants.fan_content_interaction_df["date_time_date"] >= from_date_obj) &
        (Constants.fan_content_interaction_df["date_time_date"] <= to_date_obj)
    ]
    
    # Find the content pieces with the most interactions
    content_interactions = (
        filtered_data[["slug", "content_type", "content_headline"]]
        .value_counts()
        .reset_index()
        .rename(columns={"count": "num_interactions"})
        .sort_values(by="num_interactions", ascending=False)
    )
    
    return content_interactions.head(10).to_dict(orient="records")




@contentAPIRouter.get("/generate-content-link")
def generate_mlb_com_link(content_slug: str, content_type: str):
    """
    Generate MLB.com link for an article or video based on the content slug and type.
    Parameters:
    - content_slug: The unique identifier for the content.
    - content_type: Either 'article' or 'video'.

    Returns:
    - The MLB.com link for the specified content piece.
    """
    # Determine the category path based on content type
    content_type_cat = 'news' if content_type == 'article' else 'video'

    # Generate the full MLB.com link
    content_mlb_com_link = f"https://www.mlb.com/{content_type_cat}/{content_slug}"

    return {"content_link": content_mlb_com_link}

