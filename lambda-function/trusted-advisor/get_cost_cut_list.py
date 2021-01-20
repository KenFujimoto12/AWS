import boto3
import logging

support = boto3.client('support', region_name='us-east-1')

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
    detectedResourceList = get_target_aws_resource()

    targetResouceList = [i for i in detectedResourceList['checks'] if i['category'] == 'cost_optimizing']

    costList = []

    for i in targetResouceList:
        targetDetectionName = i['name']
        cosSummary = get_reduction_cost(i['id'])

        if cosSummary['summaries'][0]['categorySpecificSummary'].get('costOptimizing') is None:
            cost = "削減するコストは有りません"
        else:
            cost = cosSummary['summaries'][0]['categorySpecificSummary']['costOptimizing']['estimatedMonthlySavings']

        costObj = {
            'name': targetDetectionName,
            'cost': cost
        }

        costList.append(costObj)

    return costList
