FROM msjpq/kde-vnc:focal


# Requirements
RUN apt update && \
    apt install -y python3 xclip && \
    apt clean && \
    export XDG_CONFIG_HOME="$HOME/.config" && \
    export XDG_DATA_HOME="$HOME/.local/share" && \
    mkdir -p "$XDG_CONFIG_HOME/isomorphic-copy" && \
    mkdir -p "$XDG_DATA_HOME/isomorphic-copy"


# Install
COPY .    /config/.isomorphic-copy/
COPY .    /config/.local/share/isomorphic-copy/
COPY .    /config/.config/isomorphic-copy/
WORKDIR   /config/.config/isomorphic-copy/
ENV PATH="/config/.config/isomorphic-copy/bin:$PATH" \
    ISOCP_USE_FILE=1

