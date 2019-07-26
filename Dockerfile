# Stage 1: Build frontend assets.
FROM node:12.7-alpine as frontend-build

ENV NODE_ENV production
COPY .babelrc gulpfile.js package.json yarn.lock ./
COPY scripts/gulp ./scripts/gulp
COPY lms/static ./lms/static
RUN yarn install --frozen-lockfile

RUN yarn build

# Stage 2: Build the rest of the app using build output from Stage 1.
FROM python:3.6.9-alpine3.10
MAINTAINER Hypothes.is Project and contributors

# Install system build and runtime dependencies.
RUN apk add libpq collectd collectd-disk supervisor

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

# Copy frontend assets.
COPY --from=frontend-build /build build

# Copy the rest of the application files.
COPY . .

EXPOSE 8001
USER lms
CMD ["bin/init-env", "supervisord", "-c", "conf/supervisord.conf"]
