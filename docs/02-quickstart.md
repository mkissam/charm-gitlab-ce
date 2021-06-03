# Gitlab CE Operator - Quickstart

Assuming you have a juju installed and bootstrapped on a Kubernetes cluster,
deploy the charm and relate it to an ingress controller:

```bash
# Deploy the GitLab CE charm
$ juju deploy gitlab-ce

# Deploy the ingress integrator charm
$ juju deploy nginx-ingress-integrator ingress

# Relate gitlab-ce and ingress integrator
$ juju relate gitlab-ce:ingress ingress:ingress

# Add an entry to /etc/hosts
$ echo "127.0.1.1 gitlab-ce" | sudo tee -a /etc/hosts

# Wait for the deployment to complete
$ watch -n1 --color juju status --color
```

Open the `http://gitlab-ce` URL in your browser, and register a new
administrator password. You can login now as 'root' using the new password.

