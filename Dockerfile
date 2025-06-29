# Use Python 3.10 image
FROM python:3.10.12-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Run your bot
CMD ["python", "main.py"
