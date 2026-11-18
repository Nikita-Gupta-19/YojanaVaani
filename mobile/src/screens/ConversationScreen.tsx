import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Animated,
  FlatList,
  Keyboard,
  KeyboardAvoidingView,
  PermissionsAndroid,
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
import { SCHEME_GENERATION_LOADING_AUDIO_BASE64 } from '../services/schemeLoadingAudio';
import { saveUserSession } from '../services/userHistoryService';
import {
  enqueueResponse,
  flushOfflineQueue,
  getQueuedCount,
  subscribeConnectivity,
} from '../services/offlineQueue';
import {
  cancelVoiceRecognition,
  isAudioRecorderAvailable,
  playTTSAudio,
  startAudioRecording,
  startVoiceRecognition,
  stopAudioRecording,
  stopTTSAudio,
  stopVoiceRecognition,
  subscribeSpeechPartialResults,
  subscribeSpeechResults,
  subscribeSpeechError,
} from '../services/audioService';

export interface ChatMessage {
  id: string;
  speaker: 'assistant' | 'citizen';
  text: string;
  timestamp: number;
}

interface ConversationScreenProps {
  isActive?: boolean;
  onNavigateToDocument: (conversationId: string, documentType: string) => void;
  onNavigateToResults: (
    conversationId: string,
    schemes: any[],
    spokenText: string,
    audioBase64?: string,
    citizenProfile?: any
  ) => void;
  onNavigateToEscalation: (conversationId: string, cscInfo: any, spokenText: string) => void;
  onBackToOnboarding: () => void;
}

export const ConversationScreen: React.FC<ConversationScreenProps> = ({
  isActive = true,
  onNavigateToDocument,
  onNavigateToResults,
  onNavigateToEscalation,
  onBackToOnboarding,
}) => {
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [assistantState, setAssistantState] = useState<'speaking' | 'listening' | 'thinking'>('listening');
  const [currentPrompt, setCurrentPrompt] = useState<string>('नमस्ते! आपका नाम क्या है?');
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
  const [quickOptions, setQuickOptions] = useState<string[]>([]);
  const [tempSpokenText, setTempSpokenText] = useState<string>('');
  const [pendingConfirmation, setPendingConfirmation] = useState<string | null>(null);
  const [isGeneratingSchemes, setIsGeneratingSchemes] = useState<boolean>(false);
  const [isScrolledAwayFromBottom, setIsScrolledAwayFromBottom] = useState<boolean>(false);
  const [isKeyboardVisible, setIsKeyboardVisible] = useState<boolean>(false);
  const [keyboardHeight, setKeyboardHeight] = useState<number>(0);

  // When ConversationScreen loses focus or isActive is false, immediately silence TTS and cancel speech recognition
  useEffect(() => {
    if (!isActive) {
      stopTTSAudio().catch(() => {});
      cancelVoiceRecognition().catch(() => {});
    }
  }, [isActive]);

  // Monitor keyboard visibility so typing doesn't get obscured by mic area
  useEffect(() => {
    const showSub = Keyboard.addListener(
      Platform.OS === 'ios' ? 'keyboardWillShow' : 'keyboardDidShow',
      (e) => {
        setIsKeyboardVisible(true);
        if (e && e.endCoordinates && e.endCoordinates.height) {
          setKeyboardHeight(e.endCoordinates.height);
        }
        setTimeout(() => {
          flatListRef.current?.scrollToEnd({ animated: true });
        }, 100);
      }
    );
    const hideSub = Keyboard.addListener(
      Platform.OS === 'ios' ? 'keyboardWillHide' : 'keyboardDidHide',
      () => {
        setIsKeyboardVisible(false);
        setKeyboardHeight(0);
      }
    );

    return () => {
      showSub.remove();
      hideSub.remove();
    };
  }, []);

  const flatListRef = useRef<FlatList>(null);
  const tempSpokenTextRef = useRef<string>('');
  const isRecordingRef = useRef<boolean>(false);
  const recordingTimerRef = useRef<any>(null);

  // Subscribe to real-time live speech recognition events (temp text streaming)
  useEffect(() => {
    const subPartial = subscribeSpeechPartialResults((partial) => {
      if (partial && partial.trim().length > 0) {
        tempSpokenTextRef.current = partial.trim();
        setTempSpokenText(partial.trim());
        setTextInputFallback(partial.trim());
      }
    });

    const subResults = subscribeSpeechResults((finalText) => {
      if (finalText && finalText.trim().length > 0) {
        tempSpokenTextRef.current = finalText.trim();
        setTempSpokenText(finalText.trim());
        setTextInputFallback(finalText.trim());
        setPendingConfirmation(finalText.trim());
        setIsRecording(false);
        isRecordingRef.current = false;
        setAssistantState('listening');
        setCurrentPrompt(`पहचाना गया (Whisper ASR): "${finalText.trim()}"`);
      }
    });

    const subError = subscribeSpeechError((_code) => {
      console.log('[ConversationScreen] Speech recognition error event code:', _code);
      setIsRecording(false);
      isRecordingRef.current = false;
      const cached = tempSpokenTextRef.current.trim();
      if (cached.length > 0) {
        setPendingConfirmation(cached);
        setAssistantState('listening');
        setCurrentPrompt(`पहचाना गया (Whisper ASR): "${cached}"`);
      } else {
        setAssistantState('listening');
      }
    });

    return () => {
      subPartial.remove();
      subResults.remove();
      subError.remove();
    };
  }, []);

  // Pulse animation for the listening/speaking microphone orb
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const haloAnim = useRef(new Animated.Value(0.3)).current;

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

  // Spoken voice guidance during Scheme Generation loading screen
  useEffect(() => {
    let isCancelled = false;
    let playTimer: any = null;

    if (isGeneratingSchemes) {
      console.log('[ConversationScreen] isGeneratingSchemes active, starting immediate voice playback...');
      playTimer = setTimeout(async () => {
        if (!isCancelled) {
          try {
            await playTTSAudio(SCHEME_GENERATION_LOADING_AUDIO_BASE64);
            console.log('[ConversationScreen] Scheme generation audio playing immediately out loud!');
          } catch (err) {
            console.warn('[ConversationScreen] Scheme generation audio playback error:', err);
          }
        }
      }, 80);

      return () => {
        isCancelled = true;
        if (playTimer) clearTimeout(playTimer);
      };
    }
  }, [isGeneratingSchemes]);

  /**
   * Dispatches an action received from the backend conversation API.
   */
  const handleAction = useCallback(
    (action: any, convId: string, profile?: any) => {
      if (!action) return;

      // Ensure any pending voice confirmation dialog or temporary speech preview is dismissed
      setPendingConfirmation(null);
      setTempSpokenText('');
      setTextInputFallback('');

      const actionType = action.type;
      const actionText = action.text || '';

      if (actionType === 'ask_question') {
        setIsGeneratingSchemes(false);
        setCurrentPrompt(actionText);
        setCurrentField(action.field_name || '');
        setQuickOptions(action.options || []);
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

        // Auto-scroll chat to latest question
        setTimeout(() => {
          flatListRef.current?.scrollToEnd({ animated: true });
        }, 120);

        // Play assistant spoken voice if available and conversation screen is active
        if (action.audio_base64 && isActive) {
          playTTSAudio(action.audio_base64).catch(() => {});
        }

        // Switch to listening
        setTimeout(() => {
          setAssistantState('listening');
        }, 1200);
      } else if (actionType === 'request_document') {
        setIsGeneratingSchemes(false);
        setAssistantState('thinking');
        onNavigateToDocument(convId, action.document_type || 'income_certificate');
      } else if (actionType === 'present_results') {
        stopTTSAudio().catch(() => {});
        setIsGeneratingSchemes(false);
        setAssistantState('speaking');
        saveUserSession({
          id: convId,
          citizenProfile: profile || {},
          recommendedSchemes: action.schemes || [],
          statedNeed: actionText,
        });
        onNavigateToResults(convId, action.schemes || [], actionText, action.audio_base64, profile);
      } else if (actionType === 'escalate') {
        setIsGeneratingSchemes(false);
        setAssistantState('speaking');
        onNavigateToEscalation(convId, action.csc_info || {}, actionText);
      }
    },
    [onNavigateToDocument, onNavigateToResults, onNavigateToEscalation]
  );

  /**
   * Flushes offline queued responses and applies returned backend actions.
   */
  const retryQueuedResponses = useCallback(async () => {
    if (getQueuedCount() === 0 || !conversationId) return;
    setAssistantState('thinking');
    setCurrentPrompt('सर्वर से उत्तर भेजा जा रहा है...');

    try {
      const { remaining } = await flushOfflineQueue(async (item) => {
        const targetConvId = item.conversationId || conversationId;
        if (!targetConvId) return false;

        const payload = item.audioBase64
          ? { audio_base64: item.audioBase64 }
          : { text: item.text || '' };

        const res = await fetch(API_ENDPOINTS.conversationRespond(targetConvId), {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Accept: 'application/json',
          },
          body: JSON.stringify(payload),
        });

        if (res.ok) {
          const turnData = await res.json();
          setIsOffline(false);
          if (turnData.citizen_profile) {
            setQuestionProgress((prev) => ({
              ...prev,
              current: Math.min(prev.current + 1, prev.total),
            }));
          }
          handleAction(turnData.action, targetConvId, turnData.citizen_profile);
          return true;
        }
        return false;
      });

      setQueuedItemsCount(remaining);
      setAssistantState('listening');
      if (remaining === 0) {
        setIsOffline(false);
      }
    } catch (_e) {
      setAssistantState('listening');
    }
  }, [conversationId, handleAction]);

  // Periodic automatic sync attempt for queued items
  useEffect(() => {
    if (queuedItemsCount === 0) return;
    const interval = setInterval(() => {
      retryQueuedResponses();
    }, 3000);
    return () => clearInterval(interval);
  }, [queuedItemsCount, retryQueuedResponses]);

  // Handle connectivity updates
  useEffect(() => {
    const unsubscribe = subscribeConnectivity((online) => {
      setIsOffline(!online);
      if (online) {
        retryQueuedResponses();
      }
    });
    return unsubscribe;
  }, [retryQueuedResponses]);

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

    // Immediately dismiss any pending comprehension box and temp previews
    setPendingConfirmation(null);
    setTempSpokenText('');
    setTextInputFallback('');

    // If answering the final baseline question, trigger the dedicated scheme generation loading view
    if (questionProgress.current >= questionProgress.total) {
      setIsGeneratingSchemes(true);
      setAssistantState('thinking');
      setCurrentPrompt('आपकी जानकारी दर्ज कर ली गई है। उपयुक्त सरकारी योजनाएं खोजी जा रही हैं...');
    }

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

    setTimeout(() => {
      flatListRef.current?.scrollToEnd({ animated: true });
    }, 100);

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
        setIsGeneratingSchemes(false);
        setAssistantState('listening');
        setCurrentPrompt('आवाज़ साफ़ सुनाई नहीं दी। कृपया दोबारा बोलें, नीचे लिखें या विकल्प चुनें।');
        setShowTextInput(true);
        return;
      }

      const turnData = await response.json();
      setIsOffline(false);

      if (turnData.citizen_profile) {
        // Increment question progress
        const targetQ = typeof turnData.question_index === 'number'
          ? turnData.question_index + 1
          : Math.min(questionProgress.current + 1, questionProgress.total);
        setQuestionProgress((prev) => ({
          ...prev,
          current: targetQ,
        }));
      }

      handleAction(turnData.action, conversationId, turnData.citizen_profile);
    } catch (_err) {
      setIsGeneratingSchemes(false);
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

    // Immediately dismiss any pending comprehension box and temp previews
    setPendingConfirmation(null);
    setTempSpokenText('');
    setTextInputFallback('');

    // If answering the final baseline question, trigger the dedicated scheme generation loading view
    if (questionProgress.current >= questionProgress.total) {
      setIsGeneratingSchemes(true);
      setAssistantState('thinking');
      setCurrentPrompt('आपकी आवाज़ पहचानी जा रही है और योजनाएं खोजी जा रही हैं...');
    }

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
        setIsGeneratingSchemes(false);
        setAssistantState('listening');
        setCurrentPrompt('आवाज़ साफ़ सुनाई नहीं दी। कृपया दोबारा बोलें, नीचे लिखें या विकल्प चुनें।');
        setShowTextInput(true);
        return;
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

      setTimeout(() => {
        flatListRef.current?.scrollToEnd({ animated: true });
      }, 100);

      if (turnData.citizen_profile) {
        const targetQ = typeof turnData.question_index === 'number'
          ? turnData.question_index + 1
          : Math.min(questionProgress.current + 1, questionProgress.total);
        setQuestionProgress((prev) => ({
          ...prev,
          current: targetQ,
        }));
      }

      handleAction(turnData.action, conversationId, turnData.citizen_profile);
    } catch (_err) {
      setIsGeneratingSchemes(false);
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
   * Voice Mic recording press:
   * Uses real native AudioRecord to capture citizen audio directly to WAV,
   * transcribes it via Whisper / SpeechRecognizer, and presents the Voice Comprehension
   * Confirmation Box ("क्या आपने यही कहा?") with Confirm (✓) and Retry (✕/↺) options.
   */
  const handleMicPress = async () => {
    console.log('[ConversationScreen] handleMicPress called, isRecording:', isRecordingRef.current);
    // Stop any active TTS audio playing first
    await stopTTSAudio();

    if (recordingTimerRef.current) {
      clearTimeout(recordingTimerRef.current);
      recordingTimerRef.current = null;
    }

    if (isRecordingRef.current) {
      // User tapped mic button while active: finish recording
      isRecordingRef.current = false;
      setIsRecording(false);
      setAssistantState('thinking');
      setCurrentPrompt('पहचाना जा रहा है (Processing with Whisper ASR)...');

      try {
        const speechText = await stopVoiceRecognition().catch(() => '');
        let textToReview = (typeof speechText === 'string' && speechText.trim().length > 0)
          ? speechText.trim()
          : tempSpokenTextRef.current.trim();

        if (textToReview.length > 0) {
          setPendingConfirmation(textToReview);
          setTextInputFallback(textToReview);
          setAssistantState('listening');
          setCurrentPrompt(`पहचाना गया (Whisper ASR): "${textToReview}"`);
        } else {
          setAssistantState('listening');
          setCurrentPrompt('आवाज़ साफ़ सुनाई नहीं दी। कृपया दोबारा बोलें, नीचे लिखें या विकल्प चुनें।');
          setShowTextInput(true);
        }
      } catch (_recErr) {
        setAssistantState('listening');
        setCurrentPrompt('रिकॉर्डिंग पूरी नहीं हो पाई। कृपया दोबारा बोलें, नीचे लिखें या विकल्प चुनें।');
        setShowTextInput(true);
      }
      return;
    }

    // Start native voice recognition
    if (Platform.OS === 'android') {
      try {
        const hasPerm = await PermissionsAndroid.check(PermissionsAndroid.PERMISSIONS.RECORD_AUDIO);
        if (!hasPerm) {
          const res = await PermissionsAndroid.request(PermissionsAndroid.PERMISSIONS.RECORD_AUDIO, {
            title: 'माइक्रोफ़ोन अनुमति (Microphone Permission)',
            message: 'योजनावाणी से बोलकर बातचीत करने के लिए माइक्रोफ़ोन की अनुमति आवश्यक है।',
            buttonPositive: 'अनुमति दें (Allow)',
            buttonNegative: 'रद्द करें (Cancel)',
          });
          if (res !== PermissionsAndroid.RESULTS.GRANTED) {
            setCurrentPrompt('माइक्रोफ़ोन अनुमति नहीं मिली। कृपया नीचे लिखें या विकल्प चुनें।');
            setShowTextInput(true);
            return;
          }
        }
      } catch (_e) {}
    }

    setPendingConfirmation(null);
    setTempSpokenText('');
    tempSpokenTextRef.current = '';
    isRecordingRef.current = true;
    setIsRecording(true);
    setAssistantState('listening');
    setCurrentPrompt('🎙️ योजनावाणी सुन रही है... बोलना पूरा होने पर लाल बटन (⏹) दबाएं');

    try {
      await startVoiceRecognition('hi-IN');
      // Auto-stop safety timeout: after 6 seconds of recording, automatically finalize and transcribe
      recordingTimerRef.current = setTimeout(() => {
        if (isRecordingRef.current) {
          handleMicPress();
        }
      }, 6000);
    } catch (_startErr) {
      isRecordingRef.current = false;
      setIsRecording(false);
      setAssistantState('listening');
      setCurrentPrompt('माइक शुरू नहीं हो पाया। कृपया नीचे लिखें या विकल्प चुनें।');
      setShowTextInput(true);
    }
  };

  /**
   * User confirms the comprehended text is correct: submits to server.
   */
  const handleConfirmSubmission = async () => {
    if (!pendingConfirmation) return;
    const textToSend = pendingConfirmation;
    setPendingConfirmation(null);
    setTempSpokenText('');
    await submitCitizenResponse(textToSend);
  };

  /**
   * User indicates the comprehended text is WRONG:
   * Clears the current input, gives them option to go back and start taking input again immediately.
   */
  const handleRetryVoiceInput = async () => {
    setPendingConfirmation(null);
    setTempSpokenText('');
    setTextInputFallback('');
    setCurrentPrompt('कृपया दोबारा बोलें, योजनावाणी फिर से सुन रही है...');
    setTimeout(() => {
      handleMicPress();
    }, 250);
  };

  /**
   * Step back to the PREVIOUS question if the citizen realizes a previous answer was wrong.
   * Completely purges the previous answers for that question and subsequent turns from the screen.
   */
  const handleGoBackQuestion = async () => {
    if (!conversationId || questionProgress.current <= 1) return;
    setPendingConfirmation(null);
    setTempSpokenText('');
    setTextInputFallback('');
    setIsGeneratingSchemes(false);
    setAssistantState('thinking');
    setCurrentPrompt('पिछले सवाल पर वापस जा रहे हैं...');

    try {
      const res = await fetch(API_ENDPOINTS.conversationBack(conversationId), {
        method: 'POST',
        headers: { Accept: 'application/json' },
      });
      if (!res.ok) throw new Error(`Back failed with ${res.status}`);
      const data = await res.json();

      const targetIndex = typeof data.question_index === 'number'
        ? data.question_index
        : Math.max(0, questionProgress.current - 2);

      setQuestionProgress({
        current: targetIndex + 1,
        total: data.total_questions || 9,
      });

      const nextQuestionText = data.action?.text || '';

      // Purge all answered messages from target question onwards.
      // At question index k, exactly 2 * k previous messages exist (pairs of Q & A).
      setMessages((prev) => {
        const kept = prev.slice(0, targetIndex * 2);
        return [
          ...kept,
          {
            id: `msg_${Date.now()}`,
            speaker: 'assistant',
            text: nextQuestionText,
            timestamp: Date.now(),
          },
        ];
      });

      setCurrentPrompt(nextQuestionText);
      setCurrentField(data.action?.field_name || '');
      setQuickOptions(data.action?.options || []);
      setAssistantState('speaking');

      if (data.action?.audio_base64 && isActive) {
        playTTSAudio(data.action.audio_base64).catch(() => {});
      }

      setTimeout(() => {
        setAssistantState('listening');
        flatListRef.current?.scrollToEnd({ animated: true });
      }, 1200);
    } catch (e) {
      setAssistantState('listening');
      setCurrentPrompt('वापस जाने में त्रुटि हुई। कृपया नीचे से उत्तर दें।');
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" />
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >

      {/* Top Header */}
      <View style={styles.topBar}>
        <TouchableOpacity onPress={onBackToOnboarding} style={styles.backButton}>
          <Text style={styles.backButtonText}>✕ छोड़ें</Text>
        </TouchableOpacity>
        <View style={styles.topTitleContainer}>
          <Text style={styles.topTitle}>योजनावाणी सहायक</Text>
          <Text style={styles.progressText}>
            प्रश्न {questionProgress.current} / {questionProgress.total}
          </Text>
        </View>
        <View style={styles.topRightActions}>
          <TouchableOpacity
            onPress={() => setShowTextInput(!showTextInput)}
            style={styles.keyboardToggle}
            accessibilityLabel="कीबोर्ड दिखाएं/छिपाएं"
          >
            <Text style={styles.keyboardToggleText}>{showTextInput ? '⌨️' : '🎙️'}</Text>
          </TouchableOpacity>
          {questionProgress.current > 1 && (
            <TouchableOpacity
              onPress={handleGoBackQuestion}
              style={styles.undoButton}
              accessibilityLabel="पिछला सवाल सुधारें"
            >
              <Text style={styles.undoButtonText}>↶ पिछला</Text>
            </TouchableOpacity>
          )}
        </View>
      </View>

      {/* Offline Alert Banner */}
      {isOffline && (
        <View style={styles.offlineBanner}>
          <Text style={styles.offlineText}>
            ⚠️ {queuedItemsCount > 0 ? `${queuedItemsCount} उत्तर कतारबद्ध (Queued)` : 'ऑफ़लाइन मोड — इंटरनेट से जुड़ने का प्रयास'}
          </Text>
          <TouchableOpacity
            style={styles.retryBannerButton}
            onPress={retryQueuedResponses}
            activeOpacity={0.8}
          >
            <Text style={styles.retryBannerButtonText}>🔄 दोबारा भेजें (Retry)</Text>
          </TouchableOpacity>
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
          {assistantState === 'listening' && (isRecording ? '🎙️ योजनावाणी सुन रही है (Whisper ASR)...' : '🎙️ बोलने के लिए नीचे बड़ा माइक दबाएं')}
          {assistantState === 'thinking' && '⏳ जानकारी जाँची जा रही है, थोड़ा रुकें...'}
        </Text>
      </View>

      {/* Floating Current Question Pill (Only visible if the citizen has scrolled upwards into past chat) */}
      {isScrolledAwayFromBottom && (
        <TouchableOpacity
          style={styles.floatingCurrentQuestionBanner}
          activeOpacity={0.85}
          onPress={() => flatListRef.current?.scrollToEnd({ animated: true })}
        >
          <View style={styles.floatingQuestionHeader}>
            <Text style={styles.floatingQuestionBadge}>📌 सवाल {questionProgress.current} (वर्तमान):</Text>
            <Text style={styles.floatingQuestionAction}>वर्तमान सवाल पर जाएं ⤓</Text>
          </View>
          <Text style={styles.floatingQuestionText} numberOfLines={1}>
            {currentPrompt}
          </Text>
        </TouchableOpacity>
      )}

      {/* Live Streaming Speech Preview (Temp text on screen while speaking) */}
      {isRecording && (
        <View style={styles.liveStreamingCard}>
          <View style={styles.liveHeader}>
            <View style={styles.livePulseDot} />
            <Text style={styles.liveStreamingTitle}>योजनावाणी सुन रही है (Live Whisper ASR):</Text>
          </View>
          <Text style={styles.liveStreamingText}>
            {tempSpokenText ? `"${tempSpokenText}"` : 'बोलना शुरू करें, आपकी आवाज़ यहाँ दिखेगी...'}
          </Text>
        </View>
      )}

      {/* Comprehension Verification & Correction Card */}
      {pendingConfirmation !== null && !isGeneratingSchemes && (
        <View style={styles.confirmationCard}>
          <View style={styles.confirmationHeaderRow}>
            <Text style={styles.confirmationBadge}>🤖 सहायक ने समझा:</Text>
            <TouchableOpacity
              onPress={() => setPendingConfirmation(null)}
              style={styles.dismissConfirmationButton}
              accessibilityLabel="बंद करें"
            >
              <Text style={styles.dismissConfirmationText}>✕</Text>
            </TouchableOpacity>
          </View>
          <View style={styles.confirmationTextBubble}>
            <Text style={styles.confirmationRecognizedText}>"{pendingConfirmation}"</Text>
          </View>
          <View style={styles.confirmationActionsRow}>
            {/* RETRY / GO BACK & RE-SPEAK */}
            <TouchableOpacity
              style={styles.retryButton}
              activeOpacity={0.8}
              onPress={handleRetryVoiceInput}
              accessibilityLabel="गलत सुना? दोबारा बोलें"
            >
              <Text style={styles.retryButtonText}>↺ गलत सुना? दोबारा बोलें</Text>
            </TouchableOpacity>

            {/* CONFIRM & PROCEED */}
            <TouchableOpacity
              style={styles.confirmButton}
              activeOpacity={0.8}
              onPress={handleConfirmSubmission}
              accessibilityLabel="हाँ, सही है (आगे बढ़ें)"
            >
              <Text style={styles.confirmButtonText}>✓ हाँ, सही है (आगे बढ़ें)</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}

      {/* Visual Chat Transcript (Primary View, Full Height) */}
      <FlatList
        ref={flatListRef}
        style={{ flex: 1 }}
        keyboardShouldPersistTaps="handled"
        data={messages}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.transcriptList}
        onScroll={(event) => {
          const { layoutMeasurement, contentOffset, contentSize } = event.nativeEvent;
          const isCloseToBottom = layoutMeasurement.height + contentOffset.y >= contentSize.height - 60;
          setIsScrolledAwayFromBottom(!isCloseToBottom);
        }}
        scrollEventThrottle={100}
        onContentSizeChange={() => {
          if (!isScrolledAwayFromBottom) {
            flatListRef.current?.scrollToEnd({ animated: true });
          }
        }}
        renderItem={({ item, index }) => {
          const isLatestAssistant = item.speaker === 'assistant' && index === messages.length - 1;
          return (
            <View
              style={[
                styles.chatBubble,
                item.speaker === 'assistant' ? styles.bubbleAssistant : styles.bubbleCitizen,
                isLatestAssistant && styles.bubbleAssistantActive,
              ]}
            >
              <View style={styles.bubbleHeaderRow}>
                <Text style={[styles.speakerLabel, isLatestAssistant && styles.speakerLabelActive]}>
                  {item.speaker === 'assistant'
                    ? (isLatestAssistant ? `🤖 वर्तमान सवाल (सवाल ${questionProgress.current})` : '🤖 योजनावाणी सहायक')
                    : '👤 आप (Whisper ASR)'}
                </Text>
                {isLatestAssistant && <View style={styles.activeDotBadge} />}
              </View>
              <Text style={[styles.bubbleText, isLatestAssistant && styles.bubbleTextActive]}>
                {item.text}
              </Text>
            </View>
          );
        }}
      />

      {/* Optional Text Input Fallback - always pinned above keyboard */}
      {showTextInput && !isGeneratingSchemes && (
        <View
          style={[
            styles.textInputAreaWrapper,
            Platform.OS === 'android' && isKeyboardVisible && { marginBottom: keyboardHeight },
          ]}
        >
          {/* Prominent Current Question Banner shown when keyboard is open so the question is NEVER hidden */}
          {isKeyboardVisible && (
            <View style={styles.typingQuestionCard}>
              <View style={styles.typingQuestionHeaderRow}>
                <Text style={styles.typingQuestionBadge}>
                  🤖 वर्तमान सवाल ({questionProgress.current}/{questionProgress.total}):
                </Text>
                <TouchableOpacity
                  onPress={() => Keyboard.dismiss()}
                  style={styles.typingDismissMiniButton}
                  accessibilityLabel="कीबोर्ड बंद करें"
                >
                  <Text style={styles.typingDismissMiniText}>✕ बंद करें</Text>
                </TouchableOpacity>
              </View>
              <Text style={styles.typingQuestionText}>
                {currentPrompt}
              </Text>
            </View>
          )}

          <View style={styles.textInputContainer}>
            <TextInput
              style={styles.textInput}
              placeholder="यहाँ बोलें या लिखें..."
              placeholderTextColor="#64748B"
              value={textInputFallback}
              onChangeText={(text) => {
                setTextInputFallback(text);
                if (text && pendingConfirmation) {
                  setPendingConfirmation(null);
                }
              }}
              onSubmitEditing={() => {
                Keyboard.dismiss();
                if (textInputFallback.trim()) {
                  submitCitizenResponse(textInputFallback.trim());
                }
              }}
              returnKeyType="send"
            />
            {isKeyboardVisible && (
              <TouchableOpacity
                style={styles.textDismissButton}
                onPress={() => Keyboard.dismiss()}
                accessibilityLabel="कीबोर्ड बंद करें"
              >
                <Text style={styles.textDismissButtonText}>✕</Text>
              </TouchableOpacity>
            )}
            <TouchableOpacity
              style={styles.textSendButton}
              onPress={() => {
                Keyboard.dismiss();
                if (textInputFallback.trim()) {
                  submitCitizenResponse(textInputFallback.trim());
                }
              }}
            >
              <Text style={styles.textSendButtonText}>भेजें</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}

      {/* Quick Suggestion Chips for Fast Vernacular Answering (hidden when typing) */}
      {!isKeyboardVisible && quickOptions && quickOptions.length > 0 && !isGeneratingSchemes && (
        <View style={styles.quickOptionsContainer}>
          <Text style={styles.quickOptionsHeader}>सुझाव / विकल्प (त्वरित चयन):</Text>
          <FlatList
            horizontal
            showsHorizontalScrollIndicator={false}
            data={quickOptions}
            keyExtractor={(opt, idx) => `opt_${idx}_${opt}`}
            contentContainerStyle={styles.quickOptionsList}
            renderItem={({ item }) => (
              <TouchableOpacity
                style={styles.quickOptionChip}
                activeOpacity={0.7}
                onPress={() => submitCitizenResponse(item)}
              >
                <Text style={styles.quickOptionText}>{item}</Text>
              </TouchableOpacity>
            )}
          />
        </View>
      )}

      {/* Dedicated Scheme Generation Screen Overlay when all questions are answered */}
      {isGeneratingSchemes && (
        <View style={styles.generatingOverlay}>
          <View style={styles.generatingCard}>
            <View style={styles.generatingSpinnerContainer}>
              <ActivityIndicator size="large" color="#FF9933" />
            </View>
            <Text style={styles.generatingTitle}>आपकी जानकारी दर्ज कर ली गई है</Text>
            <Text style={styles.generatingSubtitle}>
              योजनावाणी आपके विवरण के आधार पर उपयुक्त सरकारी योजनाएं खोज रही है और पात्रता नियमों की जाँच कर रही है...
            </Text>

            <View style={styles.generatingVoiceBadge}>
              <Text style={styles.generatingVoiceBadgeIcon}>🔊</Text>
              <Text style={styles.generatingVoiceBadgeText}>
                सहायक आपको बोलकर बता रहा है...
              </Text>
            </View>

            <View style={styles.generatingStepsContainer}>
              <View style={styles.stepItemRow}>
                <Text style={styles.stepCheckIcon}>✓</Text>
                <Text style={styles.stepCheckText}>बुनियादी साक्षात्कार पूर्ण (9/9 उत्तर प्राप्त)</Text>
              </View>
              <View style={styles.stepItemRow}>
                <ActivityIndicator size="small" color="#FF9933" style={{ marginRight: 10 }} />
                <Text style={styles.stepActiveText}>सरकारी योजनाओं से मिलान जारी (ChromaDB + Agent)...</Text>
              </View>
              <View style={styles.stepItemRow}>
                <Text style={styles.stepPendingIcon}>⏳</Text>
                <Text style={styles.stepPendingText}>पात्रता नियमों का मूल्यांकन (Deterministic Rules)</Text>
              </View>
            </View>

            <View style={styles.generatingNoteBox}>
              <Text style={styles.generatingNoteText}>
                💡 कृपया कुछ क्षण प्रतीक्षा करें, परिणाम कुछ ही सेकंड में स्क्रीन पर प्रदर्शित होंगे।
              </Text>
            </View>
          </View>
        </View>
      )}

      {/* Main Center Voice Recording Button (Hidden during generating overlay AND when keyboard is visible) */}
      {!isGeneratingSchemes && !isKeyboardVisible && (
        <View style={styles.micControlArea}>
          <View style={styles.micButtonWrapper}>
            <TouchableOpacity
              style={[styles.micButton, isRecording && styles.micButtonActive]}
              activeOpacity={0.82}
              onPress={handleMicPress}
            >
              <View style={[styles.micInnerCircle, isRecording && styles.micInnerCircleActive]}>
                <Text style={styles.micIconText}>{isRecording ? '⏹' : '🎙️'}</Text>
              </View>
            </TouchableOpacity>
          </View>
          <Text style={styles.micInstruction}>
            {isRecording ? '⏹ बोलना खत्म होने पर यहाँ दबाएं' : '🎙️ बोलने के लिए यहाँ दबाएं'}
          </Text>
        </View>
      )}
      </KeyboardAvoidingView>
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
    paddingVertical: 10,
    paddingHorizontal: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  offlineText: {
    color: '#FECACA',
    fontSize: 13,
    fontWeight: '700',
    flex: 1,
  },
  retryBannerButton: {
    backgroundColor: '#FF9933',
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 8,
    marginLeft: 8,
  },
  retryBannerButtonText: {
    color: '#0A0F1D',
    fontSize: 12,
    fontWeight: '800',
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
  topRightActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  transcriptList: {
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 24,
    flexGrow: 1,
  },
  chatBubble: {
    maxWidth: '88%',
    padding: 14,
    borderRadius: 16,
    marginBottom: 14,
  },
  bubbleAssistant: {
    alignSelf: 'flex-start',
    backgroundColor: '#1B263B',
    borderTopLeftRadius: 4,
    borderWidth: 1,
    borderColor: '#334155',
  },
  bubbleAssistantActive: {
    backgroundColor: '#1E293B',
    borderColor: '#FF9933',
    borderWidth: 2,
    borderLeftWidth: 6,
    borderLeftColor: '#FF9933',
    shadowColor: '#FF9933',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.25,
    shadowRadius: 6,
    elevation: 4,
  },
  bubbleCitizen: {
    alignSelf: 'flex-end',
    backgroundColor: '#0F766E',
    borderTopRightRadius: 4,
  },
  bubbleHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 6,
  },
  speakerLabel: {
    fontSize: 13,
    fontWeight: '700',
    color: '#94A3B8',
  },
  speakerLabelActive: {
    color: '#FFD166',
    fontWeight: '800',
  },
  activeDotBadge: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#FF9933',
  },
  bubbleText: {
    color: '#F8FAFC',
    fontSize: 19,
    lineHeight: 28,
    fontWeight: '500',
  },
  bubbleTextActive: {
    color: '#FFFFFF',
    fontSize: 21,
    lineHeight: 30,
    fontWeight: '700',
  },
  floatingCurrentQuestionBanner: {
    backgroundColor: '#1E293B',
    marginHorizontal: 16,
    marginTop: 8,
    borderRadius: 12,
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderWidth: 1.5,
    borderColor: '#FF9933',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.4,
    shadowRadius: 6,
    elevation: 6,
  },
  floatingQuestionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  floatingQuestionBadge: {
    color: '#FFD166',
    fontSize: 12,
    fontWeight: '800',
  },
  floatingQuestionAction: {
    color: '#60A5FA',
    fontSize: 12,
    fontWeight: '800',
  },
  floatingQuestionText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '600',
  },
  dismissConfirmationButton: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    backgroundColor: '#334155',
    borderRadius: 12,
  },
  dismissConfirmationText: {
    color: '#CBD5E1',
    fontSize: 14,
    fontWeight: '800',
  },
  textInputAreaWrapper: {
    borderTopWidth: 1,
    borderTopColor: '#334155',
    backgroundColor: '#1E293B',
    elevation: 8,
    zIndex: 999,
  },
  typingQuestionCard: {
    backgroundColor: '#0F172A',
    paddingHorizontal: 16,
    paddingTop: 10,
    paddingBottom: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#334155',
    borderLeftWidth: 4,
    borderLeftColor: '#FF9933',
  },
  typingQuestionHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  typingQuestionBadge: {
    color: '#FFD166',
    fontSize: 13,
    fontWeight: '800',
  },
  typingDismissMiniButton: {
    backgroundColor: '#334155',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  typingDismissMiniText: {
    color: '#CBD5E1',
    fontSize: 12,
    fontWeight: '700',
  },
  typingQuestionText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
    lineHeight: 22,
  },
  textInputContainer: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingVertical: 10,
    backgroundColor: '#1E293B',
    alignItems: 'center',
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
  textDismissButton: {
    backgroundColor: '#334155',
    paddingHorizontal: 12,
    justifyContent: 'center',
    alignItems: 'center',
    borderRadius: 12,
    marginLeft: 8,
  },
  textDismissButtonText: {
    color: '#CBD5E1',
    fontWeight: '800',
    fontSize: 16,
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
    paddingVertical: 18,
    backgroundColor: '#0D1B2A',
    borderTopWidth: 1,
    borderTopColor: '#1E293B',
  },
  micButtonWrapper: {
    width: 104,
    height: 104,
    justifyContent: 'center',
    alignItems: 'center',
  },
  micButton: {
    width: 96,
    height: 96,
    borderRadius: 48,
    backgroundColor: '#FF9933',
    justifyContent: 'center',
    alignItems: 'center',
    elevation: 8,
    shadowColor: '#FF9933',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.45,
    shadowRadius: 8,
    borderWidth: 3,
    borderColor: '#FFAA44',
  },
  micButtonActive: {
    backgroundColor: '#EF4444',
    borderColor: '#F87171',
    shadowColor: '#EF4444',
  },
  micInnerCircle: {
    width: 76,
    height: 76,
    borderRadius: 38,
    backgroundColor: '#E67E00',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#FFD166',
  },
  micInnerCircleActive: {
    backgroundColor: '#DC2626',
    borderColor: '#FECACA',
  },
  micIconText: {
    fontSize: 42,
    textAlign: 'center',
  },
  micInstruction: {
    color: '#F8FAFC',
    fontSize: 16,
    marginTop: 10,
    fontWeight: '700',
    textAlign: 'center',
  },
  quickOptionsContainer: {
    paddingVertical: 10,
    paddingHorizontal: 16,
    backgroundColor: '#0F172A',
    borderTopWidth: 1,
    borderTopColor: '#1E293B',
  },
  quickOptionsHeader: {
    color: '#94A3B8',
    fontSize: 13,
    fontWeight: '700',
    marginBottom: 8,
  },
  quickOptionsList: {
    gap: 8,
    paddingRight: 16,
  },
  quickOptionChip: {
    backgroundColor: '#1E293B',
    borderColor: '#FF9933',
    borderWidth: 1.5,
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 8,
    marginRight: 8,
  },
  quickOptionText: {
    color: '#F8FAFC',
    fontSize: 14,
    fontWeight: '700',
  },
  undoButton: {
    backgroundColor: '#334155',
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#64748B',
  },
  undoButtonText: {
    color: '#FFD166',
    fontSize: 14,
    fontWeight: '800',
  },
  goBackQuestionBar: {
    backgroundColor: '#1E293B',
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#334155',
    alignItems: 'center',
  },
  goBackQuestionText: {
    color: '#93C5FD',
    fontSize: 13,
    fontWeight: '700',
    textAlign: 'center',
  },
  liveStreamingCard: {
    backgroundColor: '#064E3B',
    marginHorizontal: 16,
    marginTop: 8,
    marginBottom: 6,
    borderRadius: 14,
    padding: 14,
    borderWidth: 2,
    borderColor: '#10B981',
    shadowColor: '#10B981',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.3,
    shadowRadius: 6,
    elevation: 4,
  },
  liveHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
  },
  livePulseDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: '#34D399',
    marginRight: 8,
  },
  liveStreamingTitle: {
    color: '#A7F3D0',
    fontSize: 13,
    fontWeight: '800',
  },
  liveStreamingText: {
    color: '#FFFFFF',
    fontSize: 20,
    lineHeight: 28,
    fontWeight: '700',
  },
  confirmationCard: {
    backgroundColor: '#1E293B',
    marginHorizontal: 16,
    marginTop: 8,
    marginBottom: 10,
    borderRadius: 16,
    padding: 16,
    borderWidth: 2,
    borderColor: '#FF9933',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.35,
    shadowRadius: 8,
    elevation: 6,
  },
  confirmationHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  confirmationBadge: {
    color: '#FFD166',
    fontSize: 14,
    fontWeight: '800',
  },
  confirmationHint: {
    color: '#94A3B8',
    fontSize: 13,
    fontWeight: '600',
  },
  confirmationTextBubble: {
    backgroundColor: '#0F172A',
    borderRadius: 12,
    padding: 14,
    marginBottom: 14,
    borderWidth: 1,
    borderColor: '#334155',
  },
  confirmationRecognizedText: {
    color: '#FFFFFF',
    fontSize: 22,
    lineHeight: 30,
    fontWeight: '700',
  },
  confirmationActionsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 10,
  },
  retryButton: {
    flex: 1,
    backgroundColor: '#7F1D1D',
    borderColor: '#EF4444',
    borderWidth: 1.5,
    paddingVertical: 12,
    paddingHorizontal: 10,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  retryButtonText: {
    color: '#FEE2E2',
    fontSize: 14,
    fontWeight: '800',
    textAlign: 'center',
  },
  confirmButton: {
    flex: 1.2,
    backgroundColor: '#059669',
    borderColor: '#10B981',
    borderWidth: 1.5,
    paddingVertical: 12,
    paddingHorizontal: 10,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  confirmButtonText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '800',
    textAlign: 'center',
  },
  generatingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: '#0D1B2A',
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 24,
    zIndex: 999,
    elevation: 10,
  },
  generatingCard: {
    backgroundColor: '#1E293B',
    borderRadius: 20,
    padding: 24,
    width: '100%',
    alignItems: 'center',
    borderWidth: 1.5,
    borderColor: '#FF9933',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.5,
    shadowRadius: 16,
    elevation: 10,
  },
  generatingSpinnerContainer: {
    width: 70,
    height: 70,
    borderRadius: 35,
    backgroundColor: '#0F172A',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 18,
    borderWidth: 2,
    borderColor: '#FF9933',
  },
  generatingTitle: {
    color: '#F8FAFC',
    fontSize: 22,
    fontWeight: '800',
    textAlign: 'center',
    marginBottom: 10,
  },
  generatingSubtitle: {
    color: '#94A3B8',
    fontSize: 15,
    lineHeight: 22,
    textAlign: 'center',
    marginBottom: 20,
  },
  generatingStepsContainer: {
    width: '100%',
    backgroundColor: '#0F172A',
    borderRadius: 14,
    padding: 16,
    marginBottom: 18,
    borderWidth: 1,
    borderColor: '#334155',
  },
  stepItemRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 6,
  },
  stepCheckIcon: {
    color: '#10B981',
    fontSize: 16,
    fontWeight: '900',
    marginRight: 10,
    width: 20,
    textAlign: 'center',
  },
  stepCheckText: {
    color: '#E2E8F0',
    fontSize: 14,
    fontWeight: '600',
    flex: 1,
  },
  stepActiveText: {
    color: '#FFD166',
    fontSize: 14,
    fontWeight: '700',
    flex: 1,
  },
  stepPendingIcon: {
    fontSize: 14,
    marginRight: 10,
    width: 20,
    textAlign: 'center',
  },
  stepPendingText: {
    color: '#64748B',
    fontSize: 14,
    fontWeight: '500',
    flex: 1,
  },
  generatingNoteBox: {
    backgroundColor: '#1E3A5F',
    borderRadius: 10,
    padding: 12,
    width: '100%',
  },
  generatingNoteText: {
    color: '#93C5FD',
    fontSize: 13,
    lineHeight: 18,
    textAlign: 'center',
    fontWeight: '500',
  },
  generatingVoiceBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#0F172A',
    paddingVertical: 6,
    paddingHorizontal: 14,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#FF9933',
    marginVertical: 10,
  },
  generatingVoiceBadgeIcon: {
    fontSize: 14,
    marginRight: 6,
  },
  generatingVoiceBadgeText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#FFD166',
  },
});
