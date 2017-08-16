FROM gliderlabs/alpine:3.6
MAINTAINER Hypothes.is Project and contributors

# Install system build and runtime dependencies.
RUN apk-install ca-certificates python py-pip libpq \
  collectd collectd-disk supervisor

# Create the lti user, group, home directory and package directory.
RUN addgroup -S lti \
  && adduser -S -G lti -h /var/lib/lti lti
WORKDIR /var/lib/lti

# Copy packaging
COPY README.markdown requirements.txt ./

# Install build deps, build, and then clean up.
RUN apk-install --virtual build-deps \
    build-base \
    postgresql-dev \
    python-dev \
  && pip install --no-cache-dir -U pip supervisor \
  && pip install --no-cache-dir -r requirements.txt \
  && apk del build-deps

# Copy collectd config
COPY conf/collectd.conf /etc/collectd/collectd.conf
RUN mkdir /etc/collectd/collectd.conf.d \
  && chown lti:lti /etc/collectd/collectd.conf.d

# collectd always tries to write to this immediately after enabling the logfile plugin.
# Even though we later configure it to write to stdout. So we do have to make sure it's
# writeable.
RUN touch /var/log/collectd.log && chown lti:lti /var/log/collectd.log

RUN apk-install collectd-disk

COPY . .

EXPOSE 8001
USER lti
CMD ["bin/init-env", "supervisord", "-c", "conf/supervisord.conf"]
