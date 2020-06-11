set mouse=a

if has('nvim')
  set clipboard=unnamedplus,unnamed
  if getenv('DISPLAY') == v:null
    exe setenv('DISPLAY', 'FAKE')
  endif
else
  autocmd TextYankPost * call system("c", getreg('"'))
endif

