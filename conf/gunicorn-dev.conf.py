from glob import glob

bind = "0.0.0.0:8001"
reload = True
reload_extra_files = glob("lms/templates/**/*", recursive=True)
timeout = 0
