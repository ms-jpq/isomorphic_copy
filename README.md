# [Isomorphic Copy](https://ms-jpq.github.io/isomorphic-copy)

**Cross platform clipboard.**

Works the same locally as over SSH, inside Docker containers, et al.

It even works inside Docker over SSH and then inside Docker!, **infinitely chainable**.

Pretends it's `pbcopy`, `xclip`, `wl-copy`, etc. and forward calls to appropriate destinations.

Works out of the box with programs that use those commands.

![clippy](https://raw.githubusercontent.com/ms-jpq/isomorphic-copy/master/preview/clippy.jpg)

---

## How to use

Requires `xclip` or `wl-clipboard` under GUI linux.

**Clone** this repo to the same location on two machines. Either relative to `~` or `/`.

**Prepend** `isomorphic-copy/bin` to your `PATH` for example:

`export PATH="$XDG_CONFIG_HOME/isomorphic-copy/bin:$PATH"` in your `bash/zshrc` file.

--

**Automatically** most applications that use `xclip`, `clipboard`, `pbcopy` and so forth will use isomorphic copy.

Works just like python `virtualenv`!

--

I added two **convenience functions**:

You don't have to use these. Things like `pbcopy` and `pbpaste` will continue to work.

`echo <my message> | c` :: Use `c` to copy to system clipboard


`p > my_message.txt` :: Use `p` to paste from system clipboard

--

Launch **remote daemon** with one of

`cssh <ssh-args>`

`cdocker <docker container name>`

Once daemon is launched, remote copy will propagate to local system clipboard.

Remote applications that use `xclip`, `pbcopy`, `wl-copy` will propagate to local system clipboard.

## Integrations

### Tmux

Copy will automatically propagate to local / remote tmux clipboard.

If daemon is run under tmux, copy will also propagate to the local tmux clipboard.

If no system clipboard is available, copy / paste will use tmux clipboard.

Copying *FROM* tmux will require this snippet.

```conf
bind -T copy-mode MouseDown1Pane \
  select-pane \;\
  send-keys -X copy-pipe "c" \;\
  send-keys -X clear-selection
```

Replace `copy-mode` with `copy-mode-vi` if you are using vi emulation.

### Vim

Vim will only use `xclip` if the x11 environmental variable `DISPLAY` is set.

Add this snippet to your `vimrc`, and Vim will automatically use the fake `xclip`.

```viml
if getenv('DISPLAY') == v:null
  exe setenv('DISPLAY', 'FAKE')
endif
```

### Others

Most CLI applications will work out of the box. (such as lazygit, for example).

If not, check if they require `DISPLAY` like Vim.

### Fallback

If no system / tmux clipboard is found, setting environmental variable `ISOCP_USE_FILE=1` will enable using a temp file as a crude clipboard.

It will write inside the git repo, put it somewhere safe.

## How does it work?

`isomorphic-copy` will use the system & tmux clipboard if run locally. It will try to detect being ran remotely, by either `SSH_TTY` env var, or `.dockerenv` file, etc.

If ran as a daemon, it will find a copy of itself on the remote machine on the same relative location, start itself on the remote, and listen on an unix socket created inside the git repo.

Remote copies then try to write to the unix socket, which will propagate via the two daemons back to your local machine.

This works pretty much everywhere, because we are only using `stdin` and `stdout`.
