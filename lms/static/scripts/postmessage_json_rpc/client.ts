import { generateHexString } from './random';

/**
 * Return a Promise that rejects with an error after `delay` ms.
 */
function createTimeout(delay: number, message: string) {
  return new Promise((_, reject) => {
    setTimeout(() => reject(new Error(message)), delay);
  });
}

/**
 * Make a JSON-RPC call to a server in another frame using `postMessage`.
 *
 * @param frame - Frame to send call to
 * @param origin - Origin filter for `window.postMessage` call
 * @param method - Name of the JSON-RPC method
 * @param params - Parameters of the JSON-RPC method
 * @param [timeout] - Maximum time to wait in ms
 * @param [window_] - Test seam.
 * @param [id] - Test seam.
 * @return - A Promise for the response to the call
 */
export async function call(
  frame: Window,
  origin: string,
  method: string,
  params: unknown[] = [],
  timeout = 2000,
  window_ = window,
  id = generateHexString(10),
): Promise<unknown> {
  // Send RPC request.
  const request = {
    jsonrpc: '2.0',
    method,
    params,
    id,
  };
  frame.postMessage(request, origin);

  // Await response or timeout.
  let listener;
  const response = new Promise<unknown>((resolve, reject) => {
    listener = (event: MessageEvent) => {
      if (event.origin !== origin) {
        // Not from the frame that we sent the request to.
        return;
      }

      if (
        !(event.data instanceof Object) ||
        event.data.jsonrpc !== '2.0' ||
        event.data.id !== id
      ) {
        // Not a valid JSON-RPC response.
        return;
      }

      const { error, result } = event.data;
      if (error !== undefined) {
        reject(error);
      } else if (result !== undefined) {
        resolve(result);
      } else {
        reject(new Error('RPC reply had no result or error'));
      }
    };
    window_.addEventListener('message', listener);
  });

  const timeoutExpired = createTimeout(
    timeout,
    `Request to ${origin} timed out`,
  );

  // Cleanup and return.
  try {
    return await Promise.race([response, timeoutExpired]);
  } finally {
    // @ts-ignore - TS can't infer that listener will be initialized here.
    window_.removeEventListener('message', listener);
  }
}

/**
 * Send a JSON-RPC 2.0 notification request to another frame via `postMessage`.
 * No response is expected.
 *
 * @param frame - Frame to send call to
 * @param origin - Origin filter for `window.postMessage` call
 * @param method - Name of the JSON-RPC method
 * @param params - Parameters of the JSON-RPC method
 */
export function notify(
  frame: Window,
  origin: string,
  method: string,
  params: unknown[],
) {
  const request = {
    jsonrpc: '2.0',
    method,
    params,
  };
  frame.postMessage(request, origin);
}
