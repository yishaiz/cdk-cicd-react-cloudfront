from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_s3,
    aws_cloudfront,
    aws_cloudfront_origins,
    aws_s3_deployment,
    CfnOutput
)
import aws_cdk as cdk

from constructs import Construct
import os


class PyWebdeplStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        deployment_bucket = aws_s3.Bucket(self, "PyDeploymentBucket",
                                          removal_policy=RemovalPolicy.DESTROY,
                                          auto_delete_objects=True,
                                          )

        ui_dir = os.path.join(os.path.dirname(__file__),
                              '..', '..', 'web', 'dist')

        if not os.path.exists(ui_dir):
            print(f"UI directory not found: {ui_dir}")
            raise FileNotFoundError(f"UI directory not found: {ui_dir}")

        print(f"UI directory is: {ui_dir}")

        origin_access_control = aws_cloudfront.S3OriginAccessControl(
            self, "PyOriginAccessControl"
        )

        distribution = aws_cloudfront.Distribution(
            self, "PyWebDeploymentDistribution",
            default_root_object="index.html",
            default_behavior=aws_cloudfront.BehaviorOptions(
                origin=aws_cloudfront_origins.S3Origin(
                    bucket=deployment_bucket,
                    origin_access_control=origin_access_control
                ),
                viewer_protocol_policy=aws_cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            )
        )

        # Grant CloudFront access to the S3 bucket
        deployment_bucket.add_to_resource_policy(
            aws_s3.PolicyStatement(
                sid="AllowCloudFrontServicePrincipal",
                effect=aws_s3.Effect.ALLOW,
                principals=[aws_s3.ServicePrincipal(
                    "cloudfront.amazonaws.com")],
                actions=["s3:GetObject"],
                resources=[f"{deployment_bucket.bucket_arn}/*"],
                conditions={
                    "StringEquals": {
                        "AWS:SourceArn": f"arn:aws:cloudfront::{self.account}:distribution/{distribution.distribution_id}"
                    }
                }
            )
        )

        aws_s3_deployment.BucketDeployment(self, "PyWebDeploy",
                                           destination_bucket=deployment_bucket,
                                           sources=[
                                               aws_s3_deployment.Source.asset(
                                                   ui_dir)
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

        CfnOutput(self, "PyOriginAccessControlId",
                  value=origin_access_control.origin_access_control_id,
                  description="ID of the CloudFront Origin Access Control",
                  export_name="PyOriginAccessControlId"
                  )
