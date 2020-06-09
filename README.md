# Isomorphic Copy

A cross platform clipboard.

Works the same locally as over SSH, inside Docker containers, inside LXD containers etc.

Pretends it's `pbcopy`, `xclip`, `wl-copy`, etc.

Works out of the box with programs that use those commands.

## How to use

Clone this repo to the same location on two machines. Either relative to `~` or `/`.

Add `isomorphic-copy/bin` to your `PATH` for example:

`export PATH="$XDG_CONFIG_HOME/isomorphic-copy/bin:$PATH"` in my `rc` file.

---

`echo <my message> | c` :: Use `c` to copy


`p > my_message.txt` :: Use `p` to paste

---

Launch remote daemon with

`cssh <ssh-args>`

`cdocker <docker container name>`

`clxd <lxd container name>`

Once daemon is launched, remote `c` will propagate to local system clipboard.

Remote applications that use `xclip`, `pbcopy`, `wl-copy` will propagate to local system clipboard.

## Integrations

## How to install

