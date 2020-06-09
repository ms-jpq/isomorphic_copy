FROM ubuntu:latest


# Requirements
RUN apt update && \
    apt upgrade -y python3 git


# Install
RUN mkdir "$HOME/.config" && \
    cd "$HOME/.config" && \
    git clone https://github.com/ms-jpq/isomorphic-copy.git

ENV PATH="$HOME/.config/isomorphic-copy/bin:$PATH"

