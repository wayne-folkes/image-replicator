
REPO_NAME ?= ecr-replicator
STAGE ?= dev


#@pip install -r requirements.txt &&\

deploy-codebuild:
	@printf "> \033[36mDeploying Codebuild...\033[0m\n"
	@aws cloudformation deploy \
	--template-file cf/codebuild.cfn.yaml --stack-name $(REPO_NAME)-$(STAGE) \
	--capabilities CAPABILITY_NAMED_IAM \
	--parameter-overrides \
		ProjectName=$(REPO_NAME)