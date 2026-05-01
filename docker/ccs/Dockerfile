FROM ubuntu:24.04
WORKDIR /cddb

# Install Python and development tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    mariadb-client \
    gdb-multiarch \
    virtualenv \
    xz-utils \
    libmariadb-dev \
    python3-dev \
    gcc \
    vim

ARG USERNAME=ccs
ARG USER_UID=501
ARG USER_GID=501

RUN groupadd --gid $USER_GID $USERNAME \
  && useradd -s /bin/bash --uid $USER_UID --gid $USER_GID -m $USERNAME

RUN mkdir -p /space/coredumps /space/sdks

COPY docker/ccs/cs/cs.py /cddb/
COPY docker/ccs/sql/*.sql /cddb/
COPY docker/shared/bt_utils.py /cddb/

RUN chown $USERNAME -R /cddb/

USER $USERNAME

RUN cd /home/ccs && virtualenv ccs-venv

RUN /home/ccs/ccs-venv/bin/pip install mariadb pyelftools

EXPOSE 5555

ENTRYPOINT ["/home/ccs/ccs-venv/bin/python3", "/cddb/cs.py"]

