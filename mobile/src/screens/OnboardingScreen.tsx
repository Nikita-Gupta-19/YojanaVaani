import React, { useEffect, useRef, useState } from 'react';
import {
  Animated,
  PermissionsAndroid,
  Platform,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { API_ENDPOINTS } from '../config';
import { playTTSAudio, stopTTSAudio } from '../services/audioService';

interface OnboardingScreenProps {
  onStartConversation: () => void;
}

const INTRO_VOICE_TEXT =
  'नमस्ते! मैं योजनावाणी सहायक हूँ। सिर्फ बोलकर सरकारी योजनाएं खोजने के लिए नीचे दिए गए माइक बटन को दबाएं।';

export const OnboardingScreen: React.FC<OnboardingScreenProps> = ({ onStartConversation }) => {
  const [isPlayingIntro, setIsPlayingIntro] = useState<boolean>(false);
  const [isStarting, setIsStarting] = useState<boolean>(false);

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
        await PermissionsAndroid.requestMultiple([
          PermissionsAndroid.PERMISSIONS.RECORD_AUDIO,
          PermissionsAndroid.PERMISSIONS.CAMERA,
        ]);
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

        {/* Subtle footer */}
        <View style={styles.footerNote}>
          <Text style={styles.footerText}>
            🔒 लिखना नहीं पड़ेगा — सिर्फ बोलकर बातचीत करें
          </Text>
        </View>
      </View>
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
