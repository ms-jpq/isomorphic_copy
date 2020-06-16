ARG PYTHON_VER="3.6.10"

FROM python:${PYTHON_VER}


# Requirements
ENTRYPOINT ["bash"]
RUN apt update && \
    apt install -y tmux vim neovim && \
    export XDG_CONFIG_HOME="$HOME/.config" && \
    export XDG_DATA_HOME="$HOME/.local/share" && \
    mkdir -p "$XDG_CONFIG_HOME/isomorphic-copy" && \
    mkdir -p "$XDG_DATA_HOME/isomorphic-copy"


# Install
COPY docker/_root/ /
COPY .    /root/.isomorphic-copy/
COPY .    /root/.local/share/isomorphic-copy/
COPY .    /root/.config/isomorphic-copy/
WORKDIR   /root/.config/isomorphic-copy/
ENV PATH="/root/.config/isomorphic-copy/bin:$PATH" \
    ISOCP_USE_FILE=1

