import typing_extensions as typing


class Highlights(typing.TypedDict):
    title: str
    timeInterval: list[str]
    description: str
    thumbnail: str
    
    

class Advertisements(typing.TypedDict):
    """
    A dictionary to represent an advertisement with the following fields:
    - title (str): The title of the advertisement.
    - description (str): A short description or summary of the advertisement.
    - html_content (str): The HTML content of the advertisement.
   """

    title: str  # Title of the advertisement
    description: str  # A brief description of the advertisement
    html_content: str  # The HTML content of the advertisement
