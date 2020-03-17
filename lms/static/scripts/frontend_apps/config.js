import { createContext } from 'preact';

/**
 * Configuration object for the file picker application, read from a JSON
 * script tag injected into the page by the backend.
 */
export const Config = createContext({ api: {} });
