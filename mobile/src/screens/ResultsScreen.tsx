import React, { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Linking,
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
import { formatBenefitsHindi, translateSchemeName } from './SchemeDetailScreen';

export interface SchemeItem {
  id: number;
  name: string;
  category?: string;
  government_name?: string;
  verdict?: 'QUALIFIES' | 'NEEDS_MORE_INFO' | 'DOES_NOT_QUALIFY';
  reason?: string;
  disqualification_reasons?: string[];
  missing_fields?: string[];
  benefits?: string | any;
  required_documents?: string[] | any;
  application_process?: string | any;
  source_url?: string;
  description?: string;
  application_url?: string;
}

interface ResultsScreenProps {
  conversationId: string;
  schemes: SchemeItem[];
  spokenText: string;
  audioBase64?: string;
  citizenProfile?: Record<string, any>;
  onSelectScheme?: (scheme: SchemeItem) => void;
  onViewReport?: () => void;
  onStartNewConversation: () => void;
}

// -----------------------------------------------------------------------------
// HINDI FORMATTING HELPERS FOR RURAL & LOW-LITERACY CITIZENS
// -----------------------------------------------------------------------------

const translateCategory = (cat?: string): string => {
  if (!cat) return 'सामान्य जनकल्याण';
  const c = cat.toLowerCase();
  if (c.includes('health') || c.includes('wellness') || c.includes('divyang')) {
    return '🏥 स्वास्थ्य एवं दिव्यांग सहायता';
  }
  if (c.includes('women') || c.includes('child')) {
    return '👩 महिला एवं बाल कल्याण';
  }
  if (c.includes('labour') || c.includes('worker') || c.includes('employment')) {
    return '🔨 मजदूर एवं श्रमिक कल्याण';
  }
  if (c.includes('agri') || c.includes('rural') || c.includes('farmer') || c.includes('crop') || c.includes('pashu')) {
    return '🌾 किसान एवं पशुपालक कल्याण';
  }
  if (c.includes('social') || c.includes('pension') || c.includes('empowerment')) {
    return '🤝 सामाजिक सुरक्षा एवं पेंशन';
  }
  if (c.includes('housing') || c.includes('awas')) {
    return '🏠 आवास एवं पक्का घर योजना';
  }
  if (c.includes('education') || c.includes('daksh')) {
    return '📚 शिक्षा एवं कौशल विकास';
  }
  return `📁 ${cat}`;
};

const translateGov = (gov?: string): string => {
  if (!gov) return '🏛️ उत्तर प्रदेश सरकार';
  const g = gov.toLowerCase();
  if (g.includes('uttar pradesh')) return '🏛️ उत्तर प्रदेश सरकार';
  if (g.includes('central') || g.includes('india')) return '🏛️ भारत सरकार (केंद्र)';
  return `🏛️ ${gov}`;
};

const cleanRawBenefitText = (text: string): string => {
  return text
    .replace(/[{}"]/g, '')
    .replace(/\\n/g, '\n')
    .replace(/\*\*/g, '')
    .replace(/>/g, '')
    .replace(/Benefits?:?/gi, '')
    .replace(/Monthly pension Rs\.?\s*(\d+)\/?-?/gi, 'हर महीने ₹$1 की पेंशन सीधे बैंक खाते में')
    .replace(/Financial Assistance\s*:?\s*₹?(\d+)\/?-?\s*per month/gi, 'प्रति माह ₹$1 की आर्थिक सहायता')
    .trim();
};

const formatApplicationProcessHindi = (proc: any): { mode: string; steps: string[]; url?: string } => {
  let modeStr = 'ऑनलाइन (जन सेवा केंद्र / CSC या कंप्यूटर द्वारा)';
  let steps: string[] = [
    'अपने आधार कार्ड और बैंक पासबुक के साथ नजदीकी जन सेवा केंद्र (CSC) या ब्लॉक कार्यालय जाएं।',
    'पोर्टल पर ऑनलाइन आवेदन पत्र भरवाएं और ज़रूरी दस्तावेज़ स्कैन करवाएं।',
    'जमा करने के बाद रसीद (पावती) सुरक्षित रखें ताकि योजना का पैसा बैंक खाते में आ सके।',
  ];
  let url = '';

  if (typeof proc === 'string') {
    if (proc.trim().startsWith('{')) {
      try { proc = JSON.parse(proc); } catch (_e) {}
    }
  }

  if (typeof proc === 'object' && proc !== null) {
    if (proc.mode) {
      modeStr = proc.mode.toLowerCase().includes('online')
        ? 'ऑनलाइन (जन सेवा केंद्र / CSC या कंप्यूटर द्वारा)'
        : 'ऑफलाइन (ब्लॉक / तहसील कार्यालय में फॉर्म जमा करके)';
    }
    if (proc.url) url = proc.url;
    if (proc.steps && Array.isArray(proc.steps) && proc.steps.length > 0) {
      steps = proc.steps.map((s: any) => String(s));
    }
  } else if (typeof proc === 'string') {
    if (proc.toLowerCase().includes('online')) {
      modeStr = 'ऑनलाइन (जन सेवा केंद्र / CSC या कंप्यूटर द्वारा)';
    } else if (proc.toLowerCase().includes('offline')) {
      modeStr = 'ऑफलाइन (ब्लॉक / तहसील कार्यालय में)';
    }
    const urlMatch = proc.match(/https?:\/\/[^\s]+/);
    if (urlMatch) url = urlMatch[0];
  }

  return { mode: modeStr, steps, url };
};

const formatDocumentsHindi = (docs: any): string[] => {
  if (!docs) return ['आधार कार्ड (Aadhaar Card)', 'बैंक खाता पासबुक'];
  let list: any[] = [];
  if (Array.isArray(docs)) {
    list = docs;
  } else if (typeof docs === 'string') {
    if (docs.trim().startsWith('[')) {
      try { list = JSON.parse(docs); } catch (_e) { list = docs.split(','); }
    } else {
      list = docs.split(',');
    }
  }

  return list.map((item) => {
    let docName = typeof item === 'object' && item !== null ? (item.purpose || item.accepts?.[0] || JSON.stringify(item)) : String(item);
    const dLower = docName.toLowerCase();
    if (dLower.includes('aadhaar')) return 'आधार कार्ड (Aadhaar Card)';
    if (dLower.includes('disability') || dLower.includes('divyang')) return 'दिव्यांगता प्रमाण पत्र (Disability Certificate)';
    if (dLower.includes('income')) return 'आय प्रमाण पत्र (Income Certificate)';
    if (dLower.includes('ration') || dLower.includes('bpl')) return 'राशन कार्ड (Ration Card)';
    if (dLower.includes('bank') || dLower.includes('passbook')) return 'बैंक खाता पासबुक (Bank Passbook)';
    if (dLower.includes('death') || dLower.includes('husband')) return 'पति का मृत्यु प्रमाण पत्र (Death Certificate)';
    if (dLower.includes('khasra') || dLower.includes('khatauni') || dLower.includes('land')) return 'खसरा / खतौनी (जमीन का पर्चा)';
    if (dLower.includes('caste')) return 'जाति प्रमाण पत्र (Caste Certificate)';
    if (dLower.includes('age') || dLower.includes('birth')) return 'आयु / जन्म प्रमाण पत्र';
    return docName.replace(/[{}"]/g, '').trim();
  });
};

export const ResultsScreen: React.FC<ResultsScreenProps> = ({
  schemes,
  spokenText,
  audioBase64,
  onSelectScheme,
  onViewReport,
  onStartNewConversation,
}) => {
  const [isPlayingAudio, setIsPlayingAudio] = useState<boolean>(false);
  const [expandedSchemeId, setExpandedSchemeId] = useState<number | null>(
    schemes.length > 0 ? schemes[0].id : null
  );
  const [playingSchemeId, setPlayingSchemeId] = useState<number | null>(null);
  const [loadingSchemeAudioId, setLoadingSchemeAudioId] = useState<number | null>(null);

  // Play spoken announcement automatically on mount (or fetch on demand from /tts)
  useEffect(() => {
    let isMounted = true;
    let timer: any = null;

    const autoPlayAnnouncement = async () => {
      try {
        if (audioBase64) {
          if (isMounted) setIsPlayingAudio(true);
          await playTTSAudio(audioBase64);
        } else {
          // Fetch audio from /tts if not pre-provided
          const textToSpeak = spokenText || 'आपकी पात्रता के अनुकूल सरकारी योजनाएं नीचे दी गई हैं।';
          const res = await fetch(API_ENDPOINTS.tts, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              text: textToSpeak,
              return_format: 'base64',
              language_code: 'hi',
            }),
          });
          if (res.ok && isMounted) {
            const data = await res.json();
            if (data?.audio_base64 && isMounted) {
              if (isMounted) setIsPlayingAudio(true);
              await playTTSAudio(data.audio_base64);
            }
          }
        }
      } catch (_err) {
      } finally {
        if (isMounted) setIsPlayingAudio(false);
      }
    };

    timer = setTimeout(() => {
      autoPlayAnnouncement();
    }, 350);

    return () => {
      isMounted = false;
      if (timer) clearTimeout(timer);
      stopTTSAudio();
    };
  }, [audioBase64, spokenText]);

  const toggleExpand = (id: number) => {
    setExpandedSchemeId(expandedSchemeId === id ? null : id);
  };

  const replayMainAudio = async () => {
    if (isPlayingAudio) {
      await stopTTSAudio();
      setIsPlayingAudio(false);
      return;
    }

    if (audioBase64) {
      setIsPlayingAudio(true);
      await playTTSAudio(audioBase64);
      setIsPlayingAudio(false);
    } else {
      // Fetch audio on demand from backend /tts
      try {
        setIsPlayingAudio(true);
        const textToSpeak = spokenText || 'आपकी पात्रता के अनुकूल सरकारी योजनाएं नीचे दी गई हैं।';
        const res = await fetch(API_ENDPOINTS.tts, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            text: textToSpeak,
            return_format: 'base64',
            language_code: 'hi',
          }),
        });
        if (res.ok) {
          const data = await res.json();
          if (data.audio_base64) {
            await playTTSAudio(data.audio_base64);
          }
        }
      } catch (_e) {
      } finally {
        setIsPlayingAudio(false);
      }
    }
  };

  const playSchemeAudio = async (scheme: SchemeItem) => {
    if (playingSchemeId === scheme.id) {
      await stopTTSAudio();
      setPlayingSchemeId(null);
      return;
    }

    await stopTTSAudio();
    setIsPlayingAudio(false);
    setLoadingSchemeAudioId(scheme.id);

    try {
      const vText = scheme.verdict === 'QUALIFIES'
        ? 'आप इस योजना के लिए पात्र हैं।'
        : scheme.verdict === 'DOES_NOT_QUALIFY'
        ? 'आप इस योजना के लिए अपात्र हैं, क्योंकि इसके नियम पूरे नहीं हैं।'
        : 'इस योजना के लिए दस्तावेज़ सत्यापन आवश्यक है।';

      const shortBenefit = formatBenefitsHindi(scheme.benefits, scheme.name);
      const hindiTitle = translateSchemeName(scheme.name);
      const textToSpeak = `${hindiTitle}। ${vText} लाभ: ${shortBenefit.split('\n')[0]}`;

      const res = await fetch(API_ENDPOINTS.tts, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: textToSpeak,
          return_format: 'base64',
          language_code: 'hi',
        }),
      });

      if (res.ok) {
        const data = await res.json();
        if (data.audio_base64) {
          setLoadingSchemeAudioId(null);
          setPlayingSchemeId(scheme.id);
          await playTTSAudio(data.audio_base64);
        }
      }
    } catch (_e) {
    } finally {
      setLoadingSchemeAudioId(null);
      setPlayingSchemeId(null);
    }
  };

  const getVerdictBadge = (verdict?: string) => {
    switch (verdict) {
      case 'QUALIFIES':
        return {
          label: '✓ आप पात्र हैं (यह योजना मिलेगी)',
          badgeStyle: styles.badgeQualifies,
          textStyle: styles.badgeTextQualifies,
          cardStyle: styles.cardQualifies,
          explanation: '✓ आप इस योजना के सभी निर्धारित नियमों को पूरा करते हैं।',
        };
      case 'NEEDS_MORE_INFO':
        return {
          label: '⏳ दस्तावेज़ सत्यापन आवश्यक',
          badgeStyle: styles.badgeNeedsInfo,
          textStyle: styles.badgeTextNeedsInfo,
          cardStyle: styles.cardNeedsInfo,
          explanation: '⏳ इस योजना के लिए अतिरिक्त सरकारी कागज़ात की जाँच आवश्यक है।',
        };
      case 'DOES_NOT_QUALIFY':
      default:
        return {
          label: '✕ अपात्र (यह योजना नहीं मिल सकती)',
          badgeStyle: styles.badgeDisqualified,
          textStyle: styles.badgeTextDisqualified,
          cardStyle: styles.cardDisqualified,
          explanation: '✕ नियमों के अनुसार आप इस योजना की आवश्यक शर्तें पूरी नहीं करते हैं।',
        };
    }
  };

  const qualifiedCount = schemes.filter((s) => s.verdict === 'QUALIFIES').length;

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" />

      {/* Top Tricolor Accent Bar */}
      <View style={styles.topAccentBar}>
        <View style={[styles.tricolorSegment, { backgroundColor: '#FF9933' }]} />
        <View style={[styles.tricolorSegment, { backgroundColor: '#FFFFFF' }]} />
        <View style={[styles.tricolorSegment, { backgroundColor: '#138808' }]} />
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.titleHindi}>सरकारी योजनाएं (जाँच परिणाम)</Text>
          <Text style={styles.titleSubHindi}>
            {qualifiedCount > 0
              ? `बधाई हो! आप नीचे दी गई ${qualifiedCount} योजनाओं के लिए पात्र हैं:`
              : 'आपकी पात्रता की स्थिति नीचे दी गई है:'}
          </Text>
        </View>

        {/* Spoken Audio Summary Card */}
        <View style={styles.audioSummaryCard}>
          <View style={styles.audioSummaryHeader}>
            <Text style={styles.audioIcon}>{isPlayingAudio ? '🔊' : '🔈'}</Text>
            <View style={styles.audioHeaderText}>
              <Text style={styles.audioLabel}>
                {isPlayingAudio ? '🔊 योजनावाणी बोल रही है...' : '🔊 आवाज़ में सुनें (Voice Summary)'}
              </Text>
              <Text style={styles.spokenSnippet}>
                {spokenText || 'आपकी पात्रता के अनुकूल योजनाओं की सूची नीचे तैयार है।'}
              </Text>
            </View>
          </View>
          <TouchableOpacity
            style={[styles.replayButton, isPlayingAudio && styles.replayButtonActive]}
            onPress={replayMainAudio}
            accessibilityRole="button"
            accessibilityLabel="दोबारा सुनें"
          >
            <Text style={styles.replayButtonText}>
              {isPlayingAudio ? '⏹️ बोलना बंद करें' : '🔁 आवाज़ में दोबारा सुनें'}
            </Text>
          </TouchableOpacity>
        </View>

        {/* View Profile Report Banner Button */}
        {onViewReport && (
          <TouchableOpacity
            style={styles.viewProfileReportCard}
            onPress={onViewReport}
            activeOpacity={0.8}
            accessibilityRole="button"
          >
            <View style={styles.viewProfileReportLeft}>
              <Text style={styles.viewProfileReportIcon}>📋</Text>
              <View style={{ flex: 1 }}>
                <Text style={styles.viewProfileReportTitle}>नागरिक संपूर्ण व्यक्तिगत विवरण रिपोर्ट</Text>
                <Text style={styles.viewProfileReportSub}>सत्यापित व्यक्तिगत विवरण, OCR कागज़ात व सारांश देखें</Text>
              </View>
            </View>
            <Text style={styles.viewProfileReportArrow}>➔</Text>
          </TouchableOpacity>
        )}

        {/* Schemes Section Header */}
        <View style={styles.sectionHeaderRow}>
          <Text style={styles.listHeader}>
            उपलब्ध योजनाएं ({schemes.length})
          </Text>
          {qualifiedCount > 0 && (
            <View style={styles.qualCountPill}>
              <Text style={styles.qualCountPillText}>✓ {qualifiedCount} में आप पात्र हैं</Text>
            </View>
          )}
        </View>

        {schemes.length === 0 ? (
          <View style={styles.emptyCard}>
            <Text style={styles.emptyTitle}>कोई योजना नहीं मिली</Text>
            <Text style={styles.emptyText}>
              आपकी जानकारी के आधार पर अभी कोई उपयुक्त योजना नहीं मिली। कृपया अपने नजदीकी कॉमन सर्विस सेंटर (CSC) पर जाकर मदद लें।
            </Text>
          </View>
        ) : (
          schemes.map((scheme, index) => {
            const badge = getVerdictBadge(scheme.verdict);
            const isExpanded = expandedSchemeId === scheme.id;
            const isAudioPlayingThis = playingSchemeId === scheme.id;
            const isLoadingAudioThis = loadingSchemeAudioId === scheme.id;
            const benefitsText = formatBenefitsHindi(scheme.benefits, scheme.name);
            const procInfo = formatApplicationProcessHindi(scheme.application_process);
            const docList = formatDocumentsHindi(scheme.required_documents);

            return (
              <TouchableOpacity
                key={scheme.id || index}
                style={[styles.schemeCard, badge.cardStyle]}
                activeOpacity={0.92}
                onPress={() => (onSelectScheme ? onSelectScheme(scheme) : toggleExpand(scheme.id))}
                accessibilityRole="button"
                accessibilityLabel={`${scheme.name} का संपूर्ण विवरण खोलें`}
              >
                {/* Top Row: Index + Verdict Badge */}
                <View style={styles.cardTopRow}>
                  <Text style={styles.schemeIndex}>#{index + 1}</Text>
                  <View style={[styles.verdictBadge, badge.badgeStyle]}>
                    <Text style={[styles.verdictBadgeText, badge.textStyle]}>
                      {badge.label}
                    </Text>
                  </View>
                </View>

                {/* Scheme Title */}
                <Text style={styles.schemeName}>{translateSchemeName(scheme.name)}</Text>

                {/* Category & Government Tag */}
                <View style={styles.metaRow}>
                  <Text style={styles.metaCategory}>{translateCategory(scheme.category)}</Text>
                  <Text style={styles.metaGov}>{translateGov(scheme.government_name)}</Text>
                </View>

                {/* Verdict Explanation Box */}
                <View
                  style={[
                    styles.reasonBox,
                    scheme.verdict === 'QUALIFIES'
                      ? styles.reasonBoxQualifies
                      : scheme.verdict === 'DOES_NOT_QUALIFY'
                      ? styles.reasonBoxDisqualified
                      : styles.reasonBoxDefault,
                  ]}
                >
                  <Text
                    style={[
                      styles.reasonText,
                      scheme.verdict === 'DOES_NOT_QUALIFY' && styles.reasonTextDisqualified,
                    ]}
                  >
                    {scheme.verdict === 'DOES_NOT_QUALIFY'
                      ? `🚫 अपात्रता: ${scheme.reason || badge.explanation}`
                      : scheme.reason || badge.explanation}
                  </Text>
                </View>

                {/* Open Full Elaborate Scheme Details Screen Button (MANDATORY FUNCTIONALITY) */}
                {onSelectScheme && (
                  <TouchableOpacity
                    style={styles.openDetailsScreenBtn}
                    onPress={() => onSelectScheme(scheme)}
                    activeOpacity={0.8}
                  >
                    <Text style={styles.openDetailsScreenBtnText}>
                      📖 संपूर्ण विवरण, आवाज़ व दस्तावेज़ देखें ➔
                    </Text>
                  </TouchableOpacity>
                )}

                {/* Listen To This Scheme Button */}
                <TouchableOpacity
                  style={[styles.schemeAudioButton, isAudioPlayingThis && styles.schemeAudioButtonActive]}
                  onPress={() => playSchemeAudio(scheme)}
                  disabled={isLoadingAudioThis}
                >
                  {isLoadingAudioThis ? (
                    <ActivityIndicator size="small" color="#FF9933" />
                  ) : (
                    <Text style={styles.schemeAudioButtonText}>
                      {isAudioPlayingThis ? '⏹️ आवाज़ बंद करें' : '🔊 इस योजना के बारे में सुनें'}
                    </Text>
                  )}
                </TouchableOpacity>

                {/* Expand / Collapse Button */}
                <TouchableOpacity
                  style={styles.expandButton}
                  onPress={() => toggleExpand(scheme.id)}
                  activeOpacity={0.7}
                >
                  <Text style={styles.expandButtonText}>
                    {isExpanded ? '▲ कम विवरण देखें (छुपाएं)' : '▼ लाभ और आवेदन का तरीका देखें'}
                  </Text>
                </TouchableOpacity>

                {/* Expanded Details Section */}
                {isExpanded && (
                  <View style={styles.expandedSection}>
                    {/* Disqualification Reasons in Expanded View */}
                    {scheme.verdict === 'DOES_NOT_QUALIFY' && (
                      <View style={styles.detailBlock}>
                        <Text style={[styles.detailTitle, { color: '#EF4444' }]}>
                          ⚠️ अपात्रता के मुख्य कारण (Missing Criteria):
                        </Text>
                        <View style={styles.disqualifiedExpandedBox}>
                          {(scheme.disqualification_reasons && scheme.disqualification_reasons.length > 0
                            ? scheme.disqualification_reasons
                            : [scheme.reason || 'पात्रता की आवश्यक शर्तें पूरी नहीं हुईं।']
                          ).map((dReason, dIdx) => (
                            <View key={dIdx} style={styles.disqualifiedReasonRow}>
                              <Text style={styles.disqualifiedReasonCross}>✕</Text>
                              <Text style={styles.disqualifiedReasonText}>{dReason}</Text>
                            </View>
                          ))}
                        </View>
                      </View>
                    )}

                    {/* Benefits Section */}
                    <View style={styles.detailBlock}>
                      <Text style={styles.detailTitle}>💰 आर्थिक लाभ व सहायता:</Text>
                      <View style={styles.benefitContainer}>
                        <Text style={styles.benefitText}>{benefitsText}</Text>
                      </View>
                    </View>

                    {/* Application Process Section */}
                    <View style={styles.detailBlock}>
                      <Text style={styles.detailTitle}>📝 आवेदन कैसे करें:</Text>
                      <View style={styles.processContainer}>
                        <Text style={styles.processModeText}>{procInfo.mode}</Text>
                        {procInfo.steps.map((st, sIdx) => (
                          <View key={sIdx} style={styles.stepRow}>
                            <Text style={styles.stepBullet}>•</Text>
                            <Text style={styles.stepText}>{st}</Text>
                          </View>
                        ))}
                        {procInfo.url ? (
                          <TouchableOpacity
                            style={styles.portalLinkButton}
                            onPress={() => Linking.openURL(procInfo.url!).catch(() => {})}
                          >
                            <Text style={styles.portalLinkText}>🌐 आधिकारिक सरकारी पोर्टल खोलें</Text>
                          </TouchableOpacity>
                        ) : null}
                      </View>
                    </View>

                    {/* Required Documents Section */}
                    {docList.length > 0 && (
                      <View style={styles.detailBlock}>
                        <Text style={styles.detailTitle}>📄 ज़रूरी कागज़ात (दस्तावेज़):</Text>
                        <View style={styles.docContainer}>
                          {docList.map((doc, dIdx) => (
                            <View key={dIdx} style={styles.docItemRow}>
                              <Text style={styles.docIcon}>✓</Text>
                              <Text style={styles.docText}>{doc}</Text>
                            </View>
                          ))}
                        </View>
                      </View>
                    )}
                  </View>
                )}
              </TouchableOpacity>
            );
          })
        )}

        {/* Start New Search Button */}
        <TouchableOpacity
          style={styles.newSearchButton}
          onPress={onStartNewConversation}
          accessibilityRole="button"
        >
          <Text style={styles.newSearchButtonText}>🔄 नई बातचीत शुरू करें (Start Over)</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
};

// -----------------------------------------------------------------------------
// HIGH-ACCESSIBILITY STYLES FOR RURAL USERS
// -----------------------------------------------------------------------------

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0A141E',
  },
  topAccentBar: {
    flexDirection: 'row',
    height: 4,
    width: '100%',
  },
  tricolorSegment: {
    flex: 1,
    height: '100%',
  },
  scrollContent: {
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 40,
  },
  header: {
    marginBottom: 14,
  },
  titleHindi: {
    fontSize: 22,
    fontWeight: '800',
    color: '#FFFFFF',
    letterSpacing: 0.3,
  },
  titleSubHindi: {
    fontSize: 16,
    color: '#81C784',
    marginTop: 4,
    fontWeight: '600',
  },

  // Audio Summary Card
  audioSummaryCard: {
    backgroundColor: '#13283E',
    borderRadius: 14,
    padding: 16,
    borderWidth: 1.5,
    borderColor: '#1E88E5',
    marginBottom: 16,
  },
  audioSummaryHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  audioIcon: {
    fontSize: 28,
    marginRight: 12,
    marginTop: 2,
  },
  audioHeaderText: {
    flex: 1,
  },
  audioLabel: {
    fontSize: 15,
    fontWeight: '700',
    color: '#64B5F6',
    marginBottom: 4,
  },
  spokenSnippet: {
    fontSize: 17,
    fontWeight: '600',
    color: '#E0E0E0',
    lineHeight: 24,
  },
  viewProfileReportCard: {
    backgroundColor: '#102A45',
    borderRadius: 12,
    padding: 14,
    marginBottom: 16,
    borderWidth: 1.5,
    borderColor: '#42A5F5',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  viewProfileReportLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    marginRight: 10,
  },
  viewProfileReportIcon: {
    fontSize: 26,
    marginRight: 12,
  },
  viewProfileReportTitle: {
    fontSize: 15,
    fontWeight: '800',
    color: '#90CAF9',
    marginBottom: 2,
  },
  viewProfileReportSub: {
    fontSize: 12,
    color: '#CFD8DC',
  },
  viewProfileReportArrow: {
    fontSize: 20,
    color: '#90CAF9',
    fontWeight: '800',
  },
  openDetailsScreenBtn: {
    backgroundColor: '#0D47A1',
    borderRadius: 8,
    paddingVertical: 10,
    paddingHorizontal: 12,
    alignItems: 'center',
    marginTop: 8,
    marginBottom: 4,
  },
  openDetailsScreenBtnText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '800',
  },
  replayButton: {
    backgroundColor: '#1E3A5F',
    borderRadius: 10,
    paddingVertical: 10,
    paddingHorizontal: 16,
    alignItems: 'center',
    marginTop: 12,
    borderWidth: 1,
    borderColor: '#42A5F5',
  },
  replayButtonActive: {
    backgroundColor: '#B71C1C',
    borderColor: '#EF5350',
  },
  replayButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },

  // Section Header
  sectionHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  listHeader: {
    fontSize: 19,
    fontWeight: '800',
    color: '#FFFFFF',
  },
  qualCountPill: {
    backgroundColor: '#1B5E20',
    paddingVertical: 4,
    paddingHorizontal: 10,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#4CAF50',
  },
  qualCountPillText: {
    color: '#A5D6A7',
    fontSize: 13,
    fontWeight: '700',
  },

  // Scheme Cards
  schemeCard: {
    backgroundColor: '#102030',
    borderRadius: 14,
    padding: 16,
    marginBottom: 14,
    borderWidth: 2,
  },
  cardQualifies: {
    borderColor: '#2E7D32',
    backgroundColor: '#0F2417',
  },
  cardNeedsInfo: {
    borderColor: '#F57C00',
    backgroundColor: '#1F1B12',
  },
  cardDisqualified: {
    borderColor: '#455A64',
    backgroundColor: '#131B22',
  },

  cardTopRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  schemeIndex: {
    fontSize: 16,
    fontWeight: '700',
    color: '#90CAF9',
  },
  verdictBadge: {
    paddingVertical: 4,
    paddingHorizontal: 10,
    borderRadius: 8,
  },
  verdictBadgeText: {
    fontSize: 14,
    fontWeight: '800',
  },
  badgeQualifies: {
    backgroundColor: '#1B5E20',
    borderWidth: 1,
    borderColor: '#4CAF50',
  },
  badgeTextQualifies: {
    color: '#A5D6A7',
    fontSize: 14,
    fontWeight: '800',
  },
  badgeNeedsInfo: {
    backgroundColor: '#E65100',
    borderWidth: 1,
    borderColor: '#FFB74D',
  },
  badgeTextNeedsInfo: {
    color: '#FFE082',
    fontSize: 14,
    fontWeight: '800',
  },
  badgeDisqualified: {
    backgroundColor: '#7F1D1D',
    borderWidth: 1.5,
    borderColor: '#EF4444',
  },
  badgeTextDisqualified: {
    color: '#FEE2E2',
    fontSize: 14,
    fontWeight: '800',
  },

  schemeName: {
    fontSize: 19,
    fontWeight: '800',
    color: '#FFFFFF',
    marginBottom: 6,
    lineHeight: 25,
  },
  metaRow: {
    flexDirection: 'column',
    marginBottom: 8,
    gap: 2,
  },
  metaCategory: {
    fontSize: 14,
    color: '#FFB74D',
    fontWeight: '600',
  },
  metaGov: {
    fontSize: 14,
    color: '#90A4AE',
    fontWeight: '500',
  },

  // Reason Box
  reasonBox: {
    padding: 10,
    borderRadius: 8,
    marginVertical: 6,
  },
  reasonBoxQualifies: {
    backgroundColor: '#163820',
    borderLeftWidth: 3,
    borderLeftColor: '#4CAF50',
  },
  reasonBoxDefault: {
    backgroundColor: '#1C2938',
    borderLeftWidth: 3,
    borderLeftColor: '#78909C',
  },
  reasonBoxDisqualified: {
    backgroundColor: '#3E161B',
    borderLeftWidth: 3.5,
    borderLeftColor: '#EF4444',
  },
  reasonText: {
    fontSize: 15,
    color: '#ECEFF1',
    fontWeight: '500',
    lineHeight: 22,
  },
  reasonTextDisqualified: {
    color: '#FFCDD2',
    fontWeight: '600',
  },
  disqualifiedExpandedBox: {
    backgroundColor: '#381216',
    borderRadius: 8,
    padding: 10,
    borderWidth: 1,
    borderColor: '#7F1D1D',
    gap: 8,
  },
  disqualifiedReasonRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  disqualifiedReasonCross: {
    color: '#EF4444',
    fontSize: 14,
    fontWeight: '900',
    marginRight: 8,
    marginTop: 2,
  },
  disqualifiedReasonText: {
    flex: 1,
    fontSize: 14,
    color: '#FFE4E6',
    lineHeight: 20,
    fontWeight: '500',
  },

  // Scheme-level audio button
  schemeAudioButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#1C3146',
    borderRadius: 8,
    paddingVertical: 8,
    paddingHorizontal: 12,
    marginTop: 6,
    borderWidth: 1,
    borderColor: '#37474F',
  },
  schemeAudioButtonActive: {
    backgroundColor: '#B71C1C',
    borderColor: '#EF5350',
  },
  schemeAudioButtonText: {
    color: '#FFB74D',
    fontSize: 15,
    fontWeight: '700',
  },

  // Expand Button
  expandButton: {
    alignItems: 'center',
    paddingVertical: 10,
    marginTop: 8,
    backgroundColor: '#172B3F',
    borderRadius: 8,
  },
  expandButtonText: {
    fontSize: 15,
    fontWeight: '700',
    color: '#FF9933',
  },

  // Expanded Section
  expandedSection: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#26384A',
  },
  detailBlock: {
    marginBottom: 14,
  },
  detailTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFD54F',
    marginBottom: 6,
  },
  benefitContainer: {
    backgroundColor: '#162736',
    padding: 12,
    borderRadius: 8,
    borderLeftWidth: 3,
    borderLeftColor: '#FFD54F',
  },
  benefitText: {
    fontSize: 16,
    color: '#E0E0E0',
    lineHeight: 24,
    fontWeight: '500',
  },
  processContainer: {
    backgroundColor: '#162736',
    padding: 12,
    borderRadius: 8,
  },
  processModeText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#64B5F6',
    marginBottom: 6,
  },
  stepRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 4,
  },
  stepBullet: {
    fontSize: 16,
    color: '#FF9933',
    marginRight: 6,
  },
  stepText: {
    fontSize: 15,
    color: '#CFD8DC',
    flex: 1,
    lineHeight: 22,
  },
  portalLinkButton: {
    marginTop: 8,
    backgroundColor: '#1E3A5F',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 6,
    alignItems: 'center',
  },
  portalLinkText: {
    color: '#64B5F6',
    fontSize: 14,
    fontWeight: '700',
  },
  docContainer: {
    backgroundColor: '#162736',
    padding: 12,
    borderRadius: 8,
  },
  docItemRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
  },
  docIcon: {
    color: '#4CAF50',
    fontSize: 15,
    fontWeight: '800',
    marginRight: 8,
  },
  docText: {
    fontSize: 15,
    color: '#ECEFF1',
    fontWeight: '500',
  },

  // Empty State
  emptyCard: {
    backgroundColor: '#13283E',
    padding: 24,
    borderRadius: 14,
    alignItems: 'center',
    marginVertical: 16,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 15,
    color: '#B0BEC5',
    textAlign: 'center',
    lineHeight: 22,
  },

  // New Search Button
  newSearchButton: {
    backgroundColor: '#FF9933',
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: 'center',
    marginTop: 8,
  },
  newSearchButtonText: {
    color: '#0A141E',
    fontSize: 17,
    fontWeight: '800',
  },
});
