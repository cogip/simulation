FROM ubuntu:24.04 as cogip-console

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && \
    apt-get install -y \
        libgl1 \
        libglib2.0-0 \
        python3 \
        python3-pip \
        python3-venv \
        git \
        cmake \
        swig \
        socat \
        wait-for-it

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN python -m pip install -U pip setuptools wheel

ADD requirements.txt requirements-dev.txt pyproject.toml /src/
RUN python -m pip install -r /src/requirements.txt -r /src/requirements-dev.txt

ADD cogip /src/cogip
RUN python -m pip install -e /src[dev]

CMD ["sleep", "infinity"]


FROM cogip-console as cogip-gui

RUN apt-get install -y \
        libegl1 \
        libxkbcommon0 \
        libdbus-1-3 \
        libnss3 \
        libxcb-cursor0 \
        libxcomposite1 \
        libxdamage1 \
        libxrender1 \
        libxrandr2 \
        libxtst6 \
        libxi6 \
        libxkbfile1 \
        libxcb-xkb1 libxcb-image0 libxcb-render-util0 libxcb-render0 libxcb-util1 \
        libxcb-icccm4 libxcb-keysyms1 libxcb-shape0 libxkbcommon-x11-0

FROM ubuntu:24.04 as cogip-firmware

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && \
        apt-get install -y \
        g++ \
        g++-multilib \
        gcc-arm-none-eabi \
        gcc-multilib \
        gdb-multiarch \
        git \
        libstdc++-arm-none-eabi-newlib \
        make \
        ncat netcat-openbsd \
        protobuf-compiler \
        python3 \
        python3-pip \
        python3-venv \
        quilt \
        socat \
        unzip \
        wait-for-it

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN python -m pip install -U pip setuptools wheel

ADD requirements.txt /tmp/
RUN python -m pip install -r /tmp/requirements.txt

CMD ["sleep", "infinity"]
