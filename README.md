# image-replicator



![Build Status](https://codebuild.us-east-1.amazonaws.com/badges?uuid=eyJlbmNyeXB0ZWREYXRhIjoiNzJhZWF2NGdtcGpDZWRnOG9VV2p3QjFQTXdEd0ZyT0RXRksxZlRaNHFwSi9aUlJTUkpqWGJERzFzZlFLOTA4NjBtTks4a3JCYkM1b0VadWNtT2pBeWFNPSIsIml2UGFyYW1ldGVyU3BlYyI6ImNsTnFHNXN4ZWlkaUtzVzIiLCJtYXRlcmlhbFNldFNlcmlhbCI6MX0%3D&branch=master)


This project allows you to keep a copy of publically available Docker images in AWS ECR. The use case for this to keep your services running in the event of an outage on Dockerhub or other public registry. This works by running a Codebuild job that will pull the images defined in the images.yaml config file and push to ECR if isnt already present.

## Components

1. [../cf/codebuild.cfn.yaml](../cf/codebuild.cfn.yaml) - Cloudformation template to create the Codebuild Job
2. [replicate-images.py](../cf/codebuild.cfn.yaml) - This python script will:
   1. parses the YAML config
   2. Checks to see if the ECR repository exists, if not create it. The default value for the repo will the URL of the source repo
   3. Check to see if an image with the same tag is in the repo if not then execute [__push-pull.sh__](../push-pull.sh)
3. [push-pull.sh](../push-pull.sh) - This script takes 2 arguments __source_repo__ and __target_repo__ it will.
   1. Pull the image
   2. Tag the image for your ECR repo
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
