
# NGSI-LD-SG-Datamall: Examples for interns
 Pull open Singapore data into NGSI-LD broker

### Fill in your API keys
create /mylibs/constants.py
Copy /mylibs/constants.py.example into /mylibs/constants.py
Fill in your API keys (Request them from LTA datamall and telegram as needed)

### Create venev
If necessary, create virtual environment:

```
python -m venv myenv
myenv\Scripts\activate
pip install -r requirements.txt
```

### To run:
python file_name


## Quick start

Run NGSI-LD broker locally

Create carparks
```
python import_parkingspots.py
```

Use postman to query carparks

Test out different queries

Delete carparks
```
python delete_parkingspots.py
```

=======


# NGSI-LD Datamall Telegrambot

## Readme

### Step 1: Create Virtual Environment

- **On Windows:**
  ```bash
  python -m venv myenv
  ```

### Step 2: Activate Virtual Environment

- **On Windows:**
  ```bash
  myenv\Scripts\activate
  ```

- **On macOS/Linux:**
  ```bash
  source myenv/bin/activate
  ```

### Step 3: Install Libraries

```bash
pip install landtransportsg
pip install ngsildclient
pip install geopy
pip install telegram
pip install python-telegram-bot
```

### Step 4: Start NGSI-LD Broker

Run a local copy of the NGSI-LD Broker. Refer to the broker's documentation for setup instructions.

### Step 5: Run Script to Import NGSI-LD Entities

```bash
python import_parkingspots.py
```

### Step 6: Start Telegram Bot

```bash
python telegram_bot.py
```

### Step 7: Interact with the Bot

1. Open Telegram.
2. Search for **#Ljp_ngsi_bot**.
3. Send `/start` to the bot.
4. Follow the instructions provided by the bot.

## Configurations

If you are not using the default broker configurations, please update the settings in `myLibs/constants.py` accordingly.



