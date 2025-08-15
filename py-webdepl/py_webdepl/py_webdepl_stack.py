from aws_cdk import (
    Stack,
    aws_s3,
    aws_cloudfront,
    aws_cloudfront_origins,
    aws_s3_deployment,
    CfnOutput
)
from constructs import Construct
import os


class PyWebdeplStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        deployment_bucket = aws_s3.Bucket(self, "PyDeploymentBucket",
                                          removal_policy=aws_cdk.RemovalPolicy.DESTROY,
                                          auto_delete_objects=True,
                                          )

        ui_dir = os.path.join(os.path.dirname(__file__),
                              '..', '..', 'web', 'dist')

        if not os.path.exists(ui_dir):
            print(f"UI directory not found: {ui_dir}")
            raise FileNotFoundError(f"UI directory not found: {ui_dir}")

        print(f"UI directory is: {ui_dir}")

        origin_identity = aws_cloudfront.OriginAccessIdentity(
            self, "PyOriginAccessIdentity")

        deployment_bucket.grant_read(origin_identity)

        distribution = aws_cloudfront.CloudFrontWebDistribution(
            self, "PyWebDeploymentDistribution",
            default_root_object="index.html",
            default_behavior=aws_cloudfront.BehaviorOptions(
                origin=aws_cloudfront_origins.S3Origin(
                    bucket=deployment_bucket,
                    origin_access_identity=origin_identity
                ),
            )
        )

        aws_s3_deployment.BucketDeployment(self, "PyWebDeploy",
                                            destination_bucket=deployment_bucket,
                                            sources=[
                                                aws_s3_deployment.Source.asset(ui_dir)
                                            ],
                                            distribution=distribution,
                                            )
        CfnOutput(self, "PyAppUrl",
                   value=f"https://{distribution.distribution_domain_name}",
                   description="URL of the deployed web application",
                   export_name="PyAppUrl"
                   )
        
        CfnOutput(self, "PyBucketName",
                   value=deployment_bucket.bucket_name,
                   description="Name of the S3 bucket used for deployment",
                   export_name="PyBucketName"
                   )
        
        CfnOutput(self, "PyDistributionId",
                   value=distribution.distribution_id,
                   description="ID of the CloudFront distribution",
                   export_name="PyDistributionId"
                   )
        
        CfnOutput(self, "PyOriginAccessIdentity",
                   value=origin_identity.origin_access_identity_id,
                   description="ID of the CloudFront Origin Access Identity",
                   export_name="PyOriginAccessIdentity"
                   )
        