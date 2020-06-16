ARG PYTHON_VER="3.6.10"

FROM python:${PYTHON_VER}


# Requirements
ENTRYPOINT ["bash"]
RUN apt update && \
    apt install -y tmux vim neovim && \
    export XDG_CONFIG_HOME="$HOME/.config" && \
    mkdir -p "$XDG_CONFIG_HOME/isomorphic-copy"


# Install
COPY docker/_root/ /
COPY .    /root/.config/isomorphic-copy/
WORKDIR   /root/.config/isomorphic-copy/
ENV PATH="/root/.config/isomorphic-copy/bin:$PATH" \
    ISOCP_USE_FILE=1

