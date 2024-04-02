import os
import boto3

s3_client = boto3.client(
    's3',
    region_name=os.getenv("AWS_S3_REGION"),
    aws_access_key_id=os.getenv("AWS_S3_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("AWS_S3_SECRET_KEY"),
)


def generate_pre_signed_url(media_key):
    """
    Method to get pre-signed url for getting data.
    """
    if media_key:
        url = s3_client.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': os.getenv("AWS_S3_BUCKET_NAME"),
                'Key': media_key,
                'ResponseContentDisposition': 'inline',
            },
            ExpiresIn=86400,
        )
        return url
    return None


def generate_upload_signed_url(media_key):
    """
    Method to get pre-signed url for uploading data.
    """
    url = s3_client.generate_presigned_url(
        ClientMethod='put_object',
        Params={
            'Bucket': os.getenv("AWS_S3_BUCKET_NAME"),
            'Key': media_key
        },
        ExpiresIn=60,
    )
    return url
