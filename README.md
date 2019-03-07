Integration Tests for Linux System Roles
========================================
[![Build Status](https://travis-ci.org/linux-system-roles/test-harness.svg?branch=master)](https://travis-ci.org/linux-system-roles/test-harness)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

Commands
--------

The CI system can be controlled with a few commands as comments in pull requests:

* `[citest]` - Trigger a re-test for all machines
* `[citest bad]` - Trigger a re-test for all machines with an error or failure status
* `[citest pending]` - Trigger a re-test for all machines with a pending status
* `[citest commit:<sha1>]` - Whitelist a commit to be tested if the submitter is not trusted

It is also possible to whitelist all commits in a PR with the `needs-ci` tag.
However, this should be only used with trusted submitters since they can still
change the commits in the PR.


Installation
------------

A docker container which runs integration tests for open pull requests on
[linux system roles](https://linux-system-roles.github.io) repositories. It runs
all playbooks `test/test_*.yml` of the repository against various virtual
machines.

To build the container, run

    sudo docker build -t linuxsystemroles/test-harness:latest .

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

The `setup` key contains either a list of Ansible plays which will be saved as a playbook and executed before the test run, or a single shell command which will be executed using the Ansible `raw` module (so the two examples above are exactly equivalent).

The container needs a `/secrets` mount, which must contain these files:

* `github-token`: A GitHub access token with `public_repo`, `repo:status` and
  `read:org` scopes. The `read:org` permission is required to identify users as
  members to organiziations in case they set their organization membership to
  private. Without it, the test harness can still update CI status but might
  ignore pull requests or command comments unexpectedly.
* `is_rsa` and `id_rsa.pub`: A ssh key with to access the server in
  `results.destination`.
* `known_hosts`: A ssh `known_hosts` file which contains the public key of that
  server.

The test runner writes images into the `/cache` mount and reuses existing ones.

The container must have access to `/dev/kvm` for fast virtualization.


## Running on OpenShift

To run the integration tests in an OpenShift instance, create a new project and
add the `ServiceAccount`, `ImageStream`, and `DeploymentConfig` from
`openshift-objects.yml`:

    oc new-project linux-system-roles-test
    oc create -f openshift-objects.yml

The service account needs to be in the privileged scc. If you have appropriate
permissions, you can edit it with

    oc edit scc privileged

and add `- system:serviceaccount:linux-system-roles:tester` under `users`.

If you need to run container as root (for example for accessing `/dev/kvm`),
apply following file:

    oc replace -f openshift-objects-root.yml

Also, create a `config.json` and a directory containing the secrets mentioned
above, and add `ConfigMap` and `Secret` objects with:

    oc create configmap config --from-file=config.json
    oc create secret generic secrets --from-file=path/to/secrets

Finally, import the image to trigger a deployment:

    oc import-image linux-system-roles-test
