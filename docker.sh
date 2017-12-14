docker run \
  -p 3000:3000 \
  -e VIA_URL="https://via.hypothes.is" \
  -e JWT_SECRET="dev_secret" \
  --link lti-postgres:postgres \
  -e DATABASE_URL="postgresql://postgres@postgres/postgres" \
  -e GOOGLE_CLIENT_ID="242096057153-ps1j2p46s6ae4n20l160mi5vut2s57c6.apps.googleusercontent.com" \
  -e GOOGLE_DEVELOPER_KEY="AIzaSyBoctvKMTHcFI8KLpKUYqkBbKH5pXApK84" \
  -e GOOGLE_APP_ID="hypothesis-185914" \
  hypothesis/lms:dev