FROM fedora:26

RUN dnf install -y \
    ansible \
    git \
    python3-requests \
    standard-test-roles

RUN useradd -m tester
USER tester

COPY test /test

# Copied from standard-test-roles with larskarlitski's patches:
# - don't hang when not connected to a tty
# - use the raw module instead of ping to contact a host
COPY standard-inventory-qcow2 /usr/share/ansible/inventory/

VOLUME /config /secrets /cache

WORKDIR /home/tester
ENTRYPOINT ["/test/run-tests"]
