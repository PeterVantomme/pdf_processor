FROM python:3.10.4

WORKDIR /
WORKDIR /home/docker


# Commands for API
COPY requirements.txt requirements.txt
COPY . .
RUN pip install --no-cache-dir --upgrade -r requirements.txt
RUN apt-get update
RUN apt-get -y install ghostscript python3-tk 
RUN apt-get install ffmpeg libzbar0 tesseract-ocr -y
RUN mkdir documents
RUN chmod -R 755 documents
RUN chmod -R 700 db.sqlite3
RUN useradd -ms /bin/bash docker
RUN chown -R docker documents
RUN chown -R docker db.sqlite3
RUN chown -R docker .
USER docker
EXPOSE 8000