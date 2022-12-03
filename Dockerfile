FROM python:3.10.7

WORKDIR /app
COPY . /app

# Install required packages
RUN pip install -r requirements.txt

CMD python main.py