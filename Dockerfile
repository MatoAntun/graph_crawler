FROM python:3.9.5
# port number container should expose
WORKDIR /scraper
RUN pip3 install --upgrade pip
RUN apt-get update && apt-get install -y python3-pip python-dev
COPY ./requirements.txt /scraper/requirements.txt
RUN pip install -r /scraper/requirements.txt
COPY . /scraper/
