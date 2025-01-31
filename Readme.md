This is Diamond District , a project built for Google * MLB hackathon


Setup:

1) Setup the virtual environment:
python3 -m venv venv

2) Activate it
source venv/bin/activate

3) Install the requirements 
pip3 install -r requirements.txt  (if some requirements doesnt download install manually using pip)

4) Set up your .env with API_KEY 
API_KEY="Insert your API KEY here"


5)Create one keys.json file and add google cloud credentials data inside it
if it causes some problem do (export path/to/json)

6) Start the server with the following command:
uvicorn app:app --port 5000 --reload

7) Check the swagger at the url : 127.0.0.1:5000/docs
click on try out to add inputs 


