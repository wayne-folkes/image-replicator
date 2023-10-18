#!/usr/bin/env python3

import logging
import subprocess
import sys

import backoff
import boto3
import yaml
from botocore import exceptions as botoexceptions

ecr = boto3.client("ecr")

ACCOUNTID = boto3.client("sts").get_caller_identity().get("Account")
REGION = boto3.DEFAULT_SESSION.region_name
ECR_BASE = f"{ACCOUNTID}.dkr.ecr.{REGION}.amazonaws.com"

log = logging.getLogger()
logging.basicConfig(stream=sys.stdout, level=logging.INFO)


@backoff.on_exception(backoff.expo, botoexceptions.ClientError, max_time=10)
def is_repo_present(image):
    log.info("Checking for image")
    try:
        ecr.describe_repositories(repositoryNames=[image])
        return True
    except ecr.exceptions.RepositoryNotFoundException:
        return False
    except ecr.exceptions.InvalidParameterException as e:
        log.error(
            f"Unable to check for the presence of {image} \
                InvalidParameterException encoutered {e}"
        )
        raise


@backoff.on_exception(backoff.expo, botoexceptions.ClientError, max_time=10)
def is_image_present(image, tag, digest=None):
    log.info(f"Searching for {image}:{tag} in ECR")
    if tag == "latest":
        log.info("Latest tag used, pulling image anyway ")
        return False
    else:
        try:
            if digest is not None:
                image_id = {"imageTag": str(tag), "imageDigest": str(digest)}
            else:
                image_id = {"imageTag": str(tag)}
            response = ecr.describe_images(
                repositoryName=image,
                imageIds=[image_id],
                filter={"tagStatus": "TAGGED"},
            )
            if len(response.get("imageDetails")) == 0:
                return False
            else:
                log.info(f"{image}:{tag} found in ECR")
                return True
        except (
            ecr.exceptions.ImageNotFoundException,
            ecr.exceptions.RepositoryNotFoundException,
        ):
            return False


@backoff.on_exception(backoff.expo, botoexceptions.ClientError, max_time=10)
def create_repo(repo_name):
    ecr.create_repository(
        repositoryName=repo_name,
        tags=[{"Key": "Source", "Value": repo_name}],
        imageScanningConfiguration={"scanOnPush": True},
    )


def get_policy():
    return open("policy.json").read().replace("\n", "").replace("  ", "")


def apply_resource_policy(repo_name):
    try:
        policy = get_policy()
        log.info("Attempting to apply ECR repo policy")
        ecr.set_repository_policy(repositoryName=repo_name, policyText=policy)
    except ecr.exceptions.InvalidParameterException as e:
        log.error(f"Unable to apply repo policy: {e}")


def replicate_image(source_image, target_image) -> int:
    log.info("Replicating image")
    log.info(f"Source {source_image}")
    log.info(f"Target {target_image}")
    script_path = "./pull-push.sh"
    result = subprocess.run(
        [script_path, source_image, target_image], capture_output=True, text=True
    )
    log.info("Running {result.args}")
    if result.returncode == 0:
        log.info(result.stdout)
        return 0
    else:
        log.error(result.stderr)
        return 1


def get_image_list():
    return yaml.safe_load(open("images.yaml"))


def main():
    images: list = get_image_list()
    failed_replicated_images: list = []
    num_images: int = len(images)
    log.info(f"{num_images} Images found in file")
    for index, image in enumerate(images, start=1):
        source = image.get("source")
        destination = image.get("destination", image.get("source"))
        tag = image.get("tag")
        digest = image.get("digest")
        log.info(tag)
        source_image = f"{source}:{tag}"

        if tag is not None and digest is not None:
            source_image = f"{source}:{tag}@{digest}"
            log.info("tag with digest")

        log.info(f"Source Image {index} of {num_images} - {source_image}")
        log.info(f"Checking for repo {destination} in ECR")

        if not is_repo_present(destination):
            log.info(f"Repo {destination} not found, creating...")
            create_repo(destination)
            log.info(f"Repo {destination} created!")
            apply_resource_policy(destination)

        target_image = f"{ECR_BASE}/{destination}:{tag}"

        log.info("Target Image %s", target_image)

        log.info(f"Checking for image {tag} in repo {destination} in ECR")
        if not is_image_present(destination, tag, digest):
            log.info(f"{target_image} not found in ECR initiating replication")
            if replicate_image(source_image, target_image) != 0:
                failed_replicated_images.append(source_image)
    if len(failed_replicated_images) > 0:
        log.info(
            f"Replication Completed with failures \
                {len(failed_replicated_images)} failed to be replicated"
        )
        for failed_replicated_image in failed_replicated_images:
            log.error(failed_replicated_image)


if __name__ == "__main__":
    main()
