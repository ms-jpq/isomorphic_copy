set clipboard=unnamedplus

if getenv('DISPLAY') == v:null
  exe setenv('DISPLAY', 'FAKE')
endif

