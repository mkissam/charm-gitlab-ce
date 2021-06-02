# Gitlab Community Edition Operator

A juju operator charm for a Kubernetes deployment and operation of GitLab
Community Edition.

Charmhub page: https://charmhub.io/gitlab-ce-operator  
Documentation: https://charmhub.io/gitlab-ce-operator/docs  
Bugs / Issues: https://github.com/mkissam/charm-gitlab-ce-operator/issues

## Description

GitLab is the de-facto open-source standard for a hosted Git repository manager,
wiki, issue-tracking and continuous integration and deployment pipeline features.
This operator charm is using the official GitLab docker image (gitlab/gitlab-ce)
as a source for deployment.

The default configuration used for this charm is providing the 
internal gitlab services included in the all-in-one gitlab-ce image.

## Quickstart

Assuming you have a juju installed and bootstrapped on a Kubernetes cluster,
deploy the charm and relate it to an ingress controller (if you do not, see the
next section):

```bash
# Deploy the GitLab CE charm
$ juju deploy gitlab-ce-operator gitlab-ce \
    --config external_url="gitlab-ce-demo.juju"

# Deploy the ingress integrator charm
$ juju deploy nginx-ingress-integrator ingress \
    --config ingress-class="public"

# Relate gitlab-ce and ingress integrator
$ juju relate gitlab-ce:ingress ingress:ingress

# Add an entry to /etc/hosts
$ echo "127.0.1.1 gitlab-ce-demo.juju" | sudo tee -a /etc/hosts

# Wait for the deployment to complete
$ watch -n1 --color juju status --color
```

Open the http://gitlab-ce-demo.juju url in your browser, and register a new
administrator password. You can login now as 'root' using the new password.

## Development Setup

To set up a local test environment with [MicroK8s](https://microk8s.io):

```bash
# Install MicroK8s
$ sudo snap install --classic microk8s

# Wait for MicroK8s to be ready
$ sudo microk8s status --wait-ready

# Enable features required by Juju controller & charm
$ sudo microk8s enable storage dns ingress

# (Optional) Alias kubectl bundled with MicroK8s package
$ sudo snap alias microk8s.kubectl kubectl

# (Optional) Add current user to 'microk8s' group
# This avoid needing to use 'sudo' with the 'microk8s' command
$ sudo usermod -aG microk8s $(whoami)

# Activate the new group (in the current shell only)
# Log out and log back in to make the change system-wide
$ newgrp microk8s

# Install Charmcraft
$ sudo snap install charmcraft

# Install juju
$ sudo snap install --classic juju

# Bootstrap the Juju controller on MicroK8s
$ juju bootstrap microk8s micro

# Add a new model to Juju
$ juju add-model development
```

## Build and Deploy Locally

```bash
# Clone the charm code
$ git clone https://github.com/mkissam/charm-gitlab-ce-operator && cd charm-gitlab-ce-operator

# Build the charm package
$ charmcraft pack

# Deploy!
$ juju deploy ./gitlab-ce-operator.charm gitlab-ce \
    --resource gitlab-image=gitlab/gitlab-ce \
    --config external_url="gitlab-ce-demo.juju"

# Deploy the ingress integrator
$ juju deploy nginx-ingress-integrator ingress \
    --config ingress-class="public"

# Relate our app to the ingress
$ juju relate gitlab-ce:ingress ingress:ingress

# Add an entry to /etc/hosts
$ echo "127.0.1.1 gitlab-ce-demo.juju" | sudo tee -a /etc/hosts

# Wait for the deployment to complete
$ watch -n1 --color juju status --color
```

## Running tests

```bash
# Clone the charm code
$ git clone https://github.com/mkissam/charm-gitlab-ce-operator && cd charm-gitlab-ce-operator

# Install python3-virtualenv
$ sudo apt update && sudo apt install -y python3-virtualenv

# Create a virtualenv for the charm code
$ virtualenv venv

# Activate the venv
$ source ./venv/bin/activate

# Install dependencies
$ pip install -r requirements-dev.txt

# Run the tests
$ ./run_tests
```

## TODO/Roadmap

See docs/04-future-plans.md for details.
