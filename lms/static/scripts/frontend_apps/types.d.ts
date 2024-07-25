import 'navigation-api-types';

export {};

declare global {
  interface Window {
    /** Global property set once OneDrive JS client is loaded. */
    OneDrive?: {
      open: (options: Record<string, any>) => void;
    };
  }
}
