import React, { useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Animated,
  Modal,
  PermissionsAndroid,
  Platform,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { API_ENDPOINTS } from '../config';
import { playTTSAudio, stopTTSAudio } from '../services/audioService';
import { clearAllUserSessions, deleteUserSession, getUserSessions } from '../services/userHistoryService';

interface OnboardingScreenProps {
  onStartConversation: () => void;
  onSelectHistorySession?: (convId: string, schemes: any[], profile: any, text: string) => void;
}

const INTRO_VOICE_TEXT =
  'नमस्ते! मैं योजनावाणी सहायक हूँ। सिर्फ बोलकर सरकारी योजनाएं खोजने के लिए नीचे दिए गए माइक बटन को दबाएं।';

export const OnboardingScreen: React.FC<OnboardingScreenProps> = ({
  onStartConversation,
  onSelectHistorySession,
}) => {
  const [isPlayingIntro, setIsPlayingIntro] = useState<boolean>(false);
  const [isStarting, setIsStarting] = useState<boolean>(false);
  const [showHistoryModal, setShowHistoryModal] = useState<boolean>(false);
  const [historyList, setHistoryList] = useState<any[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState<boolean>(false);

  // Pulsing animation for the big highlighted mic button
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const glowAnim = useRef(new Animated.Value(0.4)).current;

  useEffect(() => {
    // Start continuous pulsing animation
    const pulseLoop = Animated.loop(
      Animated.sequence([
        Animated.parallel([
          Animated.timing(pulseAnim, {
            toValue: 1.08,
            duration: 1000,
            useNativeDriver: true,
          }),
          Animated.timing(glowAnim, {
            toValue: 0.85,
            duration: 1000,
            useNativeDriver: true,
          }),
        ]),
        Animated.parallel([
          Animated.timing(pulseAnim, {
            toValue: 1.0,
            duration: 1000,
            useNativeDriver: true,
          }),
          Animated.timing(glowAnim, {
            toValue: 0.4,
            duration: 1000,
            useNativeDriver: true,
          }),
        ]),
      ])
    );
    pulseLoop.start();

    // Automatically introduce itself in voice on launch
    const timer = setTimeout(() => {
      speakIntroGreeting();
    }, 400);

    return () => {
      pulseLoop.stop();
      clearTimeout(timer);
      stopTTSAudio().catch(() => {});
    };
  }, []);

  /**
   * Synthesize and play the Hindi voice introduction.
   */
  const speakIntroGreeting = async () => {
    try {
      setIsPlayingIntro(true);
      const res = await fetch(API_ENDPOINTS.tts, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: INTRO_VOICE_TEXT,
          return_format: 'base64',
          language_code: 'hi',
        }),
      });

      if (res.ok) {
        const data = await res.json();
        if (data?.audio_base64) {
          await playTTSAudio(data.audio_base64);
        }
      }
    } catch (_err) {
      // Audio fallback gracefully handled
    } finally {
      setIsPlayingIntro(false);
    }
  };

  const loadHistory = async () => {
    stopTTSAudio().catch(() => {});
    setIsLoadingHistory(true);
    setShowHistoryModal(true);
    try {
      const res = await fetch(API_ENDPOINTS.conversationHistory);
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data)) {
          // Filter out dummy or empty sessions that don't have a valid citizen profile
          const validHistory = data.filter((item: any) => {
            const p = item.citizen_profile || {};
            const name = (p.name || '').trim();
            return (
              name.length > 0 &&
              name !== 'नागरिक' &&
              name !== 'नागरिक (सत्यापित)' &&
              name !== 'Unknown'
            );
          });
          setHistoryList(validHistory);
          setIsLoadingHistory(false);
          return;
        }
      }
    } catch (_e) {
      // Fallback to in-memory store
    }
    const local = getUserSessions().filter((item: any) => {
      const p = item.citizenProfile || item.citizen_profile || {};
      const name = (p.name || '').trim();
      return (
        name.length > 0 &&
        name !== 'नागरिक' &&
        name !== 'नागरिक (सत्यापित)' &&
        name !== 'Unknown'
      );
    });
    setHistoryList(local);
    setIsLoadingHistory(false);
  };

  const handleClearAllHistory = async () => {
    try {
      await fetch(API_ENDPOINTS.conversationHistory, { method: 'DELETE' });
    } catch (_e) {}
    clearAllUserSessions();
    setHistoryList([]);
  };

  const handleDeleteSingleSession = async (convId: string) => {
    try {
      await fetch(API_ENDPOINTS.conversationState(convId), { method: 'DELETE' });
    } catch (_e) {}
    deleteUserSession(convId);
    setHistoryList((prev) => prev.filter((item: any) => (item.conversation_id || item.id) !== convId));
  };

  const handleSelectPastSession = (item: any) => {
    setShowHistoryModal(false);
    stopTTSAudio().catch(() => {});
    if (onSelectHistorySession) {
      const convId = item.conversation_id || item.id || '';
      const schemes = item.recommended_schemes || item.recommendedSchemes || [];
      const profile = item.citizen_profile || item.citizenProfile || {};
      const need = item.stated_need || item.statedNeed || profile.stated_need || 'पात्रता खोज';
      const text = `सहेजा गया रिकॉर्ड: ${profile.name || 'नागरिक'} (${need})`;
      onSelectHistorySession(convId, schemes, profile, text);
    }
  };

  /**
   * User clicks the big highlighted mic button to move ahead.
   * Silently ensures Android runtime permissions and navigates to Conversation.
   */
  const handleStart = async () => {
    if (isStarting) return;
    setIsStarting(true);
    await stopTTSAudio().catch(() => {});

    if (Platform.OS === 'android') {
      try {
        await PermissionsAndroid.request(
          PermissionsAndroid.PERMISSIONS.RECORD_AUDIO,
        );
      } catch (_e) {
        // Continue even if permission dialog was dismissed
      }
    }

    onStartConversation();
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" />

      {/* Indian National Tricolor Accent Bar */}
      <View style={styles.topAccentBar}>
        <View style={[styles.tricolorSegment, { backgroundColor: '#FF9933' }]} />
        <View style={[styles.tricolorSegment, { backgroundColor: '#FFFFFF' }]} />
        <View style={[styles.tricolorSegment, { backgroundColor: '#138808' }]} />
      </View>

      <View style={styles.content}>
        {/* Header Branding */}
        <View style={styles.header}>
          <Text style={styles.devanagariTitle}>योजनावाणी</Text>
          <Text style={styles.englishTitle}>YojanaVaani</Text>
          <Text style={styles.hindiSubtitle}>बोलिए, हम योजनाएं ढूंढेंगे</Text>
        </View>

        {/* Minimal Voice Assistant Card */}
        <View style={styles.assistantCard}>
          <View style={styles.assistantHeaderRow}>
            <Text style={styles.assistantIcon}>🤖</Text>
            <Text style={styles.assistantTitle}>योजनावाणी सहायक</Text>
          </View>
          <Text style={styles.assistantMessage}>
            नमस्ते! सिर्फ अपनी आवाज़ में बोलकर अपने हक की सरकारी योजनाएं खोजें।
          </Text>

          {/* Voice indicator / replay button */}
          <TouchableOpacity
            style={[
              styles.voiceBadge,
              isPlayingIntro && styles.voiceBadgeActive,
            ]}
            onPress={speakIntroGreeting}
            activeOpacity={0.7}
          >
            <Text style={styles.voiceBadgeIcon}>{isPlayingIntro ? '🔊' : '▶️'}</Text>
            <Text style={styles.voiceBadgeText}>
              {isPlayingIntro ? 'सहायक बोल रहा है...' : 'आवाज़ दोबारा सुनें'}
            </Text>
          </TouchableOpacity>
        </View>

        {/* Big Highlighted Mic Button Centerpiece */}
        <View style={styles.micSection}>
          <View style={styles.micAnchor}>
            <Animated.View
              style={[
                styles.outerGlowRing,
                {
                  opacity: glowAnim,
                  transform: [{ scale: pulseAnim }],
                },
              ]}
            />

            <TouchableOpacity
              style={styles.bigMicButton}
              activeOpacity={0.82}
              onPress={handleStart}
              disabled={isStarting}
            >
              <View style={styles.micInnerCircle}>
                <Text style={styles.bigMicIcon}>🎙️</Text>
              </View>
            </TouchableOpacity>
          </View>

          <TouchableOpacity
            onPress={handleStart}
            activeOpacity={0.8}
            style={styles.callToActionContainer}
          >
            <Text style={styles.callToActionTitle}>
              {isStarting ? 'शुरू हो रहा है...' : 'शुरू करने के लिए यहाँ दबाएं'}
            </Text>
            <Text style={styles.callToActionSubtitle}>
              (माइक पर टैप करें और बोलें)
            </Text>
          </TouchableOpacity>
        </View>

        {/* Subtle footer & Past Records History Button */}
        <View style={styles.footerSection}>
          <TouchableOpacity
            style={styles.historyBtn}
            activeOpacity={0.8}
            onPress={loadHistory}
            accessibilityRole="button"
            accessibilityLabel="सहेजे गए आवेदन व पिछला इतिहास देखें"
          >
            <Text style={styles.historyBtnIcon}>📋</Text>
            <Text style={styles.historyBtnText}>सहेजे गए आवेदन व पिछला इतिहास (Past Records)</Text>
          </TouchableOpacity>

          <View style={styles.footerNote}>
            <Text style={styles.footerText}>
              🔒 100% सुरक्षित — सिर्फ बोलकर बातचीत करें
            </Text>
          </View>
        </View>
      </View>

      {/* History Modal */}
      <Modal
        visible={showHistoryModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowHistoryModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <View style={{ flex: 1 }}>
                <Text style={styles.modalTitle}>📋 सहेजे गए नागरिक रिकॉर्ड</Text>
                <Text style={styles.modalSubTitle}>पुराने आवेदन, पात्रता परिणाम एवं रिपोर्ट</Text>
              </View>
              <View style={{ flexDirection: 'row', gap: 8, alignItems: 'center' }}>
                {historyList.length > 0 && (
                  <TouchableOpacity
                    style={styles.modalClearBtn}
                    onPress={handleClearAllHistory}
                  >
                    <Text style={styles.modalClearBtnText}>🗑️ हटाएं</Text>
                  </TouchableOpacity>
                )}
                <TouchableOpacity
                  style={styles.modalCloseBtn}
                  onPress={() => setShowHistoryModal(false)}
                >
                  <Text style={styles.modalCloseBtnText}>✕ बंद करें</Text>
                </TouchableOpacity>
              </View>
            </View>

            {isLoadingHistory ? (
              <View style={styles.modalLoading}>
                <ActivityIndicator size="large" color="#FF9933" />
                <Text style={styles.modalLoadingText}>रिकॉर्ड लोड हो रहे हैं...</Text>
              </View>
            ) : historyList.length === 0 ? (
              <View style={styles.emptyHistoryBox}>
                <Text style={styles.emptyHistoryIcon}>📂</Text>
                <Text style={styles.emptyHistoryTitle}>कोई पुराना रिकॉर्ड नहीं है (इतिहास खाली है)</Text>
                <Text style={styles.emptyHistorySub}>
                  सभी पुराने रिकॉर्ड हटा दिए गए हैं। नए आवेदन के लिए मुख्य स्क्रीन पर माइक दबाएं।
                </Text>
              </View>
            ) : (
              <ScrollView style={styles.historyScroll} contentContainerStyle={{ paddingBottom: 24 }}>
                {historyList.map((item, idx) => {
                  const p = item.citizen_profile || item.citizenProfile || {};
                  const citizenName = (p.name || '').trim() || 'अनाम नागरिक';
                  const loc = [p.district, p.state].filter(Boolean).join(', ') || 'स्थान अनिर्दिष्ट';
                  const need = item.stated_need || item.statedNeed || 'कल्याणकारी योजनाएं';
                  const schemesCount = item.recommended_schemes_count || (item.recommended_schemes?.length) || (item.recommendedSchemes?.length) || 0;
                  const convId = item.conversation_id || item.id;

                  return (
                    <View key={convId || idx} style={styles.historyCard}>
                      <View style={styles.historyCardTop}>
                        <Text style={styles.historyCitizenName}>👤 {citizenName}</Text>
                        <View style={styles.historyTopRightRow}>
                          <View style={styles.historyBadge}>
                            <Text style={styles.historyBadgeText}>
                              {schemesCount > 0 ? `✓ ${schemesCount} योजनाएं` : 'सत्र पूर्ण'}
                            </Text>
                          </View>
                          <TouchableOpacity
                            style={styles.deleteSingleBtn}
                            onPress={() => handleDeleteSingleSession(convId)}
                            hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
                          >
                            <Text style={styles.deleteSingleBtnText}>🗑️ हटाएं</Text>
                          </TouchableOpacity>
                        </View>
                      </View>
                      <Text style={styles.historyLoc}>📍 {loc} • {p.approx_income_bracket ? `आय: ${p.approx_income_bracket}` : 'दस्तावेज़ सत्यापित'}</Text>
                      <Text style={styles.historyNeed} numberOfLines={2}>💬 आवश्यकता: "{need}"</Text>
                      <TouchableOpacity
                        style={styles.historyViewBtn}
                        activeOpacity={0.8}
                        onPress={() => handleSelectPastSession(item)}
                      >
                        <Text style={styles.historyViewBtnText}>➔ परिणाम व रिपोर्ट देखें</Text>
                      </TouchableOpacity>
                    </View>
                  );
                })}
              </ScrollView>
            )}
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0D1B2A',
  },
  topAccentBar: {
    flexDirection: 'row',
    height: 4,
    width: '100%',
  },
  tricolorSegment: {
    flex: 1,
  },
  content: {
    flex: 1,
    paddingHorizontal: 24,
    paddingTop: 16,
    paddingBottom: 24,
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  header: {
    alignItems: 'center',
    marginTop: 8,
  },
  devanagariTitle: {
    fontSize: 44,
    fontWeight: '900',
    color: '#FF9933',
    letterSpacing: 1.5,
  },
  englishTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#94A3B8',
    letterSpacing: 2,
    marginTop: 2,
  },
  hindiSubtitle: {
    fontSize: 21,
    color: '#FFFFFF',
    marginTop: 8,
    textAlign: 'center',
    fontWeight: '600',
  },
  assistantCard: {
    width: '100%',
    backgroundColor: '#1B263B',
    borderRadius: 20,
    paddingVertical: 18,
    paddingHorizontal: 20,
    borderWidth: 1.5,
    borderColor: '#384E6E',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
    alignItems: 'center',
  },
  assistantHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  assistantIcon: {
    fontSize: 26,
    marginRight: 8,
  },
  assistantTitle: {
    fontSize: 20,
    fontWeight: '800',
    color: '#FFD166',
  },
  assistantMessage: {
    fontSize: 17,
    color: '#E0E1DD',
    textAlign: 'center',
    lineHeight: 25,
    fontWeight: '500',
    marginBottom: 12,
  },
  voiceBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#0F172A',
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#415A77',
  },
  voiceBadgeActive: {
    borderColor: '#FF9933',
    backgroundColor: '#2A1B0A',
  },
  voiceBadgeIcon: {
    fontSize: 16,
    marginRight: 6,
  },
  voiceBadgeText: {
    fontSize: 14,
    color: '#FFD166',
    fontWeight: '700',
  },
  micSection: {
    alignItems: 'center',
    justifyContent: 'center',
    marginVertical: 12,
  },
  micAnchor: {
    width: 156,
    height: 156,
    justifyContent: 'center',
    alignItems: 'center',
    position: 'relative',
  },
  outerGlowRing: {
    position: 'absolute',
    width: 156,
    height: 156,
    borderRadius: 78,
    borderWidth: 3,
    borderColor: '#FF9933',
    backgroundColor: '#FF993318',
  },
  bigMicButton: {
    width: 136,
    height: 136,
    borderRadius: 68,
    backgroundColor: '#FF9933',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#FF9933',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.5,
    shadowRadius: 14,
    elevation: 10,
    borderWidth: 4,
    borderColor: '#FFE0B2',
  },
  micInnerCircle: {
    width: 110,
    height: 110,
    borderRadius: 55,
    backgroundColor: '#E67E00',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#FFD166',
  },
  bigMicIcon: {
    fontSize: 66,
  },
  callToActionContainer: {
    marginTop: 20,
    alignItems: 'center',
  },
  callToActionTitle: {
    fontSize: 22,
    fontWeight: '900',
    color: '#FFD166',
    textAlign: 'center',
    letterSpacing: 0.5,
  },
  callToActionSubtitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#94A3B8',
    marginTop: 4,
  },
  footerSection: {
    width: '100%',
    alignItems: 'center',
    gap: 10,
  },
  historyBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#1E293B',
    paddingVertical: 12,
    paddingHorizontal: 18,
    borderRadius: 14,
    borderWidth: 1.5,
    borderColor: '#3B82F6',
    width: '100%',
  },
  historyBtnIcon: {
    fontSize: 18,
    marginRight: 8,
  },
  historyBtnText: {
    color: '#93C5FD',
    fontSize: 15,
    fontWeight: '700',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.75)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#0F172A',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    maxHeight: '85%',
    padding: 20,
    borderWidth: 1,
    borderColor: '#334155',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#1E293B',
    paddingBottom: 14,
    marginBottom: 14,
  },
  modalTitle: {
    fontSize: 19,
    fontWeight: '800',
    color: '#F8FAFC',
  },
  modalSubTitle: {
    fontSize: 13,
    color: '#94A3B8',
    marginTop: 2,
  },
  modalClearBtn: {
    backgroundColor: '#991B1B',
    paddingVertical: 6,
    paddingHorizontal: 10,
    borderRadius: 8,
  },
  modalClearBtnText: {
    color: '#FEE2E2',
    fontSize: 12,
    fontWeight: '700',
  },
  modalCloseBtn: {
    backgroundColor: '#334155',
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 8,
  },
  modalCloseBtnText: {
    color: '#F1F5F9',
    fontSize: 13,
    fontWeight: '700',
  },
  modalLoading: {
    padding: 40,
    alignItems: 'center',
  },
  modalLoadingText: {
    color: '#94A3B8',
    fontSize: 14,
    marginTop: 12,
  },
  emptyHistoryBox: {
    padding: 40,
    alignItems: 'center',
  },
  emptyHistoryIcon: {
    fontSize: 42,
    marginBottom: 12,
  },
  emptyHistoryTitle: {
    color: '#F8FAFC',
    fontSize: 17,
    fontWeight: '700',
    textAlign: 'center',
  },
  emptyHistorySub: {
    color: '#64748B',
    fontSize: 13,
    textAlign: 'center',
    marginTop: 6,
    lineHeight: 18,
  },
  historyScroll: {
    maxHeight: 480,
  },
  historyCard: {
    backgroundColor: '#1E293B',
    borderRadius: 14,
    padding: 14,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#334155',
  },
  historyCardTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  historyCitizenName: {
    color: '#F8FAFC',
    fontSize: 16,
    fontWeight: '800',
  },
  historyBadge: {
    backgroundColor: '#1E3A8A',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  historyTopRightRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  deleteSingleBtn: {
    backgroundColor: '#374151',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#4B5563',
  },
  deleteSingleBtnText: {
    color: '#F87171',
    fontSize: 12,
    fontWeight: '700',
  },
  historyBadgeText: {
    color: '#93C5FD',
    fontSize: 12,
    fontWeight: '700',
  },
  historyLoc: {
    color: '#94A3B8',
    fontSize: 13,
    marginTop: 4,
  },
  historyNeed: {
    color: '#CBD5E1',
    fontSize: 13,
    marginTop: 6,
    fontStyle: 'italic',
  },
  historyViewBtn: {
    backgroundColor: '#2563EB',
    borderRadius: 8,
    paddingVertical: 8,
    alignItems: 'center',
    marginTop: 10,
  },
  historyViewBtnText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '700',
  },
  footerNote: {
    paddingVertical: 10,
    paddingHorizontal: 16,
    backgroundColor: '#1E293B88',
    borderRadius: 12,
  },
  footerText: {
    fontSize: 14,
    color: '#94A3B8',
    fontWeight: '600',
    textAlign: 'center',
  },
});
