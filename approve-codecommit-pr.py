import json
import boto3
import traceback

codepipeline = boto3.client('codepipeline')
codebuild = boto3.client('codebuild')
codecommit = boto3.client('codecommit')

def lambda_handler(event, context):
    print(f"Full event: {event}")
    
    job = event['CodePipeline.job']
    job_id = job['id']
    job_data = job['data']

    user_parameters_str = job_data['actionConfiguration']['configuration'].get('UserParameters', '{}')
    user_parameters = json.loads(user_parameters_str)

    pr_id = user_parameters.get('PR_ID')
    repo_name = user_parameters.get('REPO_NAME')
    revisionId = user_parameters.get('revisionId')

    print(f"PR ID: {pr_id}")
    print(f"Repo Name: {repo_name}")
    print(f"Revision ID: {revisionId}")

    # Find LintingArtifact and BuildArtifact
    lint_artifact = None
    build_artifact = None
    for artifact in job_data['inputArtifacts']:
        if artifact['name'] == 'LintingArtifact':
            lint_artifact = artifact
            print(f"Found Linting Artifact: {lint_artifact}")
        elif artifact['name'] == 'BuildArtifact':
            build_artifact = artifact
            print(f"Found Build Artifact: {build_artifact}")

    s3 = boto3.client('s3')


    import io, zipfile
    lint_file_name = f"{pr_id}_linting_status.txt"
    tests_file_name = f"{pr_id}_tests_status.txt"

    # Read PR_ID-specific linting status file (plain text)
    lint_s3 = lint_artifact['location']['s3Location']
    print(f"Lint S3 Location: {lint_s3}")
    lint_response = s3.get_object(Bucket=lint_s3['bucketName'], Key=lint_s3['objectKey'])
    print(f"Lint S3 Response: {lint_response}")
    zipped_bytes = lint_response['Body'].read()
    print(f"Zipped Bytes Length: {len(zipped_bytes)}")

    # Unzip and read the lint result file
    with zipfile.ZipFile(io.BytesIO(zipped_bytes)) as z:
        with z.open(lint_file_name) as f:
            lint_result = f.read().decode('utf-8').strip()

    # Read PR_ID-specific tests status file (plain text)
    build_s3 = build_artifact['location']['s3Location']
    build_response = s3.get_object(Bucket=build_s3['bucketName'], Key=build_s3['objectKey'])
    zipped_bytes = build_response['Body'].read()

    with zipfile.ZipFile(io.BytesIO(zipped_bytes)) as z:
        with z.open(tests_file_name) as f:
            test_result = f.read().decode('utf-8').strip()

    # Approve only if both succeeded
    if lint_result == 'success' and test_result == 'success':
        approval_state = "APPROVE"
    else:
        approval_state = "REVOKE"

    codecommit.update_pull_request_approval_state(
        pullRequestId=pr_id,
        revisionId=revisionId,
        approvalState=approval_state
    )

    # codecommit.post_comment_for_pull_request(
    #     pullRequestId=pr_id,
    #     repositoryName=repo_name,
    #     beforeCommitId=revisionId,
    #     afterCommitId=revisionId,
    #     content=f"Automated review: Lint status = {lint_result}, Test status = {test_result}. PR {approval_state}D."
    # )

    # Tells AWS CodePipeline that the Lambda action (job) has completed successfully.
    # If you omit this call, the pipeline will consider the job incomplete or failed, 
    # and may eventually time out or mark the action as failed.
    codepipeline.put_job_success_result(jobId=job_id)
    print(f"PR {pr_id} {approval_state}D successfully")
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f'PR {pr_id} {approval_state}D successfully',
            'lint_status': lint_result,
            'test_status': test_result
        })
    }#
