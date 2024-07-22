terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  required_version = ">= 1.2.0"
}


provider "aws" {
  region  = var.aws_region
}


resource "aws_instance" "control_plane" {
  ami                    = var.ami_id
  instance_type          = var.instance_type
  subnet_id              = var.public_subnet_ids[0]
  vpc_security_group_ids = var.control_plane_sg_ids
  key_name               = var.key_pair_name
  iam_instance_profile   = var.control_plane_iam_role

  tags = {
    Name = "${var.cluster_name}-control-plane"
    "kubernetes.io/cluster/${var.cluster_name}" = "owned"
  }

  root_block_device {
    volume_size = 20
  }

  user_data = templatefile("./node-bootstrap.sh", {
    aws_region = var.aws_region
    k8s_version = var.k8s_version
  })
}


resource "aws_instance" "worker_node" {
  # number of worker nodes to provision
  count = 1

  ami                    = var.ami_id
  instance_type          = var.instance_type
  subnet_id              = var.public_subnet_ids[count.index % length(var.public_subnet_ids)]
  vpc_security_group_ids = var.worker_node_sg_ids
  key_name               = var.key_pair_name
  iam_instance_profile   = var.worker_node_iam_role

  tags = {
    Name = "${var.cluster_name}-worker-node-${count.index}"
    "kubernetes.io/cluster/${var.cluster_name}" = "owned"
  }

  root_block_device {
    volume_size = 20
  }

  user_data = templatefile("./node-bootstrap.sh", {
    aws_region = var.aws_region
    k8s_version = var.k8s_version
  })
}