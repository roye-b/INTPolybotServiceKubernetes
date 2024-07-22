variable "k8s_version" {
    description = "The version of Kubernetes to deploy. Defaults to v1.30."
    type = string
    default = "v1.30"
}

variable "cluster_name" {
    description = "The name of your Kubernetes cluster (any name to your choice)"
    type = string
}

variable "aws_region" {
    description = "The AWS region to deploy in"
    type = string
}

variable "ami_id" {
    description = "The ID of the AMI to use for the nodes"
    type = string
}

variable "public_subnet_ids" {
    description = "List of public subnet IDs"
    type = list(string)
}

variable "control_plane_iam_role" {
    description = "The IAM role to attach to the control-plane node"
    type = string
}

variable "control_plane_sg_ids" {
    description = "The IDs of the security groups to attach to the control-plane node"
    type = list(string)
}

variable "worker_node_iam_role" {
    description = "The IAM role to attach to the worker nodes"
    type = string
}

variable "worker_node_sg_ids" {
    description = "The IDs of the security groups to attach to the worker nodes"
    type = list(string)
}

variable "key_pair_name" {
    description = "The name of the key pair to use for the instance"
    type = string
}

variable "instance_type" {
    description = "The type of instance to use"
    type = string
    default = "t3.medium"
}



