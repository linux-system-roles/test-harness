FROM fedora:28

RUN dnf update -y && dnf install -y \
    ansible \
    git \
    python3-requests \
    python3-CacheControl \
    standard-test-roles && dnf clean all

RUN useradd -m tester
USER tester

COPY test /test

VOLUME /config /secrets /cache

WORKDIR /home/tester
ENTRYPOINT ["/test/run-tests"]
