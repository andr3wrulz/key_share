FROM python:3.7
LABEL maintainer="geltz.andrew@gmail.com"

# Setup the working dir
WORKDIR /usr/src/app

# Install the required python libraries
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the application on port 8000
EXPOSE 8000

# Start the server
CMD ["/start.sh"]