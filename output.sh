#!/bin/bash

# Create S3 bucket
aws s3api create-bucket --bucket my-s3-bucket-762233773660 --region us-west-2 --create-bucket-configuration LocationConstraint=us-west-2

# Create EC2 instance
aws ec2 run-instances --image-id ami-0c55b159cbfafe1f0 --count 1 --instance-type t2.micro --key-name my-key-pair --security-group-ids sg-0123456789abcdef0 --subnet-id subnet-0123456789abcdef0 --region us-west-2

# Create EFS file system
aws efs create-file-system --performance-mode generalPurpose --throughput-mode bursting --encrypted --region us-west-2

# Create mount target for EFS
aws efs create-mount-target --file-system-id fs-0123456789abcdef0 --subnet-id subnet-0123456789abcdef0 --security-groups sg-0123456789abcdef0 --region us-west-2