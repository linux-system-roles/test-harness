
Integration Tests for Linux System Roles
========================================

A docker container which runs the tests from one of the [linux system
roles](https://github.com/linux-system-roles) against various operating
systems.

It starts a virtual machine based on a cloud image of each operating system
(defined in [images.yml](/images.yml)) and runs playbooks in the roles `test`
directory against that machine.

To build the container, run

    docker build --tag cockpit/linux-system-roles-test .

To run tests of a role inside the container, execute this inside the top level
directory of the test:

    docker run --privileged \
               --rm \
               --volume $PWD:/role \
               --volume $CACHEDIR:/cache \
               cockpit/linux-system-roles-test

`$CACHEDIR` is the directory in which the test downloads virtual machine
images. To save some typing, each role contains a script `run-tests.sh`.

To log into the container, run

    docker run -ti --rm --privileged -v $PWD:/role -v $CACHEDIR:/cache \
               cockpit/linux-system-roles-test /bin/bash

You can then run the tests manually with

    avocado run test.py -m image:images.yml --show-job-log

To only run tests against a single image, use avocado's parameter filtering
mechanism:

    avocado run test.py -m image:images.yml --show-job-log \
                --filter-only /run/image/centos-7
