# Isomorphic Copy

## What it does

A cross platform clipboard.

Works the same locally as over SSH, inside Docker containers, inside LXD containers etc.

Pretends it's `pbcopy`, `xclip`, `wl-copy`, etc.

Works out of the box with programs that use those commands.

## How to use

Clone this repo to the same location on two machines. Either relative to `~` or `/`.

Add `isomorphic-copy/bin` to your `PATH` for example:

`export PATH="$XDG_CONFIG_HOME/isomorphic-copy/bin:$PATH"`

in my `rc` file.

You are done!

Use `c` to copy

`echo <my message> | c`

Use `p` to paste

`p > my_message.txt`


## Integrations

## How to install

