import boto3
import json
import logging
import os
import time
import math

from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# The Slack channel to send a message to stored in the slackChannel environment variable
SLACK_CHANNEL = os.environ['slackChannel']
HOOK_URL = os.environ['slackWebHookUrl']
PROJECT = os.environ['project']
ENV = os.environ['env']

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def getLogStream(page):
    if page['events'] != []:
        return page['events'][0]['logStreamName']

def lambda_handler(event, context):
    logger.info("Event: " + str(event))
    message = json.loads(event['Records'][0]['Sns']['Message'])
    logger.info("Message: " + str(message))

    ##これ以下は自由に記述してください

    logs = boto3.client('logs')
    metricfilters = logs.describe_metric_filters(
        metricName = message['Trigger']['MetricName'] ,
        metricNamespace = message['Trigger']['Namespace']
    )
    nowTime = (math.floor(time.time()))

    paginator = logs.get_paginator('filter_log_events')
    errorResponse = paginator.paginate(
            logGroupName = metricfilters['metricFilters'][0]['logGroupName'],
            filterPattern = '?ERROR ?error ?Error ?"Error:" ?WARN ?Notice ?Warning ?Fatal',
            startTime = (nowTime - 60) * 1000,
            endTime = nowTime * 1000,
            PaginationConfig = {
                'MaxItems': 5,
                'PageSize': 1
            }
        )

    #eventが複数取得される場合対策
    logStreamNames = map(getLogStream, filter(lambda x:x['events'] != [], errorResponse))

    for logStreamName in logStreamNames:
        eventResponse = logs.filter_log_events(
          logGroupName = metricfilters['metricFilters'][0]['logGroupName'],
          filterPattern = '"[end]"',
          logStreamNames = [logStreamName],
          limit = 1,
          startTime = (nowTime - 60) * 1000,
          endTime = nowTime * 1000
        )

        if eventResponse['events'] != []:
            response = eventResponse['events'][0]['message']
            target = response.split()
            targetEvent = target[1]
            slack_message = {
                'channel': SLACK_CHANNEL,
                'text': "xxx"
            }
        else:
            slack_message = {
                'channel': SLACK_CHANNEL,
                'text': "xxx"
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

        return {
            'statusCode': 200
        }