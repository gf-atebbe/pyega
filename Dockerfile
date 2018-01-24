FROM python:3.6-alpine3.6
LABEL maintainer "Adam Tebbe <atebbe@goldfinchbio.com>"

RUN apk update && \
    apk add bash git unzip openjdk8 openjdk8-jre openssl gnupg gcc musl-dev linux-headers && \
    rm -rf /var/cache/apk/*

RUN pip3 install requests boto3 gnupg

RUN chmod 777 /usr/local/lib/python3.6/site-packages && \
    chmod 777 /usr/local/bin

SHELL ["/bin/bash", "-c"]

RUN mkdir -p /usr/src/app && \
    cd /usr/src/app && \
    wget https://www.ebi.ac.uk/ega/sites/ebi.ac.uk.ega/files/documents/EGA_download_client_2.2.2.zip && \
    unzip EGA_download_client_2.2.2.zip && \
    rm EGA_download_client_2.2.2.zip && \
    rm -f *.pdf && \
    rm -fr __MACOSX && \
    rm -f *.DOCX

ADD pyega.py /usr/src/app/

VOLUME /mnt/data
WORKDIR /mnt/data
CMD [ "python3", "/usr/src/app/pyega.py" ]
# java -jar /usr/src/app/EgaDemoClient.jar -p email password -dc path_to_file_1 -dck abc
