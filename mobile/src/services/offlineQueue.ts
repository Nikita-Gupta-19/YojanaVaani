/**
 * Offline Queue and Connectivity Service for YojanaVaani (Phase 7).
 *
 * Ensures that if the network request to /conversation/{id}/respond fails
 * mid-conversation, the citizen's voice/text response is not lost.
 * Queued responses are held locally in persistent memory and automatically
 * flushed when connectivity is restored.
 */

export interface QueuedResponse {
  id: string;
  conversationId: string;
  text?: string;
  audioBase64?: string;
  timestamp: number;
  status: 'queued' | 'sending' | 'failed';
}

// In-memory persistent queue storage (works seamlessly across React Native runtime and Jest tests)
let queueStore: QueuedResponse[] = [];
let connectivityListeners: ((isOnline: boolean) => void)[] = [];
let isDeviceOnline: boolean = true;

/**
 * Enqueues a response that failed to send due to network disruption.
 */
export function enqueueResponse(
  conversationId: string,
  text?: string,
  audioBase64?: string
): QueuedResponse {
  const item: QueuedResponse = {
    id: `queue_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
    conversationId,
    text,
    audioBase64,
    timestamp: Date.now(),
    status: 'queued',
  };
  queueStore.push(item);
  return item;
}

/**
 * Returns all currently queued items awaiting transmission.
 */
export function getQueuedResponses(): QueuedResponse[] {
  return [...queueStore];
}

/**
 * Returns the count of queued items.
 */
export function getQueuedCount(): number {
  return queueStore.length;
}

/**
 * Removes an item from the queue once successfully transmitted.
 */
export function removeQueuedResponse(id: string): void {
  queueStore = queueStore.filter((item) => item.id !== id);
}

/**
 * Clears the entire queue (useful for testing and reset).
 */
export function clearQueue(): void {
  queueStore = [];
}

/**
 * Sets connectivity status and notifies active UI listeners.
 */
export function setConnectivityStatus(online: boolean): void {
  const changed = isDeviceOnline !== online;
  isDeviceOnline = online;
  if (changed) {
    connectivityListeners.forEach((listener) => listener(online));
  }
}

/**
 * Gets current connectivity status.
 */
export function getConnectivityStatus(): boolean {
  return isDeviceOnline;
}

/**
 * Subscribes a listener to connectivity transitions.
 */
export function subscribeConnectivity(listener: (isOnline: boolean) => void): () => void {
  connectivityListeners.push(listener);
  return () => {
    connectivityListeners = connectivityListeners.filter((l) => l !== listener);
  };
}

/**
 * Attempts to flush all queued responses against the backend API.
 * Calls senderFn(item) for each pending item.
 */
export async function flushOfflineQueue(
  senderFn: (item: QueuedResponse) => Promise<boolean>
): Promise<{ successful: number; remaining: number }> {
  let successful = 0;
  const items = [...queueStore];

  for (const item of items) {
    try {
      item.status = 'sending';
      const ok = await senderFn(item);
      if (ok) {
        removeQueuedResponse(item.id);
        successful++;
      } else {
        item.status = 'failed';
      }
    } catch (_error) {
      item.status = 'failed';
    }
  }

  return {
    successful,
    remaining: queueStore.length,
  };
}
