FROM registry.fedoraproject.org/fedora:34

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

RUN curl -v -o /usr/share/ansible/inventory/standard-inventory-qcow2 \
    https://pagure.io/standard-test-roles/raw/master/f/inventory/standard-inventory-qcow2

COPY test /test
# for role2collection support
RUN curl -s -o /test/lsr_role2collection.py \
    https://raw.githubusercontent.com/linux-system-roles/auto-maintenance/master/lsr_role2collection.py
RUN curl -s -o /test/runtime.yml \
    https://raw.githubusercontent.com/linux-system-roles/auto-maintenance/master/lsr_role2collection/runtime.yml
ENV COLLECTION_SRC_OWNER=linux-system-roles COLLECTION_META_RUNTIME=/test/runtime.yml \
    ANSIBLE_STDOUT_CALLBACK=debug ANSIBLE_CALLBACK_WHITELIST=profile_tasks

RUN useradd -m tester
#EXTRAPRETESTER
USER tester

VOLUME /config /secrets /cache
WORKDIR /home/tester
ENV HOME=/home/tester
#EXTRAPOST
ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["/test/run-tests"]
