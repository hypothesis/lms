import type { ToastMessage } from '@hypothesis/frontend-shared';
import { useCallback, useState } from 'preact/hooks';

export type ToastMessageData = Omit<ToastMessage, 'id'>;

export type ToastMessages = {
  toastMessages: ToastMessage[];
  dismissToastMessage: (id: string) => void;
};

// Keep a global incremental counter to use as unique toast message ID
let toastMessageCounter = 0;

function dataToToastMessage(toastMessageData: ToastMessageData): ToastMessage {
  toastMessageCounter++;
  const id = `${toastMessageCounter}`;
  return { ...toastMessageData, id };
}

export function useToastMessages(
  initialToastMessages: ToastMessageData[]
): ToastMessages {
  const [toastMessages, setToastMessages] = useState<ToastMessage[]>(
    initialToastMessages.map(dataToToastMessage)
  );
  const dismissToastMessage = useCallback(
    (id: string) =>
      setToastMessages(messages =>
        messages.filter(message => message.id !== id)
      ),
    []
  );

  return { toastMessages, dismissToastMessage };
}
