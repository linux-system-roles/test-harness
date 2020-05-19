FROM docker.io/library/fedora:32

RUN dnf update -y && dnf install -y \
    ansible \
    dumb-init \
    git \
    python3-requests \
    python3-CacheControl \
    standard-test-roles && dnf clean all

RUN useradd -m tester
USER tester

COPY test /test

VOLUME /config /secrets /cache

WORKDIR /home/tester
ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["/test/run-tests"]
