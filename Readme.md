This is Diamond District , a project built for Google * MLB hackathon


Setup:

1) Setup the virtual environment:

python3 -m venv venv

2) Activate it

source venv/bin/activate

3) Install the requirements 

pip3 install -r requirements.txt

4) Set up your .env with API_KEY 

API_KEY="Insert your API KEY here"

5) Start the server with the following command:

uvicorn app:app --poirt 5000 --reload


