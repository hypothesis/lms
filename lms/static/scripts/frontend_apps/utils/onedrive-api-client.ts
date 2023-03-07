export async function loadOneDriveAPI(): Promise<
  NonNullable<typeof window.OneDrive>
> {
  if (window.OneDrive) {
    return window.OneDrive;
  }

  return new Promise((resolve, reject) => {
    const oneDriveScript = document.createElement('script');
    oneDriveScript.src = 'https://js.live.net/v7.2/OneDrive.js';
    oneDriveScript.onload = () => {
      resolve(window.OneDrive!);
    };
    oneDriveScript.onerror = () => {
      reject(new Error('Failed to load OneDrive API'));
    };
    document.body.appendChild(oneDriveScript);
  });
}
