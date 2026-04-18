# Use the official Python image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY . .

# Expose the port Render uses
EXPOSE 10000

# Run the application using Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:10000", "app:app"]