# Stage 1: Build frontend assets.
FROM node:14.7.0-alpine as frontend-build

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
RUN apk add libpq supervisor

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

# Copy frontend assets.
COPY --from=frontend-build /build build

# Copy the rest of the application files.
COPY . .

ENV PYTHONPATH /var/lib/lms:$PYTHONPATH

EXPOSE 8001
USER lms
CMD ["bin/init-env", "supervisord", "-c", "conf/supervisord.conf"]
