#!/bin/bash

cat > task-definition.json <<_EOF_
{
    "containerDefinitions": [
        {
            "name": "container-name",
            "image": "ecr image name",
            "cpu": ${CPU},
            "memory": ${MEMORY},
            "essential": true,
            "portMappings": [
                {
                    "containerPort": 80
                }
            ],
            "logConfiguration": {
                "logDriver": "xxx",
                "options": {
                    ""xxx"
                }
            },
            "environment": [
                {
                    "name": "xxx",
                    "value": "xxx"
                }
            ]
        }
    ],
    "family": "xxx"
}
_EOF_