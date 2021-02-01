import json
import boto3
import logging
import os
import datetime
import math
from boto3.session import Session

from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

slackChannel = os.environ['slackChannel']
hookUrl = os.environ['slackWebHookUrl']

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
      aws_session_token=response['Credentials']['SessionToken'],
      region_name='ap-northeast-1'
      )

  global ce
  ce = session.client('ce')

def fetch_measurement_period_of_cost_explorer(today):
  theFirstOfThisMonth = datetime.datetime(today.year, today.month, 1)
  theEndOfLastMonth = theFirstOfThisMonth + datetime.timedelta(days=-1)
  theFirstOfLastMonth = datetime.datetime(theEndOfLastMonth.year, theEndOfLastMonth.month, 1)
  return [theFirstOfThisMonth, theFirstOfLastMonth]

def get_costs(theFirstOfThisMonth, theFirstOfLastMonth):
  costInfo = ce.get_cost_and_usage(
    TimePeriod = {
      'Start': theFirstOfLastMonth.strftime("%Y-%m-%d"),
      'End': theFirstOfThisMonth.strftime("%Y-%m-%d")
    },
    Granularity = 'MONTHLY',
    Metrics=[
        'UnblendedCost',
    ],
    GroupBy=[
        {
            'Type': 'DIMENSION',
            'Key': 'SERVICE'
        },
    ],
    Filter = {
        'Dimensions': {
            'Key': 'REGION',
            'Values': [
              'ap-northeast-1'
            ]
        }
    }
  )
  return costInfo

def lambda_handler(event, context):
  accoundInfo = get_account_ids()
  accountIds = accountInfo['accoun-ids']

  for account in accountIds:
      accountId = accountIds[account]
      seitch_session_account(accountId)

      periodOfCostExplorer = fetch_measurement_period_of_cost_explorer(datetime.date.today())
      costInfo = get_costs(periodOfCostExplorer[0], periodOfCostExplorer[1])

      costList = []
      for i in costInfo['ResultsByTime'][0]['Groups']:
        resourceName = i['Keys'][0]
        if 'Amazon' in resourceName or 'AWS' in resourceName:
          resourceName = resourceName.replace('Amazon', '').replace('AWS', '')

        cost = float(i['Metrics']['UnblendedCost']['Amount'])

        if cost > 500:
          message = "\n *%s :* `$ %s` \n" % (resourceName, "{:.2f}".format(cost))
        else:
          message = "\n *%s : $ %s* \n" % (resourceName, "{:.2f}".format(cost))
        costList.append(message)

      messages = "======================= `%s` ======================== \n :money_with_wings: *AWSサービスごとのコスト( %s 年 %s 月分)* \n" % (account, periodOfCostExplorer[0].strftime("%Y"), periodOfCostExplorer[0].strftime("%m"))
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
