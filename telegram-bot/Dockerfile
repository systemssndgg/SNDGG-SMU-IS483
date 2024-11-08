FROM python:3.9-slim

# Set up working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

# Copy the application files
COPY . /app

# Expose the port Flask uses
EXPOSE 8080

# Start the Flask server and the bot
CMD ["python3", "main.py"]