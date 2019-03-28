FROM alpine:3.9.2
MAINTAINER Hypothes.is Project and contributors

# Install system build and runtime dependencies.
RUN apk add ca-certificates python3 libpq collectd collectd-disk supervisor nodejs nodejs-npm

# Create the lms user, group, home directory and package directory.
RUN addgroup -S lms \
  && adduser -S -G lms -h /var/lib/lms lms
WORKDIR /var/lib/lms

# Copy minimal data to allow installation of dependencies.
COPY requirements.txt ./

# Install build deps, build, and then clean up.
RUN apk add --virtual build-deps \
    build-base \
    postgresql-dev \
    python3-dev \
  && pip3 install --no-cache-dir -U pip \
  && pip3 install --no-cache-dir -r requirements.txt \
  && apk del build-deps

# Copy collectd config
COPY conf/collectd.conf /etc/collectd/collectd.conf
RUN mkdir /etc/collectd/collectd.conf.d \
  && chown lms:lms /etc/collectd/collectd.conf.d

# collectd always tries to write to this immediately after enabling the logfile plugin.
# Even though we later configure it to write to stdout. So we do have to make sure it's
# writeable.
RUN touch /var/log/collectd.log && chown lms:lms /var/log/collectd.log

COPY . .

# Build frontend assets
RUN npm install --production
RUN NODE_ENV=production node_modules/.bin/gulp build
RUN npm cache clean --force

EXPOSE 8001
USER lms
CMD ["bin/init-env", "supervisord", "-c", "conf/supervisord.conf"]
