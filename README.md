# [Isomorphic Copy](https://ms-jpq.github.io/isomorphic-copy)

**Cross platform clipboard.**

Works the same locally as over SSH, inside Docker containers, et al.

It even works inside Docker over SSH and then inside Docker!, **infinitely chainable**.

It will **pretend** it's `pbcopy`, `xclip`, `wl-copy`, etc. and forward calls to appropriate destinations.

Works out of the 📦 with most programs that use those commands.

![clippy](https://raw.githubusercontent.com/ms-jpq/isomorphic-copy/master/preview/clippy.jpg)

---

## How to use

Requires `xclip` or `wl-clipboard` under GUI linux.

**Clone** this repo to the same location on two machines. Either relative to `~` or `/`.

**Prepend** `isomorphic-copy/bin` to your `PATH` for example:

`export PATH="$XDG_CONFIG_HOME/isomorphic-copy/bin:$PATH"` in your `bash/zshrc` file.

You need to do this on both local and remote.

--

**Automatically** most applications that use `xclip`, `wl-clipboard`, `pbcopy` and so forth will use `isomorphic-copy` with zero setup.

Works just like python `virtualenv`!

--

I added two **convenience functions**:

You don't have to use these. Things like `pbcopy` and `pbpaste` will continue to work.

`echo <my message> | c` Use `c` to copy to system clipboard


`p > my_message.txt` Use `p` to paste from system clipboard

--

Launch **remote daemon** with one of

`cssh <ssh-args>`

`cdocker <docker container name>`

Once daemon is launched, remote copy will propagate to local system clipboard.

Remote applications that use `xclip`, `pbcopy`, `wl-copy` will propagate to local system clipboard.

--

**Local -> SSH -> Docker**

If you have to copy inside a `Docker` container on a remote machine via `SSH`

from local run `cssh <ssh-args>` to remote

from remote run `cdocker <container name / sha>` to container

And you are set!


## Integrations

### Tmux

Copy will automatically propagate to local / remote tmux clipboard.

If daemon is run under tmux, copy will also propagate to the local tmux clipboard.

If no system clipboard is available, copy / paste will use tmux clipboard.

Copying *FROM* tmux will require this snippet.

```conf
set -g mouse on

bind -T copy-mode MouseDragEnd1Pane \
  send-keys -X stop-selection

bind -T copy-mode MouseDown1Pane \
  select-pane \;\
  send-keys -X copy-pipe "c" \;\
  send-keys -X clear-selection
```

Drag to select, click in dragged area to copy.

Replace `copy-mode` with `copy-mode-vi` if you are using vi emulation.

### Vim

Neovim will only use `xclip` if the x11 environmental variable `DISPLAY` is set.

Vim will require an autocmd event.

Add this snippet to your `vimrc`, to work for both vims.

```viml
if has('nvim')
  " use unnamedplus only! or else will double set
  set clipboard=unnamedplus
  if getenv('DISPLAY') == v:null
    exe setenv('DISPLAY', 'FAKE')
  endif
else
  autocmd TextYankPost * call system("c", getreg('"'))
endif
```

### Others

Most CLI applications will work out of the box. (such as lazygit, for example).

If not, check if they require `DISPLAY` like Neovim.

### Fallback

If no system / tmux clipboard is found, setting environmental variable `ISOCP_USE_FILE=1` will enable using a temp file as a crude clipboard.

It will write inside the git repo, put it somewhere safe.

## How does it work?

### PATH

`isomorphic-copy` inserts itself in the `PATH` before actual system clipboards. It will forward calls to system / tmux / remote clipboards.

### Remote detection

`isomorphic-copy` will use `SSH_TTY` env var and `/.dockerenv` file to detect remote sessions. If running under remote session, it will communicate with remote daemon via an UNIX socket.

### Twin Daemons

To communicate with remote, `isomorphic-copy` will launch a local daemon, which will then launch itself as a remote daemon.

The two daemons communicate via stdout. It's so stupidly simple that it will work absolutely everywhere.

Remote copy look something like this.

```
<third party app> | fake xclip | isomorphic-copy > unix-socket ->

unix-socket -> remote-daemon > /dev/stdout | local-daemon | <actual clipboard>
```

### Chaining

Basically the same workflow above, repeated n times until finally you reach local clipboard.

