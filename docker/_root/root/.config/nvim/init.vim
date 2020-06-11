set mouse=a

if has('nvim')
  " use unnamedplus only! or else will double set
  set clipboard=unnamedplus
  if getenv('DISPLAY') == v:null
    exe setenv('DISPLAY', 'FAKE')
  endif
else
  autocmd TextYankPost * call system("c", getreg('"'))
endif

