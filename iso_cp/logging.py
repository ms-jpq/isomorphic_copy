from logging import INFO, StreamHandler, getLogger

log = getLogger()
log.addHandler(StreamHandler())
log.setLevel(INFO)

