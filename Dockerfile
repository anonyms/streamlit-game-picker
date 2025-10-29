FROM python:3.13-slim


#Set environment variables to prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install all dependencies, set up Chrome/driver, and clean up in ONE layer
RUN apt-get update \
    # Install build dependencies: wget for downloading, gnupg for keys, unzip for the driver
    && apt-get install -y wget gnupg unzip --no-install-recommends \
    # Add Google's signing key
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome-linux-signing-key.gpg \
    # Add the Google Chrome repository
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-linux-signing-key.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    # Update apt again to pull info from the new Google repo
    && apt-get update \
    # Install Google Chrome
    && apt-get install -y google-chrome-stable --no-install-recommends \
    # --- Start of Chromedriver logic ---
    # Get the installed Chrome version
    && CHROME_VERSION=$(google-chrome --version | cut -d " " -f3 | cut -d "." -f1-3) \
    # Find the matching driver version
    && DRIVER_VERSION=$(wget -qO- https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_${CHROME_VERSION}) \
    # Download the driver
    && wget -q --continue -P /tmp "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/${DRIVER_VERSION}/linux64/chromedriver-linux64.zip" \
    # Unzip the driver (This was the missing part)
    && unzip /tmp/chromedriver-linux64.zip -d /usr/local/bin \
    && rm /tmp/chromedriver-linux64.zip \
    # Make executable and create symlink
    && chmod +x /usr/local/bin/chromedriver-linux64/chromedriver \
    && ln -s /usr/local/bin/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver \
    # --- End of Chromedriver logic ---
    # Clean up the build dependencies
    && apt-get purge -y wget gnupg unzip \
    # Clean up apt caches
    && rm -rf /var/lib/apt/lists/*

# dont write pyc files
# dont buffer to stdout/stderr

WORKDIR /usr/src/app
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# COPY ./requirements.txt /usr/src/app/requirements.txt
COPY ./requirements.txt .

# dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

