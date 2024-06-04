# Use the official Python image from the Docker Hub
FROM python:3.12

# Set environment variables to make the build process non-interactive
ENV DEBIAN_FRONTEND=noninteractive

# Install required apt packages
RUN apt-get update && \
    apt-get install -y poppler-utils ghostscript swig && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy the application code
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port the app runs on
EXPOSE 5000

# Command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
