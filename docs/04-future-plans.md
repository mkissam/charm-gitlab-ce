# Gitlab CE Operator - Future Plans

As this operator charm is a work in progress, the following roadmap items
must be implemented for a production-grade quaility charm.


## Implements external postgresql relation

The gitlab/gitlab-ce image is using the built-in progress database. The
following documentation explains the environment variables required for
external postgresql database configuration: 
https://docs.gitlab.com/ee/administration/postgresql/external.html

```
# Disable the bundled Omnibus provided PostgreSQL
postgresql['enable'] = false

# PostgreSQL connection details
gitlab_rails['db_adapter'] = 'postgresql'
gitlab_rails['db_encoding'] = 'unicode'
gitlab_rails['db_host'] = '10.1.0.5' # IP/hostname of database server
gitlab_rails['db_password'] = 'DB password'
```

The postgresql data must be retrieved through a shared-db relation.


## Provide SSH access in ingress

The current charm configuration is passing through the http 80 port only,
and ssh git repositories are not accessible. The port 22 must be opened through
ingress.

## Retrieve administrator account password using an action

Currently the first step of GitLab Web UI login is the root user password
creation. The password should be a random password, and retrieved by the
get-initial-password action.

```
juju run gitlab-ce --wait get-initial-password
```

## Implement external redis support

The current configuration is using the built-in redis. It must be disabled
the same way as postgresql, and provide a redis access through a relation.

## Add charm unit tests

Implement unit tests.

## Build a gitlab-runner charm and relation

To provide CI/CD pipeline features, a gitlab-runner operator charm must be
implemented with a relation to gitlab-ce-operator.


## Improve state handling

Similar to other charm implementations, the state of the long-running
gitlab-installer must be represented in Juju status. Usual warm-up time
is between 2-3 minutes.
