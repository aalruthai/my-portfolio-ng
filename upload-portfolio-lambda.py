import boto3
from io import BytesIO
import zipfile
import mimetypes

def lambda_handler(event, context):
    sns = boto3.resource('sns')
    topic = sns.Topic('arn:aws:sns:us-east-1:243485805400:deployPortfolioTopic')
    codepipeline = boto3.client('codepipeline')
    location = {
        "bucketName":"portfoliobuild.amr",
        "objectKey":"portfoliobuild.zip"
    }
    try:
        job = event.get("CodePipeline.job")
        if job:
            for artifact in job["data"]["inputArtifacts"]:
                if artifact["name"] == "MyAppBuild":
                    location = artifact["location"]["s3Location"]
                    
        print("Building Portfolio from " + str(location))
        s3 = boto3.resource('s3')
        portfolio_bucket = s3.Bucket('portfolio.amr')
        
        build_bucket = s3.Bucket(location["bucketName"])
        
        portfolio_zip = BytesIO()
        build_bucket.download_fileobj(location["objectKey"],portfolio_zip)
        
        with zipfile.ZipFile(portfolio_zip) as myzip:
            for nm in myzip.namelist():
                obj = myzip.open(nm)
                portfolio_bucket.upload_fileobj(obj,nm, ExtraArgs={'ContentType':mimetypes.guess_type(nm)[0]})
                portfolio_bucket.Object(nm).Acl().put(ACL='public-read')
        print("Job Done!")
        topic.publish(Subject="Portfolio Depolyed",Message="Portfolio deployed successfully")
        if job:
            
            codepipeline.put_job_success_result(jobId=job["id"])
    except:
        
        topic.publish(Subject="Portfolio Deployment Failed",Message="The Portfolio Deployement Failed")
        if job:
            codepipeline.put_job_failure_result(jobId=job["id"])
        raise
    return 'Hello from Lambda'
