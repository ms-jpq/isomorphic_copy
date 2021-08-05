from logging import INFO, StreamHandler, getLogger

log = getLogger(__name__)
log.addHandler(StreamHandler())
log.setLevel(INFO)
