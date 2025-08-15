from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_s3_deployment as s3deploy,
    aws_iam as iam,
    CfnOutput
)
from constructs import Construct
import os


class PyWebdeplStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # S3 bucket for deployment
        deployment_bucket = s3.Bucket(
            self, "PyDeploymentBucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # Path to UI build output
        ui_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'web', 'dist')
        if not os.path.exists(ui_dir):
            raise FileNotFoundError(f"UI directory not found: {ui_dir}")
        print(f"UI directory is: {ui_dir}")

        # Create Origin Access Control (OAC)
        origin_access_control = cloudfront.CfnOriginAccessControl(
            self, "PyOriginAccessControl",
            origin_access_control_config=cloudfront.CfnOriginAccessControl.OriginAccessControlConfigProperty(
                name="PyOriginAccessControlConfig",
                origin_access_control_origin_type="s3",
                signing_behavior="always",
                signing_protocol="sigv4"
            )
        )

        # CloudFront distribution
        distribution = cloudfront.Distribution(
            self, "PyWebDeploymentDistribution",
            default_root_object="index.html",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3BucketOrigin(
                    deployment_bucket,
                    origin_access_control_id=origin_access_control.attr_id
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            )
        )

        # Grant CloudFront access to S3
        deployment_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                sid="AllowCloudFrontServicePrincipal",
                effect=iam.Effect.ALLOW,
                principals=[iam.ServicePrincipal("cloudfront.amazonaws.com")],
                actions=["s3:GetObject"],
                resources=[f"{deployment_bucket.bucket_arn}/*"],
                conditions={
                    "StringEquals": {
                        "AWS:SourceArn": f"arn:aws:cloudfront::{self.account}:distribution/{distribution.distribution_id}"
                    }
                }
            )
        )

        # Deploy UI build to S3 and invalidate CloudFront cache
        s3deploy.BucketDeployment(
            self, "PyWebDeploy",
            destination_bucket=deployment_bucket,
            sources=[s3deploy.Source.asset(ui_dir)],
            distribution=distribution,
            distribution_paths=["/*"]
        )

        # Outputs
        CfnOutput(
            self, "PyAppUrl",
            value=f"https://{distribution.distribution_domain_name}",
            description="URL of the deployed web application",
            export_name="PyAppUrl"
        )
        CfnOutput(
            self, "PyBucketName",
            value=deployment_bucket.bucket_name,
            description="Name of the S3 bucket used for deployment",
            export_name="PyBucketName"
        )
        CfnOutput(
            self, "PyDistributionId",
            value=distribution.distribution_id,
            description="ID of the CloudFront distribution",
            export_name="PyDistributionId"
        )
        CfnOutput(
            self, "PyOriginAccessControlId",
            value=origin_access_control.attr_id,
            description="ID of the CloudFront Origin Access Control",
            export_name="PyOriginAccessControlId"
        )
