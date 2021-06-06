# sshproxy

## Description

SSHProxy Charm example for Open Source MANO.

The purpose of this charm is to operate a VNF via SSH. For this, the charm should know the hostname of the VNF (ip address), and the username. The charm will be in a blocked state until it has the hostname, username, and the credentials for SSH-ing to the VNF. Both hostname and username are set via config, with `ssh-hostname` and `ssh-username` respectively.

There are two ways of specifying the credentials: password, keys. (See next section)

The charm is also able to clone git repositories and do deploys using docker and docker-compose.
The various actions related to this functionaties will be shown below.

To see all the steps needed to make the deployment of a application using this charm, go to the bottom of this page.


## Usage

This charm works for both LXD and K8s. By default, it will work on LXD. To make it work in K8s, just change the following in the `metadata.yaml`

```yaml
series:
# - focal
# - bionic
# - xenial
 - kubernetes
 deployment:
    mode: operator
```

### Prepare the environment:

- LXD:

```bash
sudo snap install juju --classic
juju bootstrap lxd
juju add-model test
```

- K8s:

```bash
sudo snap install juju --classic
sudo snap install microk8s --classic
sudo microk8s.status --wait-ready
sudo microk8s.enable storage dns
juju bootstrap microk8s
juju add-model test
```

### Prepare the environment (when using xenial series):
```bash
mkdir -p charms/samplecharm/
cd charms/samplecharm/
mkdir hooks lib mod src
touch src/charm.py
touch actions.yaml metadata.yaml config.yaml
chmod +x src/charm.py
ln -s ../src/charm.py hooks/upgrade-charm
ln -s ../src/charm.py hooks/install
ln -s ../src/charm.py hooks/start
git clone https://github.com/canonical/operator mod/operator
git clone https://github.com/charmed-osm/charms.osm mod/charms.osm
ln -s ../mod/operator/ops lib/ops
ln -s ../mod/charms.osm/charms lib/charms
```


### Deploying charm:

```bash
charmcraft build
juju deploy ./sshproxy.charm --config <file> --series <xenial|focal|...>
```

### Configuring the charm:
#### No need to make this step if a config file was used previously
First of all, set the username and hostname of the VNF:
```bash
juju config sshproxy ssh-hostname=<hostname> \
                     ssh-username=<username>
```

### Credentials

There are two ways to set up the credentials for the charm to be able to SSH the VNF.

With password:

```bash
juju config sshproxy ssh-password=<password>
```

With public keys:

1. First get the public key from the charm

```bash
$ juju run-action sshproxy/0 get-ssh-public-key --wait
unit-sshproxy-0:
  UnitId: sshproxy/0
  id: "12"
  results:
    pubkey: |
      ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQC0IgSXMsu/5tY9QjsQfiAqcs6MBMO/7BDJB1ohbJFfvFrPiGg3+5FohKOsgu3SPiZbBhTITmI1YdaiZK7Dye2tHUfQKXhPFVFFVRtyWG6U/QJqEn+6OvAhjladcBlah4cb//r8V2Lvk/PshBJPzgvYSNJOhMhpfAMc7SMMpS8VxGBDIuTE0JFlHcRALJy3YBg70DPea2xrLsxqfA2pTA33KcjK2GyLgfOcZavmkqudEA/WaFb0xCY16TB/hDQBSwZm3l2kJ2aHyAWyWMmLNGL0TT14HUQKR1a8NS/kAnKY/yQf04dKoicmCvl4B3ndIYFT5Pq9b07mVfZvEH5Blle/x48iUF6JHWH2383SXwZfGy3XcX+lRx3u+IIkzS/Pmgt175JVdpu8bktk1c3Ekc0aL9v1gJ8rmZo+C6cilBoaziPfbqIatGPeGxnTDdw0JSfpxUGIQF4H98VOdWf3cHGC1hJZubZt0MGYeK4bk7GfsVPMlGaBWDyTaBQ5d9dHGxJpJX5OMBCDD4MfBYvg9IlgsVr1vDbpB4OFoAmQqFgnUWxRg2w0Iv3HBeMCvvOMM7DBOjwgjgbwa693Oyt/Rxd3GOwvy6vRQkFTgVS6f69SyIMCj9aIl1zxkIcOsfM5aU6vgio1BVWt9Xrj1TA3dTYJ7fkC5LJetqJ1knO67u67ww== root@juju-73fac6-2
  status: completed
  timing:
    completed: 2020-11-18 15:42:03 +0000 UTC
    enqueued: 2020-11-18 15:42:00 +0000 UTC
    started: 2020-11-18 15:42:03 +0000 UTC
```
2. Inject that key in `~/.ssh/authorized_keys` at the VNF
3. Verify the ssh credentials

```bash
$ juju run-action sshproxy/0 verify-ssh-credentials --wait
unit-sshproxy-0:
  UnitId: sshproxy/0
  id: "14"
  results:
    verified: "True"
  status: completed
  timing:
    completed: 2020-11-18 15:39:30 +0000 UTC
    enqueued: 2020-11-18 15:39:29 +0000 UTC
    started: 2020-11-18 15:39:29 +0000 UTC
```

## Git actions

1. clone-github-repository

    - this actions clones a repository to the VM associated with the VNF service

    - usage : juju run-action sshproxy/<?> clone-github-repository repository-url=\<url> app-name=\<appname (we will use appexample further on)>

2. update-repository

    - this actions updates the repository on the VM associated with the VNF service

    - usage : juju run-action sshproxy/<?> update-repository app-name=appexample

3. delete-repository

    - this actions deletes the repository on the VM associated with the VNF service

    - usage : juju run-action sshproxy/<?> delete-repository app-name=appexample

## Docker and Docker-compose actions

1. run-app

    - this actions builds and runs a application on the VM associated with the VNF service

    - juju run-action sshproxy/<?> run-app app-name=appexample

2. stop-app

    - this actions stops a application on the VM associated with the VNF service
    
    - juju run-action sshproxy/<?> stop-app app-name=appexample

3. start-app

    - this actions starts again a application on the VM associated with the VNF service
    
    - juju run-action sshproxy/<?> run-app start-name=appexample

4. remove-app

    - this actions removes entirely a application on the VM associated with the VNF service (the git repository continues to be available)
    
    - juju run-action sshproxy/<?> remove-app app-name=appexample


## Developing

Create and activate a virtualenv with the development requirements:

    virtualenv -p python3 venv
    source venv/bin/activate
    pip install -r requirements-dev.txt

## Testing

The Python operator framework includes a very nice harness for testing
operator behaviour without full deployment. Just `run_tests`:

    ./run_tests

## Deploy a app (full guide)

1. Implement the charm

2. Build the charm

    - ```$ charmcraft build ```

3. Deploy charm

    - local.yaml is the file where we can find the characteristics of the ssh connection

    - it is not mandatory to use xenial series, on the momment that this explanation is being made, xenial series is a constraint associated with osm charms

    - ```$ juju deploy ./sshproxy.charm --config local.yaml --series xenial ```

4. Install the necessary dependencies on the VM related to the VNF service

    - supposing the unit has the name sshproxy/0

    - ```$ juju run-action sshproxy/0 start ```

5. Clone a git repository to the VM related to the VNF service

    - ```$ juju run-action sshproxy/0 clone-github-repository repository-url=https://github.com/5g-mobility/django-juju-demo.git app-name=django```

6. Run the django app

    - ```$ juju run-action sshproxy/0 run-app app-name=django```

7. Make all the necessary changes using the actions explained before

8. Stop the services of the VNF

    - With this step the vm erases all the docker dependencies and also the git repositories that may exist

    - ```$ juju run-action sshproxy/0 stop```