export {};

declare global {
  interface Window {
    OneDrive: {
      open: (options: Record<string, any>) => void;
    };
  }
}
