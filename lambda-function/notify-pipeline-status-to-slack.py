import boto3
import json
import logging
import os

from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# The Slack channel to send a message to stored in the slackChannel environment variable
SLACK_CHANNEL = os.environ['slackChannel']
HOOK_URL = os.environ['slackWebHookUr']
PROJECT = os.environ['project']
ENV = os.environ['env']

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def statusMap(status):
    messageMapByStatus = {
        "STARTED": "> 📍 *DEPLOY %s* \n> ・Environment: *%s* \n> ・Service: *%s* \n> Deployment started. " % (status, ENV, PROJECT),
        "SUCCEEDED":  "> ✅ *DEPLOY %s* \n> ・Environment: *%s* \n> ・Service: *%s* \n> Deployment success!" % (status, ENV, PROJECT),
        "FAILED": "> 🆘 *DEPLOY %s* \n> ・Environment: *%s* \n> ・Service: *%s* \n> Deployment failed to unexpected error." % (status, ENV, PROJECT)
    }
    return messageMapByStatus["%s" % status]

def lambda_handler(event, context):
    logger.info("Event: " + str(event))
    message = json.loads(event['Records'][0]['Sns']['Message'])

    if message["source"] == "aws.codepipeline":
        status = message['detail']['state']

        slack_message = {
            "channel": SLACK_CHANNEL,
            "text": statusMap(status)
        }

        req = Request(HOOK_URL, json.dumps(slack_message).encode('utf-8'))
        try:
            response = urlopen(req)
            response.read()
            logger.info("Message posted to %s", slack_message['channel'])
        except HTTPError as e:
            logger.error("Request failed: %d %s", e.code, e.reason)
        except URLError as e:
            logger.error("Server connection failed: %s", e.reason)