<h1> InsightGrid Telegram Bot </h1>
In collaboration with 5Guys1Girl, a Final Year Project team from Singapore Management University, we present InsightGrid, a Telegram Bot designed to navigate users/drivers to carparks near their destination. The telegram bot features clean message designs, customisable settings, and just-in-time notifications to provide users with a pleasant experience of navigating to locations they may not be familiar with.

InsightGrid was created to showcase the potential of NGSI-LD to solve issues on Data Interoperability.

You may find out more about NGSI-LD in the links below:
- https://fiware-datamodels.readthedocs.io/en/stable/ngsi-ld_howto/
- https://www.etsi.org/deliver/etsi_gs/CIM/001_099/009/01.05.01_60/gs_cim009v010501p.pdf
- https://stackoverflow.com/questions/68072065/which-are-the-differences-of-ngsi-ld-and-json-ld

The following details the deployment guide for InsightGrid locally and on Cloud.

<h2>Locally hosted InsightGrid Telegram Bot</h2>
The following instructions details the steps taken to locally host the InsightGrid Telegram Bot on your machine.

<h3>Setting up Context Broker</h3>

1) Git Clone Repository
```bash
git clone https://github.com/systemssndgg/SNDGG-SMU-IS483.git
```

2) Create Docker Image of MDDI Context Broker
Navigate to /telegram-bot/context_broker and run the following command in your terminal
```bash
docker compose -f orion.aio.yml up --build
```

Feel free to change any of the settings on the dockerfile at your discretion

3) Ensure docker containers and images are up and healthy
    - 8 docker images are up and running
    - In /telegram-bot, you can successfully run import_entities.py

<h3 id="set-up-insightgrid-telegram-bot">Set up InsightGrid Telegram Bot</h3>
                
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
  
4) Generate Firestore API Key

   To connect your Telegram bot to Firestore, follow these steps to generate and configure the API key:

   - **Generate the Service Account Key**:
     - Go to the [Google Cloud Console](https://console.cloud.google.com/).
     - Navigate to **IAM & Admin > Service Accounts**.
     - Select the service account associated with your Firestore database.
     - Click **Create Key** and choose the **JSON** format.

   - **Download the JSON Key File**:
     - Save the file to your local machine.

   - **Rename the JSON Key File**:
     - Rename the downloaded file to `ngsi-ld-systems.json`.

   - **Place the File in the Project Directory**:
     - Move the file to the following location in your project:
     ```
     SNDGG-SMU-IS483/telegram-bot/utils
     ```
      
5) Run the Telegram Bot
   Navigate to /telegram-bot and run the following command in your terminal

       python main.py
_Ensure that your context broker docker image is running_

The bot will start updating the entities in the context broker
    
    URA Carpark ParkingAvailability Update Frequency: Every 5 mins / 300 seconds

    Weather Data Update Frequency: Every 2 hours / 7200 seconds

    TrafficAdvisories Update Frequency: Every 2 minutes / 120 seconds

<h2> Cloud hosted InsightGrid Telegram Bot </h2>
Google Cloud Platform (GCP) was used to host the InsightGrid

### Step 1: Set Up a GCP Virtual Machine

1. **Navigate to the VM Instances Page**:
   - Go to the [VM Instances](https://console.cloud.google.com/compute/instances) page in GCP.

2. **Create a New Instance**:
   - Click **Create Instance**
   - Configure the instance with the following parameters:
     - **Name**: `your-instance-name`
     - **Machine type**: `e2-micro` (or your preferred type)
     - **Boot disk**: Use the default image or select **Ubuntu 22.04**
   - Click **Create**

### Step 2: Connect to the VM via GCP Browser SSH

1. On the **VM Instances** page, find your newly created VM
2. Click the **SSH** button in the row corresponding to your VM. A new browser window will open with an SSH session

### Step 3: Install Docker and Other Dependencies

Once inside the SSH session:

1. **Update the VM**:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```
2. **Install Docker**:
   ```bash
   sudo apt install -y docker.io
   ```
3. **Install Git**:
   ```bash
   sudo apt install -y git
   ```

### Step 4: Git Clone Repository
```bash
git clone https://github.com/systemssndgg/SNDGG-SMU-IS483.git
```
   
### Step 5: Create Docker Image of MDDI Context Broker 
Navigate to the context_broker directory:
```bash
cd SNDGG-SMU-IS483/telegram-bot/context_broker
```
Build and run the Docker container in detached mode:
```bash
sudo docker compose -f orion.aio.yml up --build -d
```

### Step 6: Set up InsightGrid Telegram Bot
Follow the instructions in the [Set up InsightGrid Telegram Bot](#set-up-insightgrid-telegram-bot) section above.

### Step 7: Run Telegram Bot Detached
1. Navigate to the telegram_bot directory:
```bash
cd SNDGG-SMU-IS483/telegram-bot
```
2. Start a tmux session to ensure the bot runs independently of your SSH session:
```bash
# Replace <session_name> with a name for your session (e.g., telegram_bot)
tmux new -s <session_name>
```

3. Run the telegram bot
```bash
python main.py
```

4. Detach from the tmux session
   - Press Ctrl + b, then d to detach from the session while keeping the bot running.

5. Reattach to the Tmux Session (if needed):
```bash
# Replace <session_name> with the name of your session.
tmux attach-session -t <session_name>
```
