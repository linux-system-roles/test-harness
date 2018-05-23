FROM fedora:26

RUN dnf install -y \
    ansible \
    git \
    python3-requests \
    standard-test-roles

RUN useradd -m tester
USER tester

COPY test /test

VOLUME /config /secrets /cache

WORKDIR /home/tester
ENTRYPOINT ["/test/run-tests"]
