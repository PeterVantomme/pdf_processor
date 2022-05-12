FROM python:3.10.4

WORKDIR /
WORKDIR /home/docker

COPY requirements.txt requirements.txt
COPY . .
RUN pip install --no-cache-dir --upgrade -r requirements.txt
RUN apt-get update
RUN apt-get -y install ghostscript python3-tk 
RUN apt-get install ffmpeg libzbar0 -y
#RUN apt-get install build-essential python -y
RUN chmod -R 755 documents
RUN useradd -ms /bin/bash docker
RUN chown -R docker documents
USER docker
EXPOSE 8000