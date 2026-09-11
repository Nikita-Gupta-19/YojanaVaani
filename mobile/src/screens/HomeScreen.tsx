import React, { useEffect, useRef, useState, useCallback } from 'react';
import {
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
  Animated,
  ScrollView,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { checkBackendHealth } from '../config';

export const HomeScreen: React.FC = () => {
  // Ambient pulse animation for the outer halo
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const haloOpacityAnim = useRef(new Animated.Value(0.2)).current;
  // Interactive spring scale animation on button press
  const scaleAnim = useRef(new Animated.Value(1)).current;
  const [isPressed, setIsPressed] = useState(false);

  // Backend connectivity state
  const [isBackendReachable, setIsBackendReachable] = useState<boolean | null>(null);
  const [isCheckingBackend, setIsCheckingBackend] = useState<boolean>(false);

  const verifyBackend = useCallback(async () => {
    setIsCheckingBackend(true);
    const reachable = await checkBackendHealth();
    setIsBackendReachable(reachable);
    setIsCheckingBackend(false);
  }, []);

  useEffect(() => {
    verifyBackend();
  }, [verifyBackend]);

  useEffect(() => {
    // Gentle continuous breathing pulse to indicate microphone readiness
    const pulseLoop = Animated.loop(
      Animated.parallel([
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 1.08,
            duration: 1800,
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1.0,
            duration: 1800,
            useNativeDriver: true,
          }),
        ]),
        Animated.sequence([
          Animated.timing(haloOpacityAnim, {
            toValue: 0.35,
            duration: 1800,
            useNativeDriver: true,
          }),
          Animated.timing(haloOpacityAnim, {
            toValue: 0.18,
            duration: 1800,
            useNativeDriver: true,
          }),
        ]),
      ])
    );
    pulseLoop.start();
    return () => pulseLoop.stop();
  }, [pulseAnim, haloOpacityAnim]);

  const handlePressIn = () => {
    setIsPressed(true);
    Animated.spring(scaleAnim, {
      toValue: 0.92,
      useNativeDriver: true,
      friction: 5,
      tension: 120,
    }).start();
  };

  const handlePressOut = () => {
    setIsPressed(false);
    Animated.spring(scaleAnim, {
      toValue: 1.0,
      useNativeDriver: true,
      friction: 4,
      tension: 100,
    }).start();
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" />

      {/* Top Banner Accent - Indian Tricolor */}
      <View style={styles.topAccentBar} accessible={false}>
        <View style={[styles.tricolorBar, { backgroundColor: '#FF9933' }]} />
        <View style={[styles.tricolorBar, { backgroundColor: '#FFFFFF' }]} />
        <View style={[styles.tricolorBar, { backgroundColor: '#138808' }]} />
      </View>

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        bounces={false}
        showsVerticalScrollIndicator={false}
      >
        {/* Header Branding */}
        <View style={styles.header}>
          <Text style={styles.devanagariTitle}>योजनावाणी</Text>
          <Text style={styles.englishTitle}>YojanaVaani</Text>
          <Text style={styles.tagline}>
            Voice-First Government Scheme Navigator
          </Text>
          <Text style={styles.hindiTagline}>
            अपनी आवाज़ में अपनी सरकारी योजनाएं खोजें
          </Text>
        </View>

        {/* Center Voice Prompt & Animated Microphone Button */}
        <View style={styles.micSection}>
          <Animated.View
            style={[
              styles.micOuterHalo,
              {
                transform: [{ scale: pulseAnim }],
                opacity: haloOpacityAnim,
              },
            ]}
          />
          <View style={styles.micInnerHalo}>
            <Animated.View style={{ transform: [{ scale: scaleAnim }] }}>
              <TouchableOpacity
                style={[
                  styles.micButton,
                  isPressed && styles.micButtonPressed,
                ]}
                activeOpacity={0.9}
                onPressIn={handlePressIn}
                onPressOut={handlePressOut}
                accessibilityLabel="बोलने के लिए माइक बटन"
                accessibilityRole="button"
                accessibilityHint="माइक दबाकर अपनी आवश्यकता या योजना के बारे में बोलें"
              >
                {/* Vector Mic Icon constructed with geometric views */}
                <View style={styles.micIconShape}>
                  <View style={styles.micHead} />
                  <View style={styles.micStem} />
                  <View style={styles.micBase} />
                </View>
              </TouchableOpacity>
            </Animated.View>
          </View>

          <Text style={styles.micInstruction}>
            {isPressed ? 'सुन रहे हैं... (Listening...)' : 'बोलने के लिए माइक दबाएं'}
          </Text>
          <Text style={styles.micInstructionSub}>
            बोलकर अपनी पात्रता जांचें • Tap to Speak
          </Text>
        </View>

        {/* Citizen-Facing Scheme Category Discovery Card */}
        <View style={styles.categoryCard}>
          <View style={styles.categoryHeader}>
            <Text style={styles.categoryHeaderTitle}>हम इन योजनाओं में मदद कर सकते हैं</Text>
            <Text style={styles.categoryHeaderSub}>
              अपनी आवश्यकता या समस्या के बारे में सीधे बोलें
            </Text>
          </View>
          <View style={styles.chipsGrid}>
            <View style={styles.categoryChip}>
              <Text style={styles.chipIcon}>🎓</Text>
              <Text style={styles.chipLabel}>शिक्षा एवं छात्रवृत्ति</Text>
            </View>
            <View style={styles.categoryChip}>
              <Text style={styles.chipIcon}>🏥</Text>
              <Text style={styles.chipLabel}>स्वास्थ्य एवं चिकित्सा</Text>
            </View>
            <View style={styles.categoryChip}>
              <Text style={styles.chipIcon}>🏠</Text>
              <Text style={styles.chipLabel}>आवास एवं मकान</Text>
            </View>
            <View style={styles.categoryChip}>
              <Text style={styles.chipIcon}>🌾</Text>
              <Text style={styles.chipLabel}>कृषि एवं किसान</Text>
            </View>
          </View>
        </View>

        {/* Backend Connectivity Indicator (Rendered only if unreachable) */}
        {isBackendReachable === false && (
          <View style={styles.offlineBanner} accessibilityRole="alert">
            <View style={styles.offlineTextRow}>
              <Text style={styles.offlineIcon}>📡</Text>
              <Text style={styles.offlineText}>
                सर्वर से संपर्क नहीं हो पा रहा है। कृपया इंटरनेट कनेक्शन जांचें।
              </Text>
            </View>
            <TouchableOpacity
              style={styles.retryButton}
              onPress={verifyBackend}
              disabled={isCheckingBackend}
              activeOpacity={0.8}
              accessibilityRole="button"
              accessibilityLabel="पुनः प्रयास करें"
              accessibilityHint="सर्वर से पुनः संपर्क जांचने के लिए दबाएं"
            >
              {isCheckingBackend ? (
                <ActivityIndicator size="small" color="#0A0F1D" />
              ) : (
                <Text style={styles.retryButtonText}>पुनः प्रयास करें</Text>
              )}
            </TouchableOpacity>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0A0F1D',
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'space-between',
    paddingHorizontal: 24,
    paddingTop: 16,
    paddingBottom: 28,
  },
  topAccentBar: {
    flexDirection: 'row',
    height: 4,
    width: '100%',
  },
  tricolorBar: {
    flex: 1,
    height: 4,
  },
  header: {
    alignItems: 'center',
    marginTop: 8,
  },
  devanagariTitle: {
    fontSize: 36,
    fontWeight: '800',
    color: '#F8FAFC',
    letterSpacing: 1,
  },
  englishTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#FF9933',
    letterSpacing: 1.5,
    marginTop: 2,
    textTransform: 'uppercase',
  },
  tagline: {
    fontSize: 14,
    color: '#CBD5E1',
    marginTop: 6,
    textAlign: 'center',
    fontWeight: '500',
  },
  hindiTagline: {
    fontSize: 13,
    color: '#94A3B8',
    marginTop: 4,
    textAlign: 'center',
  },
  micSection: {
    alignItems: 'center',
    justifyContent: 'center',
    marginVertical: 24,
  },
  micOuterHalo: {
    position: 'absolute',
    width: 176,
    height: 176,
    borderRadius: 88,
    backgroundColor: 'rgba(255, 153, 51, 0.25)',
    borderWidth: 1.5,
    borderColor: 'rgba(255, 153, 51, 0.45)',
  },
  micInnerHalo: {
    width: 134,
    height: 134,
    borderRadius: 67,
    backgroundColor: 'rgba(255, 153, 51, 0.14)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  micButton: {
    width: 92,
    height: 92,
    borderRadius: 46,
    backgroundColor: '#FF9933',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#FF9933',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.55,
    shadowRadius: 18,
    elevation: 14,
  },
  micButtonPressed: {
    backgroundColor: '#EA580C',
    shadowOpacity: 0.75,
    shadowRadius: 24,
  },
  micIconShape: {
    alignItems: 'center',
  },
  micHead: {
    width: 18,
    height: 28,
    backgroundColor: '#0A0F1D',
    borderRadius: 9,
    borderWidth: 3,
    borderColor: '#0A0F1D',
  },
  micStem: {
    width: 4,
    height: 10,
    backgroundColor: '#0A0F1D',
    marginTop: 2,
  },
  micBase: {
    width: 22,
    height: 4,
    backgroundColor: '#0A0F1D',
    borderRadius: 2,
  },
  micInstruction: {
    fontSize: 20,
    fontWeight: '700',
    color: '#F8FAFC',
    marginTop: 22,
    textAlign: 'center',
  },
  micInstructionSub: {
    fontSize: 13,
    color: '#CBD5E1',
    marginTop: 6,
    textAlign: 'center',
  },
  categoryCard: {
    backgroundColor: '#131D33',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#24324F',
    marginTop: 12,
  },
  categoryHeader: {
    marginBottom: 12,
  },
  categoryHeaderTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#F8FAFC',
    textAlign: 'center',
  },
  categoryHeaderSub: {
    fontSize: 12,
    color: '#94A3B8',
    marginTop: 2,
    textAlign: 'center',
  },
  chipsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    gap: 8,
  },
  categoryChip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1A2744',
    borderWidth: 1,
    borderColor: '#2D3E64',
    borderRadius: 20,
    paddingVertical: 7,
    paddingHorizontal: 12,
    width: '48.5%',
  },
  chipIcon: {
    fontSize: 16,
    marginRight: 6,
  },
  chipLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#E2E8F0',
    flexShrink: 1,
  },
  offlineBanner: {
    backgroundColor: 'rgba(245, 158, 11, 0.12)',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(245, 158, 11, 0.35)',
    padding: 14,
    marginTop: 14,
    alignItems: 'center',
  },
  offlineTextRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  offlineIcon: {
    fontSize: 18,
    marginRight: 8,
  },
  offlineText: {
    fontSize: 13,
    color: '#FDE68A',
    fontWeight: '500',
    flex: 1,
    lineHeight: 18,
  },
  retryButton: {
    minHeight: 48,
    minWidth: 140,
    paddingHorizontal: 20,
    backgroundColor: '#FF9933',
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
  },
  retryButtonText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#0A0F1D',
  },
});
