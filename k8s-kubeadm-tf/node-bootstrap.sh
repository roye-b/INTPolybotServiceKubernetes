#!/bin/bash

# install jq, awscli and ecr-credentials-helper (for those who store images in ECR)
apt-get update
apt-get install jq unzip -y

# install awscli
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# sysctl params required by setup, params persist across reboots
cat <<EOF | tee /etc/sysctl.d/k8s.conf
net.ipv4.ip_forward = 1
EOF

# apply sysctl params without reboot
sysctl --system

# install cri-o kubelet kubeadm kubectl
KUBERNETES_VERSION=${k8s_version}
PROJECT_PATH=prerelease:/main

curl -fsSL https://pkgs.k8s.io/core:/stable:/$KUBERNETES_VERSION/deb/Release.key | gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo "deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/$KUBERNETES_VERSION/deb/ /" | tee /etc/apt/sources.list.d/kubernetes.list

curl -fsSL https://pkgs.k8s.io/addons:/cri-o:/$PROJECT_PATH/deb/Release.key | gpg --dearmor -o /etc/apt/keyrings/cri-o-apt-keyring.gpg
echo "deb [signed-by=/etc/apt/keyrings/cri-o-apt-keyring.gpg] https://pkgs.k8s.io/addons:/cri-o:/$PROJECT_PATH/deb/ /" | tee /etc/apt/sources.list.d/cri-o.list

apt-get update
apt-get install -y software-properties-common apt-transport-https ca-certificates curl gpg
apt-get install -y cri-o kubelet kubeadm kubectl
apt-mark hold kubelet kubeadm kubectl

# start the container runtime
systemctl start crio.service
systemctl enable --now crio.service
systemctl enable --now kubelet

# update kubelet extra args
KUBELET_DEFAULTS_FILE="/etc/default/kubelet"
EXTRA_ARGS="--cloud-provider=external --image-credential-provider-bin-dir=/usr/local/bin/ --image-credential-provider-config=/etc/kubernetes/ecr-credential-provider-config.yaml"
if grep -q "KUBELET_EXTRA_ARGS" "$KUBELET_DEFAULTS_FILE"; then
  if ! grep -q -- "$EXTRA_ARGS" "$KUBELET_DEFAULTS_FILE"; then
      echo "$(cat $KUBELET_DEFAULTS_FILE)\"$EXTRA_ARGS\"" | sudo tee "$KUBELET_DEFAULTS_FILE"
  fi
else
    echo "KUBELET_EXTRA_ARGS=\"$EXTRA_ARGS\"" | sudo tee "$KUBELET_DEFAULTS_FILE"
fi

# create CredentialProviderConfig for ECR users
curl -Lo /usr/local/bin/ecr-credential-provider https://artifacts.k8s.io/binaries/cloud-provider-aws/v1.29.0/linux/amd64/ecr-credential-provider-linux-amd64
chmod +x /usr/local/bin/ecr-credential-provider
cat <<EOF > /etc/kubernetes/ecr-credential-provider-config.yaml
apiVersion: kubelet.config.k8s.io/v1
kind: CredentialProviderConfig
providers:
  - name: ecr-credential-provider
    matchImages:
      - "*.dkr.ecr.*.amazonaws.com"
    defaultCacheDuration: "12h"
    apiVersion: credentialprovider.kubelet.k8s.io/v1
EOF

# change hostname to a full form
hostname | grep -E '^ip-[0-9]{1,3}-[0-9]{1,3}-[0-9]{1,3}-[0-9]{1,3}$' &&  hostnamectl set-hostname $(hostname).${aws_region}.compute.internal

# disable swap memory
swapoff -a

# add the command to crontab to make it persistent across reboots
(crontab -l ; echo "@reboot /sbin/swapoff -a") | crontab -

