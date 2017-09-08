Integration Tests for Linux System Roles
========================================

A docker container which runs integration tests for open pull requests on
[linux system roles](https://linux-system-roles.github.io) repositories. It runs
all playbooks `test/test_*.yml` of the repository against various virtual
machines.

To build the container, run

    docker build --tag linux-system-roles-test .

Multiple of these containers can be started in parallel. They try to not step
on each others feet by synchronizing via GitHub commit statuses.

The test runner needs a `config.json` in the `/config` mount, which specifies
the repositories to monitor for open pull requests, the cloud images to use,
a location where to copy (via ssh) the test results to, and a publicly
accessible URL for these results. For example:

```json
  "repositories": [
    "linux-system-roles/network"
  ],
  "images": [
    {
      "name": "fedora-26",
      "source": "https://download.fedoraproject.org/pub/fedora/linux/releases/26/CloudImages/x86_64/images/Fedora-Cloud-Base-26-1.5.x86_64.qcow2",
      "setup": "sudo dnf install -yq python2 python2-dnf libselinux-python"
    },
    {
      "name": "centos-7",
      "source": "https://cloud.centos.org/centos/7/images/CentOS-7-x86_64-GenericCloud-1702.qcow2"
    }
  ],
  "results": {
    "destination": "user@example.org:public_html/logs",
    "public_url": "https://example.com/logs"
  }
}
```

The container needs a `/secrets` mount, which must contain these files:

* `github-token`: A GitHub access token with `public_repo` and `repo:status`
  rights.
* `is_rsa` and `id_rsa.pub`: A ssh key with to access the server in
  `results.destination`.
* `known_hosts`: A ssh `known_hosts` file which contains the public key of that
  server.

The test runner writes images into the `/cache` mount and reuses existing ones.

The container should have access to `/dev/kvm/` for fast virtualization.


## Running on OpenShift

To run the integration tests in an OpenShift instance, create a new project and
add the `ServiceAccount`, `ImageStream`, and `DeploymentConfig` from
`openshift-objects.yml`:

    oc new-project linux-system-roles-test
    oc create -f openshift-objects.yml

The service account needs to be in the privileged scc. Edit it with

    oc edit scc privileged

and add `- system:serviceaccount:linux-system-roles:tester` under `users`.

Also, create a `config.json` and a directory containing the secrets mentioned
above, and add `ConfigMap` and `Secrect` objects with:

    oc create configmap config --from-file=config.json
    oc create secret generic secrets --from-file=path/to/secrets

Finally, import the image to trigger a deployment:

    oc import-image linux-system-roles-test
