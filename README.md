# Isomorphic Copy

Cross platform clipboard.

Works the same locally as over SSH, inside Docker containers, inside LXD containers etc.

Pretends it's `pbcopy`, `xclip`, `wl-copy`, etc.

Works out of the box with programs that use those commands.

## How to use

Clone this repo to the same location on two machines. Either relative to `~` or `/`.

Add `isomorphic-copy/bin` to your `PATH` for example:

`export PATH="$XDG_CONFIG_HOME/isomorphic-copy/bin:$PATH"` in your `bash/zshrc` file.

---

`echo <my message> | c` :: Use `c` to copy to system clipboard


`p > my_message.txt` :: Use `p` to paste from system clipboard

---

Launch remote daemon with

`cssh <ssh-args>`

`cdocker <docker container name>`

`clxd <lxd container name>`

Once daemon is launched, remote copy will propagate to local system clipboard.

Remote applications that use `xclip`, `pbcopy`, `wl-copy` will propagate to local system clipboard.

## Integrations

### Tmux

Copy will automatically propagate to local / remote tmux clipboard.

If daemon is run under tmux, copy will also propagate to the local tmux clipboard.

If no system clipboard is available, copy / paste will use tmux clipboard.

### Vim

Vim will only use `xclip` if the x11 environmental variable `DISPLAY` is set.

Add this snippet to your `vimrc`, and Vim will automatically use the fake `xclip`.

```viml
if getenv('DISPLAY') == v:null
  exe setenv('DISPLAY', 'FAKE')
endif
```

### Others

Most applications will work out of the box. (such as lazygit, for example).

If not, check if they require some environmental variables like Vim.

### Fallback

If no system / tmux clipboard is found, setting environmental variable `ISOCP_USE_FILE=1` can use the filesystem as the clipboard.

It write to the git repo.

