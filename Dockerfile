FROM ubuntu:latest


# Requirements
RUN apt update && \
    apt upgrade -y python3 && \
    mkdir "$HOME/.config" && \
    mkdir "$HOME/.config/isomorphic-copy"


# Install
COPY . "$HOME/.config/isomorphic-copy/"
ENV PATH="/root/.config/isomorphic-copy/bin:$PATH"

