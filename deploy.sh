#!/bin/bash
set -ux

# 1) CONFIG
# read the configuration file to load variables into this shell script
source config

# 2) 
echo "Checking if the stack exist"
if ! aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION ; then
        aws cloudformation create-stack \
                --stack-name $STACK_NAME \
                --template-body file://cfn-template.yaml \
                --capabilities CAPABILITY_IAM  \
                --region $REGION \
                --parameters \
                    ParameterKey=pContainerImage,ParameterValue=$CONTAINER_IMAGE

else
        echo -e "\nStack exists, attempting update ..."
        aws cloudformation update-stack \
                --stack-name $STACK_NAME \
                --template-body file://cfn-template.yaml \
                --capabilities CAPABILITY_IAM  \
                --region $REGION \
                --parameters \
                    ParameterKey=pContainerImage,ParameterValue=$CONTAINER_IMAGE
fi