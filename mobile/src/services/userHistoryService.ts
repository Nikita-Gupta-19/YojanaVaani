/**
 * User Data History Service for YojanaVaani.
 *
 * Saves, retrieves, and manages citizen assessment history, including:
 * - Demographics and socioeconomic profiles
 * - Question-and-answer session transcripts
 * - Recommended welfare schemes and verdicts
 * - Verified identity/income/ration/land documents
 */

export interface UserSessionHistory {
  id: string;
  timestamp: number;
  dateFormatted: string;
  citizenProfile: Record<string, any>;
  recommendedSchemes: Array<{
    id: number;
    name: string;
    category?: string;
    government_name?: string;
    verdict?: string;
    benefits?: any;
    [key: string]: any;
  }>;
  verifiedDocuments?: Array<{
    document_type: string;
    extracted_fields: Record<string, any>;
    verification_status: string;
    confirmed_at: string;
  }>;
  statedNeed?: string;
  transcriptSummary?: string;
}

// In-memory persistent history storage across mobile app lifecycle
let historyStore: UserSessionHistory[] = [];

/**
 * Saves or updates a citizen session history record.
 */
export function saveUserSession(session: Partial<UserSessionHistory> & { id: string }): UserSessionHistory {
  const existingIdx = historyStore.findIndex((s) => s.id === session.id);
  const now = Date.now();
  const dateFormatted = new Date(now).toLocaleDateString('hi-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });

  const fullRecord: UserSessionHistory = {
    id: session.id,
    timestamp: session.timestamp || now,
    dateFormatted: session.dateFormatted || dateFormatted,
    citizenProfile: session.citizenProfile || {},
    recommendedSchemes: session.recommendedSchemes || [],
    verifiedDocuments: session.verifiedDocuments || [],
    statedNeed: session.statedNeed || session.citizenProfile?.stated_need || '',
    transcriptSummary: session.transcriptSummary || '',
  };

  if (existingIdx >= 0) {
    historyStore[existingIdx] = {
      ...historyStore[existingIdx],
      ...fullRecord,
      timestamp: now,
      dateFormatted,
    };
  } else {
    historyStore.unshift(fullRecord);
  }

  return fullRecord;
}

/**
 * Retrieves all saved citizen session history records, newest first.
 */
export function getUserSessions(): UserSessionHistory[] {
  return [...historyStore];
}

/**
 * Retrieves a single citizen session by its unique conversation ID.
 */
export function getUserSessionById(id: string): UserSessionHistory | undefined {
  return historyStore.find((s) => s.id === id);
}

/**
 * Deletes a specific session from history.
 */
export function deleteUserSession(id: string): void {
  historyStore = historyStore.filter((s) => s.id !== id);
}

/**
 * Clears the entire user history store.
 */
export function clearAllUserSessions(): void {
  historyStore = [];
}
