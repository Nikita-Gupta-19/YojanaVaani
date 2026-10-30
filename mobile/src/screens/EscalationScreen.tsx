import React from 'react';
import {
  Linking,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

export interface CSCInfo {
  csc_name?: string;
  helpline?: string;
  address?: string;
  timings?: string;
}

interface EscalationScreenProps {
  conversationId: string;
  cscInfo: CSCInfo;
  spokenText: string;
  onBackToConversation: () => void;
}

export const EscalationScreen: React.FC<EscalationScreenProps> = ({
  cscInfo,
  spokenText,
  onBackToConversation,
}) => {
  const cscName = cscInfo.csc_name || 'हैदरगढ़ डिजिटल सेवा केंद्र (CSC Kendra)';
  const helpline = cscInfo.helpline || '1800-3000-3468';
  const address =
    cscInfo.address || 'तहसील परिसर के पास, हैदरगढ़, जिला बाराबंकी, उत्तर प्रदेश - 225126';
  const timings = cscInfo.timings || 'सुबह 09:00 बजे से शाम 05:00 बजे तक (सोमवार से शनिवार)';

  const handleCallHelpline = () => {
    const cleanNumber = helpline.replace(/[^0-9]/g, '');
    Linking.openURL(`tel:${cleanNumber}`);
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" />

      {/* Top Banner Accent */}
      <View style={styles.topAccentBar}>
        <View style={[styles.tricolorSegment, { backgroundColor: '#FF9933' }]} />
        <View style={[styles.tricolorSegment, { backgroundColor: '#FFFFFF' }]} />
        <View style={[styles.tricolorSegment, { backgroundColor: '#138808' }]} />
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        {/* Warning / Advisory Header */}
        <View style={styles.header}>
          <Text style={styles.headerIcon}>🏢</Text>
          <Text style={styles.headerTitle}>निकटतम ग्राहक सेवा केंद्र (CSC)</Text>
          <Text style={styles.headerSubtitle}>
            यहाँ जाकर किसी भी योजना के लिए मुफ़्त मदद लें
          </Text>
        </View>

        {/* Spoken Advice Box */}
        <View style={styles.adviceBox}>
          <Text style={styles.adviceLabel}>📢 सहायक का संदेश:</Text>
          <Text style={styles.adviceText}>
            {spokenText ||
              'आपकी बात थोड़ी जटिल है। किसी भी परेशानी से बचने के लिए कृपया अपने पास के ग्राहक सेवा केंद्र (CSC) पर जाएं। वहाँ कर्मचारी आपकी पूरी मदद करेंगे।'}
          </Text>
        </View>

        {/* CSC Kiosk Card */}
        <View style={styles.cscCard}>
          <Text style={styles.cscCardHeader}>पास के केंद्र की जानकारी:</Text>

          {/* Name */}
          <View style={styles.detailRow}>
            <Text style={styles.detailIcon}>🏛️</Text>
            <View style={styles.detailTextCol}>
              <Text style={styles.detailLabel}>केंद्र का नाम</Text>
              <Text style={styles.detailValue}>{cscName}</Text>
            </View>
          </View>

          {/* Helpline */}
          <View style={styles.detailRow}>
            <Text style={styles.detailIcon}>📞</Text>
            <View style={styles.detailTextCol}>
              <Text style={styles.detailLabel}>हेल्पलाइन फोन नंबर</Text>
              <Text style={[styles.detailValue, styles.helplineText]}>{helpline}</Text>
            </View>
          </View>

          {/* Address */}
          <View style={styles.detailRow}>
            <Text style={styles.detailIcon}>📍</Text>
            <View style={styles.detailTextCol}>
              <Text style={styles.detailLabel}>पता</Text>
              <Text style={styles.detailValue}>{address}</Text>
            </View>
          </View>

          {/* Timings */}
          <View style={styles.detailRow}>
            <Text style={styles.detailIcon}>🕒</Text>
            <View style={styles.detailTextCol}>
              <Text style={styles.detailLabel}>खुलने का समय</Text>
              <Text style={styles.detailValue}>{timings}</Text>
            </View>
          </View>

          {/* Direct Call Button */}
          <TouchableOpacity
            style={styles.callButton}
            activeOpacity={0.85}
            onPress={handleCallHelpline}
          >
            <Text style={styles.callButtonText}>📞 सीधे केंद्र पर फोन लगाएं</Text>
          </TouchableOpacity>
        </View>

        {/* Back Button */}
        <TouchableOpacity style={styles.backButton} onPress={onBackToConversation}>
          <Text style={styles.backButtonText}>← बातचीत पर वापस जाएं</Text>
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
    padding: 20,
    paddingBottom: 40,
  },
  header: {
    alignItems: 'center',
    marginBottom: 20,
  },
  headerIcon: {
    fontSize: 48,
    marginBottom: 8,
  },
  headerTitle: {
    fontSize: 26,
    fontWeight: '900',
    color: '#FF9933',
    textAlign: 'center',
  },
  headerSubtitle: {
    fontSize: 16,
    color: '#CBD5E1',
    marginTop: 4,
    textAlign: 'center',
    fontWeight: '600',
  },
  adviceBox: {
    backgroundColor: '#1E293B',
    borderRadius: 14,
    padding: 18,
    marginBottom: 20,
    borderLeftWidth: 6,
    borderLeftColor: '#F59E0B',
  },
  adviceLabel: {
    color: '#F59E0B',
    fontSize: 17,
    fontWeight: '800',
    marginBottom: 6,
  },
  adviceText: {
    color: '#F1F5F9',
    fontSize: 18,
    lineHeight: 26,
    fontWeight: '500',
  },
  cscCard: {
    backgroundColor: '#1B263B',
    borderRadius: 16,
    padding: 20,
    borderWidth: 1,
    borderColor: '#415A77',
    marginBottom: 20,
  },
  cscCardHeader: {
    color: '#FFD166',
    fontSize: 18,
    fontWeight: '800',
    marginBottom: 16,
  },
  detailRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 16,
  },
  detailIcon: {
    fontSize: 26,
    marginRight: 14,
    marginTop: 2,
  },
  detailTextCol: {
    flex: 1,
  },
  detailLabel: {
    color: '#94A3B8',
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 2,
  },
  detailValue: {
    color: '#FFFFFF',
    fontSize: 17,
    fontWeight: '700',
    lineHeight: 24,
  },
  helplineText: {
    color: '#34D399',
    fontSize: 20,
    fontWeight: '800',
  },
  callButton: {
    backgroundColor: '#10B981',
    paddingVertical: 18,
    borderRadius: 14,
    alignItems: 'center',
    marginTop: 10,
  },
  callButtonText: {
    color: '#FFFFFF',
    fontSize: 19,
    fontWeight: '900',
  },
  backButton: {
    backgroundColor: '#334155',
    paddingVertical: 16,
    borderRadius: 14,
    alignItems: 'center',
    marginBottom: 24,
  },
  backButtonText: {
    color: '#E2E8F0',
    fontSize: 17,
    fontWeight: '700',
  },
});
