#!/usr/bin/env python3

import boto3
import yaml
import os
import subprocess
import sys
import logging
import backoff
from botocore import exceptions as botoexceptions

ecr = boto3.client('ecr')

ACCOUNTID = boto3.client('sts').get_caller_identity().get('Account')
REGION = boto3.DEFAULT_SESSION.region_name
ECR_BASE = "{}.dkr.ecr.{}.amazonaws.com".format(ACCOUNTID,REGION)

log = logging.getLogger()
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

def is_repo_present(image):
    log.info('Checking for image')
    try:
        ecr.describe_repositories(repositoryNames=[image])
        return True
    except ecr.exceptions.RepositoryNotFoundException as e:
        return False

def is_image_present(image,tag):
    log.info("Searching for {}:{} in ECR".format(image,tag))
    try:
        response = ecr.describe_images(
            repositoryName=image,
            imageIds=[{
                    'imageTag': tag
                }],
            filter={
                'tagStatus': 'TAGGED'
            })
        if (len(response.get('imageDetails')) == 0):
            return False
        else:
            return True
    except (ecr.exceptions.ImageNotFoundException, ecr.exceptions.RepositoryNotFoundException) as e:
        return False

@backoff.on_exception(backoff.expo, botoexceptions.ClientError, max_time=10)
def create_repo(repo_name):
    ecr.create_repository(
        repositoryName=repo_name,
        tags==[
            {'Key': 'Source', 'Value': repo_name}
        ],
        imageScanningConfiguration={
        'scanOnPush': True
    })

def get_policy():
    return open('policy.json').read().replace('\n', '').replace('  ','')

def apply_resource_policy(repo_name):
    try:
        policy=get_policy()
        log.info("Attempting to apply ECR repo policy")
        ecr.set_repository_policy(
            repositoryName=repo_name,
            policyText=policy
        )
    except ecr.exceptions.InvalidParameterException as e:
        log.error("Unable to apply repo policy: {}".format(e))


def replicate_image(source_image,target_image):
    log.info("Replicating image")
    log.info("Source {}".format(source_image))
    log.info("Target {}".format(target_image))
    script_path = './pull-push.sh'
    result = subprocess.run([script_path, source_image, target_image],
                   capture_output=True, text=True
                   )
    log.info("Running {}".format(result.args))
    if (result.returncode == 0):
        log.info(result.stdout)
    else:
        log.error(result.stderr)

def get_image_list():
    return yaml.safe_load(open('images.yaml'))

def main():
    images = get_image_list()
    num_images=len(images)
    log.info("{} Images found in file".format(num_images))
    for index, image in enumerate(images,start=1):
        source = image.get('source')
        destination = image.get('source')
        tag = image.get('tag')
        source_image = "{}:{}".format(source,tag)
        log.info("Source Image {} of {} - {}".format(index, num_images, source_image))

        log.info("Checking for repo {} in ECR".format(destination))
        if not is_repo_present(destination):
            log.info("Repo {} not found, creating...".format(destination))
            create_repo(destination)
            log.info("Repo {} created!".format(destination))
            apply_resource_policy(destination)

        target_image = "{}/{}:{}".format(ECR_BASE,destination,tag)
        log.info("Target Image %s",target_image)

        log.info("Checking for image {} in repo {} in ECR".format(tag, destination))
        if not is_image_present(destination,tag):
            log.info("{} not found in ECR initiating replication".format(target_image))
            replicate_image(source_image,target_image)

if __name__ == "__main__":
    main()