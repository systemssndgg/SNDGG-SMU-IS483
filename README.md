<h1> InsightGrid Telegram Bot </h1>
Welcome to InsightGrid, a Telegram Bot designed to navigate users/drivers to carparks near their destination. The telegram bot features clean message designs, customisable settings, and just-in-time notifications to provide users with a pleasant experience of navigating to locations they may not be familiar with.

InsightGrid was created to showcase the potential of NGSI-LD to solve issues on Data Interoperability.

You may find out more about NGSI-LD in the links below:
- https://fiware-datamodels.readthedocs.io/en/stable/ngsi-ld_howto/
- https://www.etsi.org/deliver/etsi_gs/CIM/001_099/009/01.05.01_60/gs_cim009v010501p.pdf
- https://stackoverflow.com/questions/68072065/which-are-the-differences-of-ngsi-ld-and-json-ld

The following details the deployment guide for InsightGrid locally and on Cloud.

<h2> Locally hosted InsightGrid Telegram Bot </h2>
The following instructions details the steps taken to locally host the InsightGrid Telegram Bot on your machine.

<h3>Setting up Context Broker</h3>

1) Create docker image of MDDI Context Broker
Navigate to /telegram-bot/context_broker and run the following command in your terminal

       docker compose -f orion.aio.yml up --build

Feel free to change any of the settings on the dockerfile at your discretion

2) Ensure docker containers and images are up and healthy
    - 8 docker images are up and running
    - In /telegram-bot, you can successfully run import_entities.py

<h3>Set up InsightGrid Telegram Bot</h3>
                
1) Create and activate Virtual Environment inside telegram-bot folder (if necessary)

       # For windows
       python -m venv myenv
   
       # For macOS/Linux
       source myenv/bin/activate
   
       # Activate Virtual Environment
       myenv\Scripts\activate

2) Install Dependencies
   Navigate to /telegram-bot and pip install the requirements.txt file

        pip install -r requirements.txt
 
3) In Replicate constants.py.example (omit .example) and fill in API keys in the newly created constants.py

   Request API Keys from the following links:
    - Telegram API -> https://t.me/botfather
    - Google Maps API -> https://developers.google.com/maps
    - Datamall -> https://datamall.lta.gov.sg/content/datamall/en/request-for-api.html 
    - URA API -> https://www.developer.tech.gov.sg/products/categories/data-and-apis/ura-apis/overview.html
    - Data.gov API -> https://guide.data.gov.sg/user-guide/for-data-owners/how-to-generate-api-keys
      
4) Run the Telegram Bot
   Navigate to /telegram-bot and run the following command in your terminal

       python main.py
_Ensure that your context broker docker image is running_

The bot will start updating the entities in the context broker
    
    URA Carpark ParkingAvailability Update Frequency: Every 5 mins / 300 seconds

    Weather Data Update Frequency: Every 2 hours / 7200 seconds

    TrafficAdvisories Update Frequency: Every 2 minutes / 120 seconds

<h2> Cloud hosted InsightGrid Telegram Bot </h2>
Google Cloud Platform (GCP) was used to host the InsightGrid

1) xxx

2) xxx

