# image-replicator

This project allows you to keep a copy of publically available Docker images in AWS ECR. The use case for this to keep your services running in the event of an outage on Dockerhub or other public registry. This works by running a Codebuild job that will pull the images defined in the images.yaml config file and push to ECR if isnt already present.

## Components

1. [../cf/codebuild.cfn.yaml](../cf/codebuild.cfn.yaml) - Cloudformation template to create the Codebuild Job
2. [replicate-images.py](../cf/codebuild.cfn.yaml) - This python script will:
   1. parses the YAML config
   2. Checks to see if the ECR repository exists, if not create it. The default value for the repository will the URL of the source repository
   3. Check to see if an image with the same tag is in the repository if not then execute [__push-pull.sh__](../push-pull.sh)
3. [push-pull.sh](../push-pull.sh) - This script takes 2 arguments __source_repo__ and __target_repo__ it will.
   1. Pull the image
   2. Tag the image for your ECR repository
   3. Login to ECR
   4. Push the image
4. [buildspec.yaml](../buildspec.yaml) - This defines the dependencies and steps to be run in the Codebuild
5. [policy.json](../policy.json) - This defines a resource policy for your ECR repos to allow cross account sharing if needed
6. [images.yaml](../images.yaml) - This file should contain the images you want to replicate. Required fields are __source__ and __tag__

  ```yaml
  -  source: quay.io/giantswarm/cni
     tag: v3.9.1
   ```
## Usage

1. Deploy Codebuild job - `make deploy-codebuild`
2. Update [images.yaml](../images.yaml)
3. Push changes
