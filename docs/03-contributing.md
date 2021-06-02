# Gitlab CE Operator - Contributing

For any problems with this charm, please [report bugs here](https://github.com/mkissam/charm-gitlab-ce-operator/issuest).

The code for this charm can be downloaded as follows:

```
git clone https://github.com/mkissam/charm-gitlab-ce-operator.git
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
