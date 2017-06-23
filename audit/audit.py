"""

Description:
 A simple lambda function which will run a quick audit Ravello VMs.

"""
from __future__ import print_function
import json
import logging
import boto3
import pycurl
from io import BytesIO
import json

from base64 import b64decode
from urllib2 import Request, urlopen, URLError, HTTPError

SLACK_CHANNEL = '#training'  # Enter the Slack channel to send a message to
#SLACK_CHANNEL = '#play'  # debug


# noinspection PyPep8
logger = logging.getLogger()
logger.setLevel(logging.INFO)

#
# The encrypted values below were created using the following process
#
# 1. Create a new encryption key in AWS by going to the main console
#    and selecting IAM->Encryption Keys->Create key
#
# 2. Go to your local command line and encrypt your strings using the
#    newly-created key (e.g. 'foo') like this:
#       aws kms encrypt --key-id alias/foo --plaintext "secrets and lies"
#
# 3. The resulting output are the ENCRYPTED_<whatever> values pasted below
#
# They can only be deciphered by the 'foo' key. That key is associated with
# this lambda function using the "KMS key" option in the lambda Advanced
# settings section of the Configuration tab.
#
ENCRYPTED_HOOK_URL = "AQICAHgo09mInVFdR4EEq0EVGKEqdsrRfiv24DtHIkiUO6cEfgHIhtt5bRV1/i5hdm2TWrOGAAAApzCBpAYJKoZIhvcNAQcGoIGWMIGTAgEAMIGNBgkqhkiG9w0BBwEwHgYJYIZIAWUDBAEuMBEEDJHX0UnigIOdAya6hQIBEIBga4VxTDO8KDLapVw2z1pZjekITWs4Q7p9QtToehHuT33EcBunQ0dVHRCruaA/lVik4Adxkbr8Z6eGkm2N1opnAFz51eeUg7PozaSv5D24RnEiUTEAB9Bt/aZwNCMhWk7n"
DECRYPTED_HOOK_URL = boto3.client('kms').decrypt(CiphertextBlob=b64decode(ENCRYPTED_HOOK_URL))['Plaintext']
HOOK_URL = "https://%s" % DECRYPTED_HOOK_URL
ENCRYPTED_USER = "AQICAHgo09mInVFdR4EEq0EVGKEqdsrRfiv24DtHIkiUO6cEfgGhkO9rpSP1vek8aOkxVLTvAAAAcDBuBgkqhkiG9w0BBwagYTBfAgEAMFoGCSqGSIb3DQEHATAeBglghkgBZQMEAS4wEQQM5rWZfz6EurzQfmJiAgEQgC22xVN8xbIS2m4DD4zBruqWjBslGVzdJ72Jc3Ck5K+V0c10nbmHwFfFVCqAcF4="
DECRYPTED_USER = boto3.client('kms').decrypt(CiphertextBlob=b64decode(ENCRYPTED_USER))['Plaintext']
ENCRYPTED_PASSWORD = "AQICAHgo09mInVFdR4EEq0EVGKEqdsrRfiv24DtHIkiUO6cEfgHzPG0rjbCezBqKOGuxY0nJAAAAZzBlBgkqhkiG9w0BBwagWDBWAgEAMFEGCSqGSIb3DQEHATAeBglghkgBZQMEAS4wEQQM4mlpF3dZu/KN7aVTAgEQgCTYWrUPeDtFYmXoAkNwoerIRdO/DZyUMoH6tRQdmWClXo16kD4="
DECRYPTED_PASSWORD = boto3.client('kms').decrypt(CiphertextBlob=b64decode(ENCRYPTED_PASSWORD))['Plaintext']


def post_to_slack(msg):
    # uncomment to debug
    #    print(msg)
    #    return
    slack_message = {
        'channel': SLACK_CHANNEL,
        'text': msg
    }
    req = Request(HOOK_URL, json.dumps(slack_message))
    try:
        response = urlopen(req)
        response.read()
        logger.info("Message posted to %s", slack_message['channel'])
    except HTTPError as e:
        logger.error("Request failed: %d %s", e.code, e.reason)
    except URLError as e:
        logger.error("Server connection failed: %s", e.reason)


# noinspection PyUnusedLocal
def handler(event, context):

    total_active = 0
    buf = BytesIO()
    c = pycurl.Curl()
    c.setopt(c.URL, 'https://cloud.ravellosystems.com/api/v1/applications')
    c.setopt(c.WRITEFUNCTION, buf.write)
    c.setopt(c.HTTPHEADER, ['Accept: application/json'])
    c.setopt(c.USERPWD, "%s:%s" % (DECRYPTED_USER,DECRYPTED_PASSWORD))
    c.perform()
    j = json.loads(buf.getvalue())
    for item in j:
        if "deployment" in item:
            active = item["deployment"]["totalActiveVms"]
            total_active += active
            if active:
                msg = "Lab: %s, Owner: %s, VMs: %d" % (item["name"], item["owner"], active)
                post_to_slack(msg)
    post_to_slack("Ravello total active VMs is %d"%total_active)

# Uncomment to debug
# handler("", "")
