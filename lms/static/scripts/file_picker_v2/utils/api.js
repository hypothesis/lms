export class AuthorizationError extends Error {
  constructor() {
    super('Authorization failed');
  }
}

async function listFiles(authToken, courseId) {
  const result = await fetch(`/api/canvas/courses/${courseId}/files`, {
    headers: {
      Authorization: authToken,
    },
  });
  if (result.status === 403) {
    throw new AuthorizationError();
  }
  return await result.json();
}

// Separate export from declaration to work around
// https://github.com/robertknight/babel-plugin-mockable-imports/issues/9
export { listFiles };
