FROM docker.io/library/fedora:32

USER 0

RUN dnf update -y && dnf install -y \
    ansible \
    dumb-init \
    git \
    rsync \
    python3-requests \
    python3-CacheControl \
    python3-productmd \
    python3-ruamel-yaml \
    standard-test-roles && dnf clean all

RUN useradd -m tester
#EXTRAPRETESTER
USER tester

COPY test /test

VOLUME /config /secrets /cache
WORKDIR /home/tester
ENV HOME=/home/tester
#EXTRAPOST
ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["/test/run-tests"]
