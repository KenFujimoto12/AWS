import json
import boto3
import logging
import os
import math
from boto3.session import Session

from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

slackChannel = os.environ['slackChannel']
hookUrl = os.environ['slackWebHookUrl']

# support = boto3.client('support', region_name='us-east-1')
sts = boto3.client('sts')
secretsmanager = boto3.client('secretsmanager')

def get_account_ids():
    getSecretValues = secretsmanager.get_secret_value(
        SecretId = "aws/account-ids"
        )

    accountIds = json.loads(getSecretValues['SecretString'])
    return accountIds

def seitch_session_account(accounId):
    ## another account session
    iamRoleArn = 'arn:aws:iam::%s:role/read-only-cross-account-role' % accounId
    iamRoleSessionName = 'internal'

    response = sts.assume_role(
        RoleArn = iamRoleArn,
        RoleSessionName = iamRoleSessionName
        )

    session = Session(
        aws_access_key_id=response['Credentials']['AccessKeyId'],
        aws_secret_access_key=response['Credentials']['SecretAccessKey'],
        aws_session_token=response['Credentials']['SessionToken']
        )

    global support
    support = session.client('support', region_name='us-east-1')

def get_target_aws_resource():
    detectedResourceList = support.describe_trusted_advisor_checks(
        language='ja'
        )
    return detectedResourceList

def get_reduction_cost(id):
    cost = support.describe_trusted_advisor_check_summaries(
        checkIds=[
            id,
        ]
    )
    return cost

def lambda_handler(event, context):
    accoundInfo = get_account_ids()
    accountIds = accoundInfo['accoun-ids']

    for account in accountIds:
        accountId = accountIds[account]

        seitch_session_account(accountId)
        detectedResourceList = get_target_aws_resource()

        targetResouceList = [i for i in detectedResourceList['checks'] if i['category'] == 'cost_optimizing']

        costList = []

        for i in targetResouceList:
            targetDetectionName = i['name'].replace(' ', '')
            cosSummary = get_reduction_cost(i['id'])

            if cosSummary['summaries'][0]['categorySpecificSummary'].get('costOptimizing') is None:
                logger.info("No cost!")
            else:
                cost = cosSummary['summaries'][0]['categorySpecificSummary']['costOptimizing']['estimatedMonthlySavings']
                if cost == 0:
                    logger.info("No cost!")
                else:
                    message = "\n *%s : $ %s*" % (targetDetectionName, math.floor(cost))
                    costList.append(message)

        messages = "======================= `%s` ======================== \n :moneybag: *削減できそうなコスト(合計値)* " % account

        for message in costList:
            messages += message

        slackMessage = {
            "channel": slackChannel,
            "text": messages
        }

        req = Request(hookUrl, json.dumps(slackMessage).encode('utf-8'))
        try:
            response = urlopen(req)
            response.read()
            logger.info("Message posted to %s", slackMessage['channel'])
        except HTTPError as e:
            logger.error("Request failed: %d %s", e.code, e.reason)
        except URLError as e:
            logger.error("Server connection failed: %s", e.reason)
