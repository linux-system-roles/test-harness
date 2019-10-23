# Integration Tests for Linux System Roles

[![Build Status](https://travis-ci.org/linux-system-roles/test-harness.svg?branch=master)](https://travis-ci.org/linux-system-roles/test-harness)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

## Commands

The CI system can be controlled with a few commands as comments in pull requests:

* `[citest]` - Trigger a re-test for all machines
* `[citest bad]` - Trigger a re-test for all machines with an error or failure status
* `[citest pending]` - Trigger a re-test for all machines with a pending status
* `[citest commit:<sha1>]` - Whitelist a commit to be tested if the submitter is not trusted

It is also possible to whitelist all commits in a PR with the `needs-ci` tag.
However, this should be only used with trusted submitters since they can still
change the commits in the PR.

## Installation

A docker container which runs integration tests for open pull requests on
[linux system roles](https://linux-system-roles.github.io) repositories. It runs
all playbooks `test/test_*.yml` of the repository against various virtual
machines.

To build the container, run

```
sudo docker build -t linuxsystemroles/test-harness:latest .
```

Multiple of these containers can be started in parallel. They try to not step
on each others feet by synchronizing via GitHub commit statuses.

The test runner needs a `config.json` in the `/config` mount, which specifies
the repositories to monitor for open pull requests, the cloud images to use,
a location where to copy (via ssh) the test results to, and a publicly
accessible URL for these results. For example:

```json
{
  "repositories": [
    "linux-system-roles/network",
    "linux-system-roles/selinux",
    "linux-system-roles/timesync",
    "linux-system-roles/tuned",
    "linux-system-roles/kdump",
    "linux-system-roles/firewall",
    "linux-system-roles/postfix"
  ],
  "images": [
    {
      "name": "fedora-27",
      "source": "https://download.fedoraproject.org/pub/fedora/linux/releases/27/CloudImages/x86_64/images/Fedora-Cloud-Base-27-1.6.x86_64.qcow2",
      "upload_results": true,
      "setup": "dnf install -yv python2 python2-dnf libselinux-python"
    },
    {
      "name": "fedora-28",
      "source": "https://download.fedoraproject.org/pub/fedora/linux/releases/28/Cloud/x86_64/images/Fedora-Cloud-Base-28-1.1.x86_64.qcow2",
      "upload_results": true,
      "setup": [
        {
          "name": "Setup",
          "hosts": "all",
          "become": true,
          "gather_facts": false,
          "tasks": [
            {"raw": "dnf install -yv python2 python2-dnf libselinux-python"}
          ]
        }
      ]
    },
    {
      "name": "centos-6",
      "source": "https://cloud.centos.org/centos/6/images/CentOS-6-x86_64-GenericCloud-1804_02.qcow2c",
      "upload_results": true
    },
    {
      "name": "centos-7",
      "source": "https://cloud.centos.org/centos/7/images/CentOS-7-x86_64-GenericCloud-1804_02.qcow2c",
      "upload_results": true
    }
  ],
  "results": {
    "destination": "user@example.org:public_html/logs",
    "public_url": "https://example.com/logs"
  }
}
```

The `setup` key contains either a list of Ansible plays which will be saved as
a playbook and executed before the test run, or a single shell command which
will be executed using the Ansible `raw` module (so the two examples above are
exactly equivalent).

The container needs a `/secrets` mount, which must contain these files:

* `github-token`: A GitHub access token with `public_repo`, `repo:status` and
  `read:org` scopes. The `read:org` permission is required to identify users as
  members to organiziations in case they set their organization membership to
  private. Without it, the test harness can still update CI status but might
  ignore pull requests or command comments unexpectedly.
* `id_rsa` and `id_rsa.pub`: A ssh key with to access the server in
  `results.destination`.
* `known_hosts`: A ssh `known_hosts` file which contains the public key of that
  server.

The test runner writes images into the `/cache` mount and reuses existing ones.

The container must have access to `/dev/kvm` for fast virtualization.

## Running on OpenShift

In this section we first describe how to setup an OpenShift environment and run
the CI system on it. Then we give several tips concerning maintenance the
entire system and backing up important data.

### Preparing OpenShift Environment and Running the CI System on it

In our use case, we create OpenShift project with two deployments. The first
one will be used for testing and will be based on
[stable version](https://github.com/linux-system-roles/test-harness/tree/master)
of the CI. The second one, based on
[staging version](https://github.com/linux-system-roles/test-harness/tree/staging)
of the CI, will be used to test new features of the CI before they will become
part of the stable version (i.e. before merging them into the
[master branch](https://github.com/linux-system-roles/test-harness/tree/master)).

Before start, get the `config.json` and `config-staging.json`. Then create an
empty directory and put the secrets inside it (files `github-token`, `id_rsa`,
`id_rsa.pub` and `known_hosts` discussed before). The requirements put on
`config{,-staging}.json` and secrets were discussed above.

In what follows, suppose you have set following environment variables:

* `PROJECT_NAME`: A name of OpenShift project.
* `CONFIG_PATH`: A path to `config.json`.
* `CONFIG_STAGING_PATH`: A path to `config-staging.json`.
* `SECRETS_PATH`: A path to the directory with secrets.

First, you need to be logged on (replace `[URL]` with a real URL of your
OpenShift server):

```
$ oc login [URL]
```

Now, you can create a fresh OpenShift project:

```
$ oc new-project ${PROJECT_NAME} --display-name=${PROJECT_NAME}
```

The `--display-name` parameter is optional and it is what is displayed in
OpenShift web console.

If you have already OpenShift project created and you want to use it, you can
select it by typing:

```
$ oc project ${PROJECT_NAME}
```

Now its time to create objects. Type:

```
$ oc create -f ./openshift-objects.yml
```

This will create `ServiceAccount` object named `tester` and `ImageStream` and
`DeploymentConfig` objects both named `linux-system-roles` for us, just as they
are specified in `./openshift-objects.yml`. Be careful: if some of the object
does exist so far, the `create` command ends with an error. In this case, you
can use `replace` command to just replace the existing object (suppose that
`./openshift-object.yml` contains a specification of object to be replaced):

```
$ oc replace -f ./openshift-object.yml
```

Because we need also staging deployment, lets create `DeploymentConfig` object
named `linux-system-roles-staging`:

```
$ oc create -f ./openshift-objects-staging.yml
```

**Note:** If `ImageStream` was created from an older version of
`./openshift-objects.yml`, it is possible that `staging` tag is missing. To
check this, please type (`is` refers to `ImageStreams` resource,
`linux-system-roles` is the name of `ImageStream` we want to inspect):

```
$ oc get is linux-system-roles -o jsonpath='{range .spec.tags[*]}{.name}{"\n"}{end}'
latest
staging
$
```

If you are not seeing `staging` in the above command output, then you must add
`staging` tag by yourself. To do this, type:

```
$ ./add-staging-tag linux-system-roles
```

and now you should have `staging` tag in your `linux-system-roles` image
stream.

The CI system launches virtual machines (VMs for short), so the container
needs to have `/dev/kvm` device (in other words, the container must be
privileged). Containers are launched using service account named `tester`.
Such account must be present in a list of privileged account. If you are
a cluster-admin, you can simply type

```
$ oc edit scc privileged
```

and then add under the `users` list a user with the name `tester`. Please keep
the following format for items in the `users` list:

```
system:serviceaccount:${PROJECT_NAME}:tester
```

**Tip:** `oc edit` will open file to be edited in `vi`, which is a default
editor. To change this behavior, set `OC_EDITOR` environment variable to point
to your favorite editor.

If you are done with editing, the snippet from your editor should looks like
this (if you named your project `lsr-test-harness`):

```yaml
users:
  - system:serviceaccount:lsr-test-harness:tester
```

After you save and quit the editor, `tester` should become the new privileged
user. You can check this with

```
$ oc get scc -o jsonpath='{range .items[?(.allowPrivilegedContainer==true)].users[*]}{@}{"\n"}{end}' | grep -Ee ':tester$'
system:serviceaccount:lsr-test-harness:tester
$
```

If you are not a cluster-admin, ask someone more powerful to make `tester`
privileged user for you.

Some OpenShift servers selects nodes in which deployments should run according
to node selectors. For example, if you need to run your deployments on bare
metal node and OpenShift server selects such a node for deployments that have
node selector set to `system-roles-ci = "true"`, run the following command for
both `linux-system-roles` and `linux-system-roles-staging` deployment configs:

```
$ ./apply-node-selectors linux-system-roles
$ ./apply-node-selectors linux-system-roles-staging
```

If you need to run containers as a root, run:

```
$ ./grant-root-privileges linux-system-roles
$ ./grant-root-privileges linux-system-roles-staging
```

Now its time to create `ConfigMap` and `Secret` objects. This will create two
`ConfigMap` objects named `config` and `config-staging` and one `Secret` object
named `secrets`:

```
$ oc create configmap config --from-file=${CONFIG_PATH}
$ oc create configmap config-staging --from-file=${CONFIG_STAGING_PATH}
$ oc create secret generic secrets --from-file=${SECRETS_PATH}
```

Once all required objects are created, import the images to kick up our
deployments:

```
$ oc import-image linux-system-roles
$ oc import-image linux-system-roles:staging
```

Congratulations! Now you can check via OpenShift web console that the things
are properly set up. You can browse the statuses, scale a number of pods in
each deployment up or down and do many other operations.
