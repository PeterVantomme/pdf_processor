FROM python:3.10.4

WORKDIR /home/docker


# Commands for Nginx
RUN apt-get update \
    && apt-get install -y nginx \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    && echo "daemon off;" >> /etc/nginx/nginx.conf
RUN useradd nginx

# Commands for API
RUN apt-get update
COPY requirements.txt requirements.txt
COPY . .
RUN apt-get install ffmpeg libzbar0 tesseract-ocr ghostscript python3-tk  -y
RUN pip install --no-cache-dir --upgrade -r requirements.txt
RUN mkdir documents
RUN chmod -R 755 documents
RUN chmod -R 700 db.sqlite3
RUN useradd -ms /bin/bash docker
RUN chown -R docker documents
RUN chown -R docker db.sqlite3
RUN chown -R docker .
EXPOSE 443
EXPOSE 8000
EXPOSE 80