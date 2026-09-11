import { Platform } from 'react-native';

/**
 * Backend service configuration for YojanaVaani.
 * Uses 10.0.2.2 for Android emulator loopback and localhost for iOS / desktop.
 */
export const BACKEND_BASE_URL = Platform.select({
  android: 'http://10.0.2.2:8000',
  ios: 'http://localhost:8000',
  default: 'http://10.0.2.2:8000',
});

export const API_ENDPOINTS = {
  health: `${BACKEND_BASE_URL}/health`,
  conversationStart: `${BACKEND_BASE_URL}/conversation/start`,
  conversationRespond: (id: string) => `${BACKEND_BASE_URL}/conversation/${id}/respond`,
  conversationDocument: (id: string) => `${BACKEND_BASE_URL}/conversation/${id}/document`,
  conversationConfirm: (id: string) => `${BACKEND_BASE_URL}/conversation/${id}/confirm_document`,
  conversationState: (id: string) => `${BACKEND_BASE_URL}/conversation/${id}`,
  tts: `${BACKEND_BASE_URL}/tts`,
  stt: `${BACKEND_BASE_URL}/stt`,
};

/**
 * Checks backend health endpoint with a configurable timeout.
 * Returns true if server responds with HTTP 200 and status 'ok', false otherwise.
 */
export async function checkBackendHealth(timeoutMs: number = 4000): Promise<boolean> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(API_ENDPOINTS.health, {
      method: 'GET',
      headers: {
        Accept: 'application/json',
      },
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    if (!response.ok) {
      return false;
    }
    const data = await response.json();
    return Boolean(data && data.status === 'ok');
  } catch (_error) {
    clearTimeout(timeoutId);
    return false;
  }
}
