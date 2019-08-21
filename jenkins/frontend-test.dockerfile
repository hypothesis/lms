# nb. We use Alpine as a base image and then install Node + Yarn separately
# rather than using a Node base image because this enables automated tools to
# upgrade everything by simply updating the Alpine version.
#
# Alpine is updated every 6 months so all packages are pretty recent.
FROM alpine:3.10

RUN apk update && apk add --no-cache \
  chromium \
  git \
  make \
  nodejs \
  npm \
  yarn

# Enable test scripts to detect that they are running from the Docker image.
ENV RUNNING_IN_DOCKER true
