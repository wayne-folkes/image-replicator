#!/bin/bash

SOURCE=${1}
DESTINATION=${2}

echo The source is "${SOURCE}" the target is "${DESTINATION}"

docker pull ${SOURCE} && \
docker tag ${SOURCE} ${DESTINATION} && \
eval $(aws ecr get-login --no-include-email --region us-east-1) && \
docker push ${DESTINATION}

echo "${DESTINATION}" pushed successfully