import React, { useState } from 'react';
import {
  Alert,
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

interface OnboardingScreenProps {
  onStartConversation: () => void;
}

export const OnboardingScreen: React.FC<OnboardingScreenProps> = ({ onStartConversation }) => {
  const [micGranted, setMicGranted] = useState<boolean>(false);
  const [cameraGranted, setCameraGranted] = useState<boolean>(false);
  const [isRequesting, setIsRequesting] = useState<boolean>(false);

  /**
   * Plain-language permission request with prior vernacular explanation.
   * Complies with Android runtime permission requirements.
   */
  const requestAppPermissions = async () => {
    if (Platform.OS !== 'android') {
      setMicGranted(true);
      setCameraGranted(true);
      onStartConversation();
      return;
    }

    setIsRequesting(true);
    try {
      const results = await PermissionsAndroid.requestMultiple([
        PermissionsAndroid.PERMISSIONS.RECORD_AUDIO,
        PermissionsAndroid.PERMISSIONS.CAMERA,
      ]);

      const micOk =
        results[PermissionsAndroid.PERMISSIONS.RECORD_AUDIO] ===
        PermissionsAndroid.RESULTS.GRANTED;
      const camOk =
        results[PermissionsAndroid.PERMISSIONS.CAMERA] ===
        PermissionsAndroid.RESULTS.GRANTED;

      setMicGranted(micOk);
      setCameraGranted(camOk);

      if (micOk && camOk) {
        onStartConversation();
      } else {
        Alert.alert(
          'अनुमति आवश्यक है (Permissions Needed)',
          'योजनावाणी में बिना लिखे केवल बोलकर और दस्तावेज़ स्कैन करके योजनाएं खोजने के लिए माइक्रोफ़ोन और कैमरा आवश्यक है।',
          [
            { text: 'पुनः प्रयास करें', onPress: () => requestAppPermissions() },
            { text: 'आगे बढ़ें', onPress: () => onStartConversation() },
          ]
        );
      }
    } catch (_err) {
      onStartConversation();
    } finally {
      setIsRequesting(false);
    }
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

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Header Branding */}
        <View style={styles.header}>
          <Text style={styles.devanagariTitle}>योजनावाणी</Text>
          <Text style={styles.englishTitle}>YojanaVaani</Text>
          <Text style={styles.hindiSubtitle}>
            सिर्फ बोलकर अपने हक की सरकारी योजनाएं खोजें
          </Text>
        </View>

        {/* Purpose Card */}
        <View style={styles.card}>
          <Text style={styles.cardHeader}>यह ऐप कैसे काम करता है?</Text>
          <Text style={styles.cardText}>
            १. कुछ भी लिखने की ज़रूरत नहीं — सिर्फ बोलकर बात करें।{'\n'}
            २. सहायक आपसे आसान भाषा में ९ सवाल पूछेगा।{'\n'}
            ३. आप बोलकर जवाब दें, हम आपके लिए सही योजना ढूंढेंगे।
          </Text>
        </View>

        {/* Vernacular Permission Explanations */}
        <View style={styles.permissionSection}>
          <Text style={styles.permissionSectionTitle}>
            माइक और कैमरे की अनुमति
          </Text>

          {/* Microphone Card */}
          <View style={[styles.permissionCard, micGranted && styles.permissionCardGranted]}>
            <View style={styles.permissionIconBadge}>
              <Text style={styles.permissionIcon}>🎙️</Text>
            </View>
            <View style={styles.permissionTextContainer}>
              <Text style={styles.permissionTitle}>
                माइक (बोलने के लिए) {micGranted ? '✓ स्वीकृत' : ''}
              </Text>
              <Text style={styles.permissionDescription}>
                अपनी आवाज़ में बोलकर जवाब देने और अपनी बात बताने के लिए।
              </Text>
            </View>
          </View>

          {/* Camera Card */}
          <View style={[styles.permissionCard, cameraGranted && styles.permissionCardGranted]}>
            <View style={styles.permissionIconBadge}>
              <Text style={styles.permissionIcon}>📷</Text>
            </View>
            <View style={styles.permissionTextContainer}>
              <Text style={styles.permissionTitle}>
                कैमरा (कागज़ दिखाने के लिए) {cameraGranted ? '✓ स्वीकृत' : ''}
              </Text>
              <Text style={styles.permissionDescription}>
                राशन कार्ड या आय प्रमाण पत्र की फोटो खींचकर जांचने के लिए।
              </Text>
            </View>
          </View>
        </View>

        {/* Privacy Note */}
        <View style={styles.privacyNote}>
          <Text style={styles.privacyText}>
            🔒 आपकी आवाज़ और जानकारी पूरी तरह सुरक्षित रखी जाती है।
          </Text>
        </View>

        {/* Action Button */}
        <TouchableOpacity
          style={styles.startButton}
          activeOpacity={0.85}
          onPress={requestAppPermissions}
          disabled={isRequesting}
        >
          <Text style={styles.startButtonText}>
            {isRequesting ? 'शुरू हो रहा है...' : 'बातचीत शुरू करें (यहाँ दबाएं) 🎙️'}
          </Text>
        </TouchableOpacity>
      </ScrollView>
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
  scrollContent: {
    paddingHorizontal: 20,
    paddingTop: 24,
    paddingBottom: 40,
  },
  header: {
    alignItems: 'center',
    marginBottom: 24,
  },
  devanagariTitle: {
    fontSize: 42,
    fontWeight: '900',
    color: '#FF9933',
    letterSpacing: 1.5,
  },
  englishTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: '#FFFFFF',
    marginTop: 2,
    letterSpacing: 2,
  },
  hindiSubtitle: {
    fontSize: 20,
    color: '#E0E1DD',
    marginTop: 8,
    textAlign: 'center',
    fontWeight: '600',
    lineHeight: 28,
  },
  card: {
    backgroundColor: '#1B263B',
    borderRadius: 16,
    padding: 20,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#415A77',
  },
  cardHeader: {
    fontSize: 22,
    fontWeight: '800',
    color: '#FFD166',
    marginBottom: 10,
  },
  cardText: {
    fontSize: 18,
    color: '#E0E1DD',
    lineHeight: 28,
    fontWeight: '500',
  },
  permissionSection: {
    marginBottom: 20,
  },
  permissionSectionTitle: {
    fontSize: 20,
    fontWeight: '800',
    color: '#FFFFFF',
    marginBottom: 14,
  },
  permissionCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1E293B',
    borderRadius: 14,
    padding: 16,
    marginBottom: 14,
    borderWidth: 1,
    borderColor: '#334155',
  },
  permissionCardGranted: {
    borderColor: '#10B981',
    backgroundColor: '#064E3B22',
  },
  permissionIconBadge: {
    width: 52,
    height: 52,
    borderRadius: 26,
    backgroundColor: '#0F172A',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  permissionIcon: {
    fontSize: 28,
  },
  permissionTextContainer: {
    flex: 1,
  },
  permissionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#F8FAFC',
    marginBottom: 4,
  },
  permissionDescription: {
    fontSize: 15,
    color: '#CBD5E1',
    lineHeight: 22,
  },
  privacyNote: {
    backgroundColor: '#0F172A',
    borderRadius: 12,
    padding: 14,
    marginBottom: 24,
    borderLeftWidth: 4,
    borderLeftColor: '#3B82F6',
  },
  privacyText: {
    fontSize: 15,
    color: '#94A3B8',
    lineHeight: 22,
    fontWeight: '500',
  },
  startButton: {
    backgroundColor: '#FF9933',
    paddingVertical: 18,
    borderRadius: 16,
    alignItems: 'center',
    shadowColor: '#FF9933',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.45,
    shadowRadius: 10,
    elevation: 6,
  },
  startButtonText: {
    fontSize: 22,
    fontWeight: '900',
    color: '#0D1B2A',
  },
});
