FROM python:3.10.4

WORKDIR /

COPY requirements.txt requirements.txt
COPY . .
RUN pip install --no-cache-dir --upgrade -r requirements.txt
RUN apt-get update
RUN apt-get -y install ghostscript python3-tk 
RUN apt-get install ffmpeg libsm6 libxext6  -y
#RUN apt-get install build-essential python -y
EXPOSE 8000