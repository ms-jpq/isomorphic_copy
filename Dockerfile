FROM alpine:latest


# Requirements
RUN apk add --no-cache python3 && \
    mkdir "$HOME/.config" && \
    mkdir "$HOME/.config/isomorphic-copy"


# Install
COPY .    /root/.config/isomorphic-copy/
WORKDIR   /root/.config/isomorphic-copy/
ENV PATH="/root/.config/isomorphic-copy/bin:$PATH" \
    ISOCP_USE_FILE=1

