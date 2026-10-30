import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Animated,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  StatusBar,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { API_ENDPOINTS } from '../config';
import {
  enqueueResponse,
  flushOfflineQueue,
  getQueuedCount,
  subscribeConnectivity,
} from '../services/offlineQueue';
import {
  isAudioRecorderAvailable,
  playTTSAudio,
  startAudioRecording,
  stopAudioRecording,
  stopTTSAudio,
} from '../services/audioService';

export interface ChatMessage {
  id: string;
  speaker: 'assistant' | 'citizen';
  text: string;
  timestamp: number;
}

interface ConversationScreenProps {
  onNavigateToDocument: (conversationId: string, documentType: string) => void;
  onNavigateToResults: (conversationId: string, schemes: any[], spokenText: string) => void;
  onNavigateToEscalation: (conversationId: string, cscInfo: any, spokenText: string) => void;
  onBackToOnboarding: () => void;
}

export const ConversationScreen: React.FC<ConversationScreenProps> = ({
  onNavigateToDocument,
  onNavigateToResults,
  onNavigateToEscalation,
  onBackToOnboarding,
}) => {
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [assistantState, setAssistantState] = useState<'speaking' | 'listening' | 'thinking'>('speaking');
  const [currentPrompt, setCurrentPrompt] = useState<string>('बातचीत शुरू की जा रही है...');
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [textInputFallback, setTextInputFallback] = useState<string>('');
  const [showTextInput, setShowTextInput] = useState<boolean>(true);
  const [isOffline, setIsOffline] = useState<boolean>(false);
  const [queuedItemsCount, setQueuedItemsCount] = useState<number>(0);
  const [currentField, setCurrentField] = useState<string>('name');
  const [questionProgress, setQuestionProgress] = useState<{ current: number; total: number }>({
    current: 1,
    total: 9,
  });

  // Pulse animation for the listening/speaking microphone orb
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const haloAnim = useRef(new Animated.Value(0.3)).current;

  // Handle connectivity updates
  useEffect(() => {
    const unsubscribe = subscribeConnectivity((online) => {
      setIsOffline(!online);
      if (online && conversationId) {
        // Automatically attempt to flush queued voice responses
        flushOfflineQueue(async (item) => {
          try {
            const res = await fetch(API_ENDPOINTS.conversationRespond(item.conversationId), {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ text: item.text }),
            });
            return res.ok;
          } catch (_e) {
            return false;
          }
        }).then(({ remaining }) => setQueuedItemsCount(remaining));
      }
    });
    return unsubscribe;
  }, [conversationId]);

  // Mic Pulse animation loop
  useEffect(() => {
    const animation = Animated.loop(
      Animated.parallel([
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: assistantState === 'listening' ? 1.18 : 1.06,
            duration: 1200,
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1.0,
            duration: 1200,
            useNativeDriver: true,
          }),
        ]),
        Animated.sequence([
          Animated.timing(haloAnim, {
            toValue: 0.6,
            duration: 1200,
            useNativeDriver: true,
          }),
          Animated.timing(haloAnim, {
            toValue: 0.2,
            duration: 1200,
            useNativeDriver: true,
          }),
        ]),
      ])
    );
    animation.start();
    return () => animation.stop();
  }, [assistantState, pulseAnim, haloAnim]);

  /**
   * Dispatches an action received from the backend conversation API.
   */
  const handleAction = useCallback(
    (action: any, convId: string) => {
      if (!action) return;

      const actionType = action.type;
      const actionText = action.text || '';

      if (actionType === 'ask_question') {
        setCurrentPrompt(actionText);
        setCurrentField(action.field_name || '');
        setAssistantState('speaking');

        // Append assistant's question to visual transcript
        setMessages((prev) => [
          ...prev,
          {
            id: `msg_${Date.now()}`,
            speaker: 'assistant',
            text: actionText,
            timestamp: Date.now(),
          },
        ]);

        // Play assistant spoken voice if available
        if (action.audio_base64) {
          playTTSAudio(action.audio_base64).catch(() => {});
        }

        // Switch to listening
        setTimeout(() => {
          setAssistantState('listening');
        }, 1200);
      } else if (actionType === 'request_document') {
        setAssistantState('thinking');
        onNavigateToDocument(convId, action.document_type || 'income_certificate');
      } else if (actionType === 'present_results') {
        setAssistantState('speaking');
        onNavigateToResults(convId, action.schemes || [], actionText);
      } else if (actionType === 'escalate') {
        setAssistantState('speaking');
        onNavigateToEscalation(convId, action.csc_info || {}, actionText);
      }
    },
    [onNavigateToDocument, onNavigateToResults, onNavigateToEscalation]
  );

  const hasInitializedRef = useRef<boolean>(false);

  /**
   * Initializes the session on screen mount via POST /conversation/start.
   */
  const initSession = useCallback(async () => {
    setAssistantState('thinking');
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 8000);

    try {
      const response = await fetch(API_ENDPOINTS.conversationStart, {
        method: 'POST',
        headers: { Accept: 'application/json' },
        signal: controller.signal,
      });
      clearTimeout(timer);

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}`);
      }

      const data = await response.json();
      setConversationId(data.conversation_id);
      setQuestionProgress({
        current: data.question_index + 1,
        total: data.total_questions || 9,
      });

      handleAction(data.action, data.conversation_id);
      setIsOffline(false);
    } catch (_err) {
      clearTimeout(timer);
      setIsOffline(true);
      setAssistantState('listening');
      setCurrentPrompt('नमस्ते! आपका नाम क्या है?');
    }
  }, [handleAction]);

  useEffect(() => {
    if (hasInitializedRef.current) return;
    hasInitializedRef.current = true;
    initSession();
  }, [initSession]);

  /**
   * Submits a spoken or text response to POST /conversation/{id}/respond.
   */
  const submitCitizenResponse = async (responseText: string) => {
    if (!responseText.trim() || !conversationId) return;

    // Record citizen answer to visual transcript
    setMessages((prev) => [
      ...prev,
      {
        id: `msg_${Date.now()}`,
        speaker: 'citizen',
        text: responseText.trim(),
        timestamp: Date.now(),
      },
    ]);

    setTextInputFallback('');
    setAssistantState('thinking');

    try {
      const response = await fetch(API_ENDPOINTS.conversationRespond(conversationId), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        body: JSON.stringify({ text: responseText.trim() }),
      });

      if (!response.ok) {
        if (response.status === 400) {
          setAssistantState('listening');
          setCurrentPrompt('आवाज़ सुनाई नहीं दी। कृपया बोलें या नीचे लिखकर भेजें।');
          setShowTextInput(true);
          Alert.alert(
            'आवाज़ नहीं सुनाई दी (No Audio Detected)',
            'एमुलेटर के माइक्रोफ़ोन से आवाज़ नहीं आई। कृपया नीचे दिए गए इनपुट बॉक्स में टाइप करें या कीबोर्ड माइक का उपयोग करें।'
          );
          return;
        }
        throw new Error(`HTTP error ${response.status}`);
      }

      const turnData = await response.json();
      setIsOffline(false);

      if (turnData.citizen_profile) {
        // Increment question progress
        setQuestionProgress((prev) => ({
          ...prev,
          current: Math.min(prev.current + 1, prev.total),
        }));
      }

      handleAction(turnData.action, conversationId);
    } catch (_err) {
      // Offline fallback: Queue the response locally
      enqueueResponse(conversationId, responseText.trim());
      setQueuedItemsCount(getQueuedCount());
      setIsOffline(true);
      setAssistantState('listening');
      setCurrentPrompt('आपका उत्तर स्थानीय रूप से सहेज लिया गया है। नेटवर्क आते ही भेजा जाएगा।');
    }
  };

  /**
   * Submits recorded base64 WAV audio to POST /conversation/{id}/respond.
   * Server transcribes it via Whisper STT and records the citizen's actual spoken answer.
   */
  const submitCitizenAudioResponse = async (audioBase64: string) => {
    if (!audioBase64 || !conversationId) return;

    setAssistantState('thinking');
    setCurrentPrompt('आपकी आवाज़ पहचानी जा रही है (Transcribing with Whisper)...');

    try {
      const response = await fetch(API_ENDPOINTS.conversationRespond(conversationId), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        body: JSON.stringify({ audio_base64: audioBase64 }),
      });

      if (!response.ok) {
        if (response.status === 400) {
          setAssistantState('listening');
          setCurrentPrompt('आवाज़ सुनाई नहीं दी। कृपया बोलें या नीचे लिखकर भेजें।');
          setShowTextInput(true);
          Alert.alert(
            'आवाज़ नहीं सुनाई दी (No Audio Detected)',
            'एमुलेटर के माइक्रोफ़ोन से आवाज़ नहीं आई। कृपया नीचे दिए गए इनपुट बॉक्स में टाइप करें या कीबोर्ड माइक का उपयोग करें।'
          );
          return;
        }
        throw new Error(`HTTP error ${response.status}`);
      }

      const turnData = await response.json();
      setIsOffline(false);

      const transcribed = turnData.transcribed_text || 'आवाज़ प्राप्त हुई';

      // Record citizen answer to visual transcript
      setMessages((prev) => [
        ...prev,
        {
          id: `msg_${Date.now()}`,
          speaker: 'citizen',
          text: transcribed,
          timestamp: Date.now(),
        },
      ]);

      if (turnData.citizen_profile) {
        setQuestionProgress((prev) => ({
          ...prev,
          current: Math.min(prev.current + 1, prev.total),
        }));
      }

      handleAction(turnData.action, conversationId);
    } catch (_err) {
      setIsOffline(true);
      setAssistantState('listening');
      Alert.alert(
        'त्रुटि (Error)',
        'सर्वर से संपर्क नहीं हो पाया या ऑडियो ट्रांसक्राइब नहीं हुआ। कृपया दोबारा बोलें या नीचे लिखकर भेजें।'
      );
      setCurrentPrompt('ऑडियो भेजने में समस्या हुई। कृपया दोबारा प्रयास करें।');
    }
  };

  /**
   * Voice Mic recording press: starts/stops real native audio recording.
   * Never injects mock or predefined answers.
   */
  const handleMicPress = async () => {
    if (isRecording) {
      // User tapped to finish speaking
      setIsRecording(false);
      setAssistantState('thinking');
      setCurrentPrompt('ऑडियो प्रोसेस किया जा रहा है...');

      try {
        const base64Audio = await stopAudioRecording();
        if (base64Audio && base64Audio.length > 50) {
          await submitCitizenAudioResponse(base64Audio);
        } else {
          setAssistantState('listening');
          setCurrentPrompt('कोई आवाज़ रिकॉर्ड नहीं हुई। कृपया दोबारा बोलें।');
        }
      } catch (_err) {
        setAssistantState('listening');
        setCurrentPrompt('रिकॉर्डिंग पूरी नहीं हो सकी। कृपया दोबारा प्रयास करें।');
      }
    } else {
      // Check if native audio recorder module is ready
      const available = await isAudioRecorderAvailable();
      if (!available) {
        Alert.alert(
          'आवाज़ इनपुट (Voice Input)',
          'माइक्रोफ़ोन मॉड्यूल लोड नहीं हुआ है। कृपया नीचे दिए गए इनपुट बॉक्स में कीबोर्ड माइक (Gboard 🎙️) से बोलें या लिखकर उत्तर दें।',
          [{ text: 'समझ गया (OK)' }]
        );
        setShowTextInput(true);
        return;
      }

      try {
        await startAudioRecording();
        setIsRecording(true);
        setAssistantState('listening');
        setCurrentPrompt('हम सुन रहे हैं... बोलने के बाद लाल बटन दोबारा दबाएं।');
      } catch (_err) {
        Alert.alert('त्रुटि', 'माइक्रोफ़ोन शुरू करने में समस्या हुई। कृपया ऐप की ऑडियो अनुमति (Permission) जांचें।');
      }
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" />

      {/* Top Header */}
      <View style={styles.topBar}>
        <TouchableOpacity onPress={onBackToOnboarding} style={styles.backButton}>
          <Text style={styles.backButtonText}>← वापस</Text>
        </TouchableOpacity>
        <View style={styles.topTitleContainer}>
          <Text style={styles.topTitle}>योजनावाणी सहायक</Text>
          <Text style={styles.progressText}>
            प्रश्न {questionProgress.current} / {questionProgress.total}
          </Text>
        </View>
        <TouchableOpacity
          onPress={() => setShowTextInput(!showTextInput)}
          style={styles.keyboardToggle}
        >
          <Text style={styles.keyboardToggleText}>{showTextInput ? '🎙️' : '⌨️'}</Text>
        </TouchableOpacity>
      </View>

      {/* Offline Alert Banner */}
      {isOffline && (
        <View style={styles.offlineBanner}>
          <Text style={styles.offlineText}>
            ⚠️ इंटरनेट कनेक्शन नहीं है — {queuedItemsCount > 0 ? `${queuedItemsCount} उत्तर कतारबद्ध (Queued)` : 'ऑफ़लाइन मोड'}
          </Text>
        </View>
      )}

      {/* Assistant Status Banner */}
      <View style={styles.statusIndicatorRow}>
        <View
          style={[
            styles.statusDot,
            assistantState === 'speaking' && styles.statusDotSpeaking,
            assistantState === 'listening' && styles.statusDotListening,
            assistantState === 'thinking' && styles.statusDotThinking,
          ]}
        />
        <Text style={styles.statusLabel}>
          {assistantState === 'speaking' && '🔊 योजनावाणी बोल रही है, कृपया सुनें...'}
          {assistantState === 'listening' && (isRecording ? '🎙️ माइक चालू है, बोलिए...' : '🎙️ बोलने के लिए नीचे बड़ा माइक दबाएं')}
          {assistantState === 'thinking' && '⏳ जानकारी जाँची जा रही है, थोड़ा रुकें...'}
        </Text>
      </View>

      {/* Primary Voice Prompt Banner */}
      <View style={styles.promptCard}>
        <Text style={styles.promptDevanagari}>{currentPrompt}</Text>
      </View>

      {/* Visual Chat Transcript (Secondary Channel) */}
      <FlatList
        data={messages}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.transcriptList}
        renderItem={({ item }) => (
          <View
            style={[
              styles.chatBubble,
              item.speaker === 'assistant' ? styles.bubbleAssistant : styles.bubbleCitizen,
            ]}
          >
            <Text style={styles.speakerLabel}>
              {item.speaker === 'assistant' ? '🤖 योजनावाणी सहायक' : '👤 आप'}
            </Text>
            <Text style={styles.bubbleText}>{item.text}</Text>
          </View>
        )}
      />

      {/* Optional Text Input Fallback */}
      {showTextInput && (
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : undefined}
          style={styles.textInputContainer}
        >
          <TextInput
            style={styles.textInput}
            placeholder="यहाँ बोलें (Gboard माइक 🎙️) या लिखें..."
            placeholderTextColor="#64748B"
            value={textInputFallback}
            onChangeText={setTextInputFallback}
            onSubmitEditing={() => submitCitizenResponse(textInputFallback)}
          />
          <TouchableOpacity
            style={styles.textSendButton}
            onPress={() => submitCitizenResponse(textInputFallback)}
          >
            <Text style={styles.textSendButtonText}>भेजें</Text>
          </TouchableOpacity>
        </KeyboardAvoidingView>
      )}

      {/* Main Center Voice Recording Button */}
      <View style={styles.micControlArea}>
        <Animated.View
          style={[
            styles.micHalo,
            {
              transform: [{ scale: pulseAnim }],
              opacity: haloAnim,
              backgroundColor: isRecording ? '#EF4444' : '#FF9933',
            },
          ]}
        />
        <TouchableOpacity
          style={[styles.micButton, isRecording && styles.micButtonActive]}
          activeOpacity={0.8}
          onPress={handleMicPress}
        >
          {assistantState === 'thinking' ? (
            <ActivityIndicator size="large" color="#FFFFFF" />
          ) : (
            <Text style={styles.micIconText}>{isRecording ? '⏹' : '🎙️'}</Text>
          )}
        </TouchableOpacity>
        <Text style={styles.micInstruction}>
          {isRecording ? '⏹ बोलना खत्म होने पर यहाँ दबाएं' : '🎙️ बोलने के लिए यहाँ दबाएं'}
        </Text>
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0D1B2A',
  },
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#1E293B',
  },
  backButton: {
    padding: 10,
  },
  backButtonText: {
    color: '#FF9933',
    fontSize: 16,
    fontWeight: '700',
  },
  topTitleContainer: {
    alignItems: 'center',
  },
  topTitle: {
    color: '#F8FAFC',
    fontSize: 20,
    fontWeight: '800',
  },
  progressText: {
    color: '#FFD166',
    fontSize: 14,
    fontWeight: '700',
    marginTop: 2,
  },
  keyboardToggle: {
    padding: 10,
  },
  keyboardToggleText: {
    fontSize: 24,
  },
  offlineBanner: {
    backgroundColor: '#7F1D1D',
    paddingVertical: 8,
    paddingHorizontal: 16,
    alignItems: 'center',
  },
  offlineText: {
    color: '#FECACA',
    fontSize: 14,
    fontWeight: '700',
  },
  statusIndicatorRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 10,
    backgroundColor: '#1B263B',
  },
  statusDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 10,
  },
  statusDotSpeaking: {
    backgroundColor: '#10B981',
  },
  statusDotListening: {
    backgroundColor: '#FF9933',
  },
  statusDotThinking: {
    backgroundColor: '#3B82F6',
  },
  statusLabel: {
    color: '#F1F5F9',
    fontSize: 16,
    fontWeight: '700',
  },
  promptCard: {
    backgroundColor: '#1E293B',
    marginHorizontal: 16,
    marginTop: 12,
    marginBottom: 10,
    borderRadius: 16,
    padding: 18,
    borderLeftWidth: 6,
    borderLeftColor: '#FF9933',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.3,
    shadowRadius: 6,
    elevation: 4,
  },
  promptDevanagari: {
    color: '#FFFFFF',
    fontSize: 24,
    lineHeight: 34,
    fontWeight: '700',
  },
  transcriptList: {
    paddingHorizontal: 16,
    paddingVertical: 10,
  },
  chatBubble: {
    maxWidth: '86%',
    padding: 14,
    borderRadius: 16,
    marginBottom: 12,
  },
  bubbleAssistant: {
    alignSelf: 'flex-start',
    backgroundColor: '#1B263B',
    borderTopLeftRadius: 4,
  },
  bubbleCitizen: {
    alignSelf: 'flex-end',
    backgroundColor: '#0F766E',
    borderTopRightRadius: 4,
  },
  speakerLabel: {
    fontSize: 14,
    fontWeight: '700',
    color: '#94A3B8',
    marginBottom: 4,
  },
  bubbleText: {
    color: '#F8FAFC',
    fontSize: 20,
    lineHeight: 28,
    fontWeight: '500',
  },
  textInputContainer: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingVertical: 10,
    backgroundColor: '#1E293B',
  },
  textInput: {
    flex: 1,
    backgroundColor: '#0F172A',
    color: '#FFFFFF',
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 18,
  },
  textSendButton: {
    backgroundColor: '#FF9933',
    paddingHorizontal: 20,
    justifyContent: 'center',
    borderRadius: 12,
    marginLeft: 10,
  },
  textSendButtonText: {
    color: '#0D1B2A',
    fontWeight: '800',
    fontSize: 18,
  },
  micControlArea: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 20,
    backgroundColor: '#0D1B2A',
    borderTopWidth: 1,
    borderTopColor: '#1E293B',
  },
  micHalo: {
    position: 'absolute',
    width: 120,
    height: 120,
    borderRadius: 60,
  },
  micButton: {
    width: 90,
    height: 90,
    borderRadius: 45,
    backgroundColor: '#FF9933',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#FF9933',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.5,
    shadowRadius: 12,
    elevation: 8,
  },
  micButtonActive: {
    backgroundColor: '#EF4444',
  },
  micIconText: {
    fontSize: 42,
    color: '#FFFFFF',
  },
  micInstruction: {
    color: '#F8FAFC',
    fontSize: 17,
    marginTop: 12,
    fontWeight: '700',
    textAlign: 'center',
  },
});
