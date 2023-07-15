# Use a Python base image
FROM python:3.9

# Set the working directory inside the container
WORKDIR /app

# Copy the code repository files to the container's working directory
COPY . .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port your application is listening on (if applicable)
EXPOSE 5000

# Define the command to run your application
CMD ["python", "app.py"]
