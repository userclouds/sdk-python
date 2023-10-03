# sdk-python

Install the SDK by running
```
pip3 install usercloudssdk
```

You need to have a tenant on UserClouds to run the sample code against. Once you have the tenant information, you can try running the various samples in this repo. Clone this repo locally, and then update the following lines in `userstore_sample.py`:
```
client_id = "<REPLACE ME>"
client_secret = "<REPLACE ME>"
url = "<REPLACE ME>"
```
with the details from your tenant.

then run:
```
python3 userstore_sample.py
```
