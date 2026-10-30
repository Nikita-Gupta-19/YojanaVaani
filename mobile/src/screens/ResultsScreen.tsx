import React, { useState } from 'react';
import {
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

export interface SchemeItem {
  id: number;
  name: string;
  category?: string;
  government_name?: string;
  verdict?: 'QUALIFIES' | 'NEEDS_MORE_INFO' | 'DOES_NOT_QUALIFY';
  reason?: string;
  benefits?: string | any;
  required_documents?: string[];
  application_process?: string | any;
  source_url?: string;
}

interface ResultsScreenProps {
  conversationId: string;
  schemes: SchemeItem[];
  spokenText: string;
  onStartNewConversation: () => void;
}

export const ResultsScreen: React.FC<ResultsScreenProps> = ({
  schemes,
  spokenText,
  onStartNewConversation,
}) => {
  const [isPlayingAudio, setIsPlayingAudio] = useState<boolean>(true);
  const [expandedSchemeId, setExpandedSchemeId] = useState<number | null>(null);

  const toggleExpand = (id: number) => {
    setExpandedSchemeId(expandedSchemeId === id ? null : id);
  };

  const replayAudio = () => {
    setIsPlayingAudio(true);
    setTimeout(() => {
      setIsPlayingAudio(false);
    }, 2500);
  };

  const getVerdictBadge = (verdict?: string) => {
    switch (verdict) {
      case 'QUALIFIES':
        return {
          label: '✓ आप पात्र हैं (यह योजना मिलेगी)',
          badgeStyle: styles.badgeQualifies,
          textStyle: styles.badgeTextQualifies,
          cardStyle: styles.cardQualifies,
        };
      case 'NEEDS_MORE_INFO':
        return {
          label: '⏳ थोड़ी और जानकारी चाहिए',
          badgeStyle: styles.badgeNeedsInfo,
          textStyle: styles.badgeTextNeedsInfo,
          cardStyle: styles.cardNeedsInfo,
        };
      default:
        return {
          label: '✕ यह योजना नहीं मिल सकती',
          badgeStyle: styles.badgeDisqualified,
          textStyle: styles.badgeTextDisqualified,
          cardStyle: styles.cardDisqualified,
        };
    }
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
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.titleHindi}>आपके लिए सरकारी योजनाएं</Text>
          <Text style={styles.titleEnglish}>Matched Government Welfare Schemes</Text>
        </View>

        {/* Spoken Audio Summary Card */}
        <View style={styles.audioSummaryCard}>
          <View style={styles.audioSummaryHeader}>
            <Text style={styles.audioIcon}>{isPlayingAudio ? '🔊' : '🔈'}</Text>
            <View style={styles.audioHeaderText}>
              <Text style={styles.audioLabel}>
                {isPlayingAudio ? '🔊 योजनावाणी बोल रही है...' : '🔊 आवाज़ में सुनें'}
              </Text>
              <Text style={styles.spokenSnippet}>
                {spokenText || 'आपके लिए सही योजनाओं की सूची नीचे दी गई है।'}
              </Text>
            </View>
          </View>
          <TouchableOpacity style={styles.replayButton} onPress={replayAudio}>
            <Text style={styles.replayButtonText}>🔁 दोबारा सुनें</Text>
          </TouchableOpacity>
        </View>

        {/* Schemes List Header */}
        <Text style={styles.listHeader}>
          आपके लिए योजनाएं ({schemes.length})
        </Text>

        {schemes.length === 0 ? (
          <View style={styles.emptyCard}>
            <Text style={styles.emptyText}>
              आपके लिए अभी कोई योजना नहीं मिली। कृपया अपने पास के ग्राहक सेवा केंद्र (CSC) पर जाएं।
            </Text>
          </View>
        ) : (
          schemes.map((scheme, index) => {
            const badge = getVerdictBadge(scheme.verdict);
            const isExpanded = expandedSchemeId === scheme.id;

            return (
              <View key={scheme.id || index} style={[styles.schemeCard, badge.cardStyle]}>
                {/* Card Top Row: Index + Verdict Badge */}
                <View style={styles.cardTopRow}>
                  <Text style={styles.schemeIndex}>#{index + 1}</Text>
                  <View style={[styles.verdictBadge, badge.badgeStyle]}>
                    <Text style={[styles.verdictBadgeText, badge.textStyle]}>
                      {badge.label}
                    </Text>
                  </View>
                </View>

                {/* Scheme Name */}
                <Text style={styles.schemeName}>{scheme.name}</Text>

                {/* Category & Government Jurisdiction */}
                <View style={styles.metaRow}>
                  {scheme.category && (
                    <Text style={styles.metaCategory}>📁 {scheme.category}</Text>
                  )}
                  {scheme.government_name && (
                    <Text style={styles.metaGov}>🏛️ {scheme.government_name}</Text>
                  )}
                </View>

                {/* Reason / Verdict Justification */}
                {scheme.reason && (
                  <View style={styles.reasonBox}>
                    <Text style={styles.reasonText}>📌 {scheme.reason}</Text>
                  </View>
                )}

                {/* Expand / Collapse Details Button */}
                <TouchableOpacity
                  style={styles.expandButton}
                  onPress={() => toggleExpand(scheme.id)}
                >
                  <Text style={styles.expandButtonText}>
                    {isExpanded ? '▲ कम विवरण देखें' : '▼ लाभ और आवेदन प्रक्रिया देखें'}
                  </Text>
                </TouchableOpacity>

                {/* Expanded Details */}
                {isExpanded && (
                  <View style={styles.expandedSection}>
                    {scheme.benefits && (
                      <View style={styles.detailBlock}>
                        <Text style={styles.detailTitle}>💰 आर्थिक लाभ व सब्सिडी:</Text>
                        <Text style={styles.detailText}>
                          {typeof scheme.benefits === 'string'
                            ? scheme.benefits
                            : JSON.stringify(scheme.benefits)}
                        </Text>
                      </View>
                    )}

                    {scheme.application_process && (
                      <View style={styles.detailBlock}>
                        <Text style={styles.detailTitle}>📝 आवेदन प्रक्रिया:</Text>
                        <Text style={styles.detailText}>
                          {typeof scheme.application_process === 'string'
                            ? scheme.application_process
                            : JSON.stringify(scheme.application_process)}
                        </Text>
                      </View>
                    )}

                    {scheme.required_documents && scheme.required_documents.length > 0 && (
                      <View style={styles.detailBlock}>
                        <Text style={styles.detailTitle}>📄 आवश्यक दस्तावेज़:</Text>
                        <Text style={styles.detailText}>
                          {Array.isArray(scheme.required_documents)
                            ? scheme.required_documents.join(', ')
                            : String(scheme.required_documents)}
                        </Text>
                      </View>
                    )}
                  </View>
                )}
              </View>
            );
          })
        )}

        {/* Start New Search Button */}
        <TouchableOpacity style={styles.newSearchButton} onPress={onStartNewConversation}>
          <Text style={styles.newSearchButtonText}>🔄 नई बातचीत शुरू करें (Start Over)</Text>
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
    padding: 16,
    paddingBottom: 40,
  },
  header: {
    alignItems: 'center',
    marginVertical: 14,
  },
  titleHindi: {
    fontSize: 24,
    fontWeight: '800',
    color: '#FF9933',
    textAlign: 'center',
  },
  titleEnglish: {
    fontSize: 13,
    color: '#94A3B8',
    marginTop: 2,
    textAlign: 'center',
  },
  audioSummaryCard: {
    backgroundColor: '#1B263B',
    borderRadius: 12,
    padding: 14,
    marginBottom: 18,
    borderLeftWidth: 4,
    borderLeftColor: '#10B981',
  },
  audioSummaryHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  audioIcon: {
    fontSize: 26,
    marginRight: 10,
    marginTop: 2,
  },
  audioHeaderText: {
    flex: 1,
  },
  audioLabel: {
    color: '#10B981',
    fontSize: 13,
    fontWeight: '700',
  },
  spokenSnippet: {
    color: '#F8FAFC',
    fontSize: 14,
    lineHeight: 20,
    marginTop: 4,
  },
  replayButton: {
    marginTop: 10,
    alignSelf: 'flex-start',
    backgroundColor: '#0F172A',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  replayButtonText: {
    color: '#FF9933',
    fontSize: 12,
    fontWeight: '600',
  },
  listHeader: {
    color: '#FFFFFF',
    fontSize: 17,
    fontWeight: '700',
    marginBottom: 12,
  },
  emptyCard: {
    backgroundColor: '#1E293B',
    padding: 20,
    borderRadius: 12,
    alignItems: 'center',
  },
  emptyText: {
    color: '#94A3B8',
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 20,
  },
  schemeCard: {
    backgroundColor: '#1E293B',
    borderRadius: 14,
    padding: 16,
    marginBottom: 14,
    borderWidth: 1,
  },
  cardQualifies: {
    borderColor: '#10B981',
  },
  cardNeedsInfo: {
    borderColor: '#F59E0B',
  },
  cardDisqualified: {
    borderColor: '#475569',
    opacity: 0.85,
  },
  cardTopRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  schemeIndex: {
    color: '#64748B',
    fontSize: 16,
    fontWeight: '700',
  },
  verdictBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  verdictBadgeText: {
    fontSize: 15,
    fontWeight: '800',
  },
  badgeQualifies: {
    backgroundColor: '#064E3B',
  },
  badgeTextQualifies: {
    color: '#34D399',
    fontSize: 15,
    fontWeight: '800',
  },
  badgeNeedsInfo: {
    backgroundColor: '#78350F',
  },
  badgeTextNeedsInfo: {
    color: '#FCD34D',
    fontSize: 15,
    fontWeight: '800',
  },
  badgeDisqualified: {
    backgroundColor: '#334155',
  },
  badgeTextDisqualified: {
    color: '#CBD5E1',
    fontSize: 15,
    fontWeight: '700',
  },
  schemeName: {
    color: '#FFFFFF',
    fontSize: 22,
    fontWeight: '800',
    lineHeight: 30,
    marginBottom: 8,
  },
  metaRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 10,
  },
  metaCategory: {
    color: '#94A3B8',
    fontSize: 14,
    fontWeight: '600',
  },
  metaGov: {
    color: '#94A3B8',
    fontSize: 14,
    fontWeight: '600',
  },
  reasonBox: {
    backgroundColor: '#0F172A',
    borderRadius: 10,
    padding: 12,
    marginBottom: 12,
  },
  reasonText: {
    color: '#F1F5F9',
    fontSize: 17,
    lineHeight: 24,
  },
  expandButton: {
    paddingVertical: 10,
    alignItems: 'center',
  },
  expandButtonText: {
    color: '#FF9933',
    fontSize: 16,
    fontWeight: '700',
  },
  expandedSection: {
    marginTop: 10,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#334155',
  },
  detailBlock: {
    marginBottom: 12,
  },
  detailTitle: {
    color: '#FFD166',
    fontSize: 16,
    fontWeight: '800',
    marginBottom: 4,
  },
  detailText: {
    color: '#E2E8F0',
    fontSize: 16,
    lineHeight: 22,
  },
  newSearchButton: {
    backgroundColor: '#FF9933',
    paddingVertical: 16,
    borderRadius: 14,
    alignItems: 'center',
    marginTop: 16,
    marginBottom: 24,
  },
  newSearchButtonText: {
    color: '#0D1B2A',
    fontSize: 20,
    fontWeight: '900',
  },
});
