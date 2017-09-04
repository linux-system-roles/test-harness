FROM fedora:25

RUN dnf install -y \
  ansible \
  genisoimage \
  openssh-clients \
  python2-avocado \
  python2-avocado-plugins-varianter-yaml-to-mux \
  qemu-system-x86

RUN useradd -m tester
USER tester

VOLUME /cache /role

COPY . /system-api-test
COPY avocado.conf /etc/avocado

# NOTE can be removed once avocado handles its cache configuration correctly
RUN mkdir -p /home/tester/avocado/data/cache

WORKDIR /system-api-test
CMD avocado run test.py -m image:images.yml --show-job-log
