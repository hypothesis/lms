# Stage 1: Build frontend assets.
FROM node:24.1.0-alpine as frontend-build

ENV NODE_ENV production
COPY .babelrc rollup.config.js tailwind.config.js gulpfile.js package.json .yarnrc.yml yarn.lock /tmp/frontend-build/
COPY .yarn /tmp/frontend-build/.yarn
COPY lms/static /tmp/frontend-build/lms/static

WORKDIR /tmp/frontend-build
RUN yarn install --immutable
RUN yarn build

# Stage 2: Build the rest of the app using build output from Stage 1.
FROM python:3.11.11-alpine3.19
LABEL authors="Hypothes.is Project and contributors"

# Install system build and runtime dependencies.
RUN apk add libpq supervisor git

# Create the lms user, group, home directory and package directory.
RUN addgroup -S lms \
  && adduser -S -G lms -h /var/lib/lms lms
WORKDIR /var/lib/lms

# Copy minimal data to allow installation of dependencies.
COPY requirements/prod.txt ./

# Install build deps, build, and then clean up.
RUN apk add --virtual build-deps \
    build-base \
    postgresql-dev \
    python3-dev \
    libffi-dev \
  && pip3 install --no-cache-dir -U pip \
  && pip3 install --no-cache-dir -r prod.txt \
  && apk del build-deps

# Copy frontend assets.
COPY --from=frontend-build /tmp/frontend-build/build build

# Copy the rest of the application files.
COPY . .

ENV PYTHONPATH /var/lib/lms:$PYTHONPATH

EXPOSE 8001
USER lms
CMD ["bin/init-env", "supervisord", "-c", "conf/supervisord.conf"]
