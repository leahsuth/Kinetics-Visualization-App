
# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt ./

# Install any needed packages specified in requirements.txt (openpyxl required for .xlsx files)
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the port Streamlit runs on (default is 8501)
EXPOSE 8501

# Command to run the application when the container starts
CMD [ "streamlit", "run", "Main.py" ]
# CMD ["streamlit", "run", "your_app_name.py", "--server.port=8501", "--server.address=0.0.0.0"]

