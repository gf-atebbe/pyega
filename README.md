pyEGA uses the EGA REST API to download authorized datasets and files
and is an alternaive to the supplied EgaDemoClient.jar


# REQUIREMENTS
Python "requests" module
http://docs.python-requests.org/en/master/
pip3 install requests


First, store your credentials in ~/.ega.json:
{
    "username": "my.email@university.edu",
    "password": "SuperSecurePasswordIncludes123",
    "key": "symmetric_encryption_key"
}

Your username and password are provided to you by EGA.
The symmetric encryption key can be any non-empty value and
is used to encrypt the data before it is transferred over the wire.
You will still need to decrypt using EgaDemoClient.java


If you know the stable identifier of a dataset (EGAD...) or file (EGAF...)
you can fetch it directly with the "fetch" subcommand. Other commands
to look at specific requests or file details are available. These would
mostly apply to aborted downloads, etc., as the "fetch" command executes
a complete (make request -> list request [metadata] -> download request)
workflow automatically. The "fetch" command will also save a copy of the
request metadata as <requestlabelid>.json


# TODO
Download metadata package
List metadata when listing authorized datasets
Verify file size and MD5 hash after download
Parallel download streams

# BUGS
Files will be overwritten without warning!


# HELP
pyEGA version 1.1.0
James S. Blachly, MD

usage: pyega.py [-h] [-d]
                {datasets,datasetinfo,requests,rmreq,files,fetch,sync} ...

Download from EMBL EBI's EGA (European Genome-phenome Archive

positional arguments:
  {datasets,datasetinfo,requests,rmreq,files,fetch,sync}
                        subcommands
    datasets            List authorized datasets
    datasetinfo         List files in a specified dataset
    requests            List outstanding requests
    rmreq               Delete (remove) request label
    files               List files (optionally, for a specific request label)
    fetch               Fetch a dataset or file
    sync                Sync a dataset or file to a remote location

optional arguments:
  -h, --help            show this help message and exit
  -d, --debug           Extra debugging messages


# Running PyEGA in Docker

This is a simple example illustrating how to sync
``` bash
docker run \
--rm \
-ti \
-v ~/.ega.json:/root/.ega.json \
-v ~/.aws:/root/.aws \
-v /mnt/data/EGAD00001000598:/mnt/data \
227114915345.dkr.ecr.us-east-1.amazonaws.com/pyega:1.1.0 \
python3 /usr/src/app/pyega.py sync \
EGAD0000... \
s3://my_bucket/EGAD0000.../
```