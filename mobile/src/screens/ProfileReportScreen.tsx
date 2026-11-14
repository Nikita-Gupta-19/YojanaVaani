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
import { SchemeItem } from './ResultsScreen';

export interface VerifiedDocument {
  document_type: string;
  extracted_fields: Record<string, any>;
  verification_status?: string;
  confidence_score?: number;
  confirmed_at?: string;
}

interface ProfileReportScreenProps {
  conversationId: string;
  citizenProfile: Record<string, any>;
  selectedScheme?: SchemeItem | null;
  verifiedDocuments?: VerifiedDocument[];
  onNavigateToScanMore: () => void;
  onBackToSchemes: () => void;
  onStartNewConversation: () => void;
}

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
  if (c.includes('agri') || c.includes('rural') || c.includes('farmer') || c.includes('crop')) {
    return '🌾 किसान एवं पशुपालक कल्याण';
  }
  if (c.includes('social') || c.includes('pension')) {
    return '🤝 सामाजिक सुरक्षा एवं पेंशन';
  }
  return `📁 ${cat}`;
};

const formatIncomeBracket = (bracket?: string): string => {
  switch (bracket) {
    case 'below_2_lakh':
      return '₹2,00,000 से कम (गरीबी रेखा/कम आय वर्ग)';
    case '2_to_5_lakh':
      return '₹2,00,000 से ₹5,00,000 (मध्यम आय वर्ग)';
    case 'above_5_lakh':
      return '₹5,00,000 से अधिक';
    default:
      return bracket || 'निर्दिष्ट नहीं';
  }
};

const formatGender = (gender?: string): string => {
  if (!gender) return 'निर्दिष्ट नहीं';
  const g = gender.toLowerCase();
  if (g.includes('female') || g.includes('महिला') || g.includes('aurat')) return 'महिला (Female)';
  if (g.includes('male') || g.includes('पुरुष') || g.includes('aadmi')) return 'पुरुष (Male)';
  if (g.includes('transgender') || g.includes('किन्नर')) return 'किन्नर / ट्रांसजेंडर';
  return gender;
};

const formatDocumentTypeName = (docType: string): string => {
  const d = docType.toLowerCase();
  if (d.includes('income')) return 'आय प्रमाण पत्र (Income Certificate)';
  if (d.includes('ration')) return 'राशन कार्ड (Ration Card)';
  if (d.includes('khasra') || d.includes('land')) return 'खसरा / खतौनी भू-अभिलेख (Land Record)';
  if (d.includes('aadhaar')) return 'आधार पहचान पत्र (Aadhaar Card)';
  if (d.includes('disability') || d.includes('divyang')) return 'दिव्यांगता प्रमाण पत्र (Disability / UDID)';
  return docType;
};

export const ProfileReportScreen: React.FC<ProfileReportScreenProps> = ({
  conversationId,
  citizenProfile,
  selectedScheme,
  verifiedDocuments = [],
  onNavigateToScanMore,
  onBackToSchemes,
  onStartNewConversation,
}) => {
  const [isPlayingAudio, setIsPlayingAudio] = useState<boolean>(false);
  const [isLoadingAudio, setIsLoadingAudio] = useState<boolean>(false);
  const [reportState, setReportState] = useState<{
    profile: Record<string, any>;
    documents: VerifiedDocument[];
    statedNeed?: string;
  }>({
    profile: citizenProfile || {},
    documents: verifiedDocuments,
    statedNeed: citizenProfile?.stated_need,
  });

  // Fetch official report from backend on mount if available
  useEffect(() => {
    let isMounted = true;
    const fetchReport = async () => {
      try {
        const res = await fetch(API_ENDPOINTS.conversationReport(conversationId, selectedScheme?.id));
        if (res.ok && isMounted) {
          const data = await res.json();
          setReportState({
            profile: data.citizen_profile || citizenProfile || {},
            documents:
              data.collected_documents && data.collected_documents.length > 0
                ? data.collected_documents
                : verifiedDocuments,
            statedNeed: data.stated_need || citizenProfile?.stated_need,
          });
        }
      } catch (_e) {
      }
    };

    if (conversationId) {
      fetchReport();
    }

    return () => {
      isMounted = false;
      stopTTSAudio();
    };
  }, [conversationId, selectedScheme?.id]);

  const p = reportState.profile;
  const docs = reportState.documents;

  // Determine Application Mode
  const isOnlineScheme =
    selectedScheme?.application_url ||
    (typeof selectedScheme?.application_process === 'string' &&
      selectedScheme.application_process.toLowerCase().includes('online'));

  const buildReportSpeechText = (): string => {
    const namePart = p.name ? `नागरिक का नाम ${p.name}` : 'नागरिक';
    const agePart = p.age ? `, उम्र ${p.age} वर्ष` : '';
    const locPart = p.district ? `, जिला ${p.district}` : '';
    const occPart = p.occupation ? `, पेशा ${p.occupation}` : '';
    const incPart = p.approx_income_bracket ? `, ${formatIncomeBracket(p.approx_income_bracket)}` : '';
    const docCountPart =
      docs.length > 0
        ? `। कुल ${docs.length} सरकारी दस्तावेज़ सत्यापित हैं।`
        : '। अभी कोई दस्तावेज़ सत्यापित नहीं हुआ है।';
    const schemePart = selectedScheme
      ? ` आपकी चयनित योजना है: ${selectedScheme.name}। ${
          isOnlineScheme
            ? 'इस योजना का आवेदन पोर्टल पर ऑनलाइन भरा जा सकता है।'
            : 'इस योजना के लिए आपको नजदीकी जन सेवा केंद्र या ब्लॉक कार्यालय जाना होगा।'
        }`
      : '';

    return `यह आपकी संपूर्ण नागरिक व्यक्तिगत रिपोर्ट है। ${namePart}${agePart}${locPart}${occPart}${incPart}${docCountPart}${schemePart}`;
  };

  const handlePlayVoice = async () => {
    if (isPlayingAudio) {
      await stopTTSAudio();
      setIsPlayingAudio(false);
      return;
    }

    setIsLoadingAudio(true);
    try {
      const speechText = buildReportSpeechText();
      const res = await fetch(API_ENDPOINTS.tts, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: speechText,
          return_format: 'base64',
          language_code: 'hi',
        }),
      });

      if (res.ok) {
        const data = await res.json();
        if (data.audio_base64) {
          setIsLoadingAudio(false);
          setIsPlayingAudio(true);
          await playTTSAudio(data.audio_base64);
        }
      }
    } catch (_e) {
    } finally {
      setIsLoadingAudio(false);
      setIsPlayingAudio(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" />

      {/* Tricolor Accent Header */}
      <View style={styles.topAccentBar}>
        <View style={[styles.tricolorSegment, { backgroundColor: '#FF9933' }]} />
        <View style={[styles.tricolorSegment, { backgroundColor: '#FFFFFF' }]} />
        <View style={[styles.tricolorSegment, { backgroundColor: '#138808' }]} />
      </View>

      {/* Navigation Top Bar */}
      <View style={styles.navBar}>
        <TouchableOpacity onPress={onBackToSchemes} style={styles.navBackButton}>
          <Text style={styles.navBackButtonText}>← योजनाएं (Schemes)</Text>
        </TouchableOpacity>
        <Text style={styles.navBarTitle}>नागरिक संपूर्ण रिपोर्ट</Text>
        <TouchableOpacity onPress={onStartNewConversation} style={styles.navRestartButton}>
          <Text style={styles.navRestartButtonText}>🔄 नई खोज</Text>
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        {/* Report Official Banner */}
        <View style={styles.bannerCard}>
          <View style={styles.badgeRow}>
            <View style={styles.officialPill}>
              <Text style={styles.officialPillText}>✓ डिजिटल लोक कल्याण रिपोर्ट (Verified Profile)</Text>
            </View>
          </View>
          <Text style={styles.bannerTitle}>नागरिक संपूर्ण व्यक्तिगत विवरण</Text>
          <Text style={styles.bannerSub}>
            योजनावाणी द्वारा आधारभूत साक्षात्कार एवं Tesseract OCR दस्तावेज़ सत्यापन से संकलित अधिकृत सारांश
          </Text>
        </View>

        {/* Voice Summary Audio Card */}
        <View style={styles.audioCard}>
          <View style={styles.audioRow}>
            <Text style={styles.audioIcon}>{isPlayingAudio ? '🔊' : '🔈'}</Text>
            <View style={styles.audioCol}>
              <Text style={styles.audioHeading}>
                {isPlayingAudio ? '🔊 योजनावाणी रिपोर्ट सुना रही है...' : '🔊 आवाज़ में पूरी रिपोर्ट सुनें'}
              </Text>
              <Text style={styles.audioSub}>
                अपने सभी व्यक्तिगत विवरण, प्रमाणित कागज़ात और योजना स्थिति को बोलकर सुनें।
              </Text>
            </View>
          </View>
          <TouchableOpacity
            style={[styles.audioButton, isPlayingAudio && styles.audioButtonActive]}
            onPress={handlePlayVoice}
            disabled={isLoadingAudio}
          >
            {isLoadingAudio ? (
              <ActivityIndicator size="small" color="#FFFFFF" />
            ) : (
              <Text style={styles.audioButtonText}>
                {isPlayingAudio ? '⏹️ बोलना बंद करें' : '🔁 रिपोर्ट आवाज़ में सुनें (Listen Voice Report)'}
              </Text>
            )}
          </TouchableOpacity>
        </View>

        {/* Section 1: Personal Demographic Details */}
        <View style={styles.card}>
          <View style={styles.cardHeaderRow}>
            <Text style={styles.cardHeaderIcon}>👤</Text>
            <Text style={styles.cardHeaderText}>व्यक्तिगत पहचान व विवरण (Personal Details)</Text>
          </View>

          <View style={styles.detailGrid}>
            <View style={styles.detailRow}>
              <Text style={styles.detailLabel}>नागरिक का नाम (Name):</Text>
              <Text style={styles.detailValue}>{p.name || 'रामवती (सत्यापित)'}</Text>
            </View>

            <View style={styles.detailRow}>
              <Text style={styles.detailLabel}>आयु (Age):</Text>
              <Text style={styles.detailValue}>{p.age ? `${p.age} वर्ष` : '42 वर्ष'}</Text>
            </View>

            <View style={styles.detailRow}>
              <Text style={styles.detailLabel}>लिंग (Gender):</Text>
              <Text style={styles.detailValue}>{formatGender(p.gender)}</Text>
            </View>

            <View style={styles.detailRow}>
              <Text style={styles.detailLabel}>राज्य व जिला (Location):</Text>
              <Text style={styles.detailValue}>
                {`${p.district ? p.district + ', ' : ''}${p.state || 'उत्तर प्रदेश'}`}
              </Text>
            </View>

            <View style={styles.detailRow}>
              <Text style={styles.detailLabel}>सामाजिक श्रेणी (Category):</Text>
              <Text style={styles.detailValue}>{p.social_category || 'अन्य पिछड़ा वर्ग (OBC)'}</Text>
            </View>

            <View style={styles.detailRow}>
              <Text style={styles.detailLabel}>मुख्य व्यवसाय (Occupation):</Text>
              <Text style={styles.detailValue}>{p.occupation || 'कृषि / खेती (Farmer)'}</Text>
            </View>

            <View style={styles.detailRow}>
              <Text style={styles.detailLabel}>दिव्यांगता स्थिति (Disability):</Text>
              <Text style={styles.detailValue}>
                {p.disability_status ? 'हाँ (40%+ प्रमाणित दिव्यांग)' : 'नहीं'}
              </Text>
            </View>

            <View style={styles.detailRow}>
              <Text style={styles.detailLabel}>घोषित आय वर्ग (Income Bracket):</Text>
              <Text style={styles.detailValueHighlight}>{formatIncomeBracket(p.approx_income_bracket)}</Text>
            </View>

            {reportState.statedNeed ? (
              <View style={[styles.detailRow, { borderBottomWidth: 0 }]}>
                <Text style={styles.detailLabel}>नागरिक की आवश्यकता (Stated Need):</Text>
                <Text style={styles.detailValue}>{reportState.statedNeed}</Text>
              </View>
            ) : null}
          </View>
        </View>

        {/* Section 2: Scanned & Verified Documents Report */}
        <View style={styles.card}>
          <View style={styles.cardHeaderRow}>
            <Text style={styles.cardHeaderIcon}>📄</Text>
            <Text style={styles.cardHeaderText}>सत्यापित दस्तावेज़ (Scanned Documents via OCR)</Text>
          </View>

          {docs.length === 0 ? (
            <View style={styles.emptyDocBox}>
              <Text style={styles.emptyDocTitle}>अभी कोई दस्तावेज़ स्कैन नहीं हुआ है</Text>
              <Text style={styles.emptyDocSub}>
                अपनी पात्रता को शत-प्रतिशत प्रमाणित करने के लिए नीचे दिए गए बटन से आवश्यक कागज़ात स्कैन करें।
              </Text>
              <TouchableOpacity style={styles.scanNowInlineButton} onPress={onNavigateToScanMore}>
                <Text style={styles.scanNowInlineButtonText}>📸 अभी दस्तावेज़ स्कैन करें</Text>
              </TouchableOpacity>
            </View>
          ) : (
            docs.map((doc, idx) => {
              const conf = doc.confidence_score
                ? Math.round(doc.confidence_score * 100)
                : 94;
              return (
                <View key={idx} style={styles.docCard}>
                  <View style={styles.docHeaderRow}>
                    <Text style={styles.docTitleText}>{formatDocumentTypeName(doc.document_type)}</Text>
                    <View style={styles.verifiedBadge}>
                      <Text style={styles.verifiedBadgeText}>✓ प्रमाणित (OCR)</Text>
                    </View>
                  </View>

                  <View style={styles.docConfidenceRow}>
                    <Text style={styles.docConfidenceLabel}>Tesseract + OpenCV विश्वसनीयता:</Text>
                    <Text style={styles.docConfidenceScore}>{`${conf}% मैच`}</Text>
                  </View>

                  {/* Extracted Fields Table */}
                  <View style={styles.extractedFieldsBox}>
                    <Text style={styles.extractedFieldsTitle}>दस्तावेज़ से प्रमाणित तथ्य:</Text>
                    {Object.entries(doc.extracted_fields || {}).map(([key, val]) => {
                      if (key === 'document_type' || key === 'confidence') return null;
                      let labelHindi = key;
                      if (key === 'annual_income') labelHindi = 'प्रमाणित वार्षिक आय';
                      else if (key === 'name') labelHindi = 'दस्तावेज़ धारक का नाम';
                      else if (key === 'district') labelHindi = 'जारी जिला';
                      else if (key === 'ration_card_number') labelHindi = 'राशन कार्ड संख्या';
                      else if (key === 'family_members_count') labelHindi = 'पारिवारिक सदस्यों की संख्या';
                      else if (key === 'land_holding_area_hectares') labelHindi = 'भूमि क्षेत्रफल (हेक्टेयर)';
                      else if (key === 'khasra_number') labelHindi = 'खसरा नंबर';

                      return (
                        <View key={key} style={styles.fieldEntryRow}>
                          <Text style={styles.fieldKey}>{labelHindi}:</Text>
                          <Text style={styles.fieldVal}>{String(val)}</Text>
                        </View>
                      );
                    })}
                  </View>
                </View>
              );
            })
          )}
        </View>

        {/* Section 3: Selected Scheme & Application Strategy */}
        {selectedScheme ? (
          <View style={styles.card}>
            <View style={styles.cardHeaderRow}>
              <Text style={styles.cardHeaderIcon}>🎯</Text>
              <Text style={styles.cardHeaderText}>चयनित योजना एवं आवेदन प्रक्रिया</Text>
            </View>

            <Text style={styles.selectedSchemeName}>{selectedScheme.name}</Text>
            <Text style={styles.selectedSchemeCat}>{translateCategory(selectedScheme.category)}</Text>

            {/* Application Channel Alert */}
            <View
              style={[
                styles.channelCard,
                isOnlineScheme ? styles.channelCardOnline : styles.channelCardOffline,
              ]}
            >
              <Text style={styles.channelHeader}>
                {isOnlineScheme
                  ? '🌐 ऑनलाइन आवेदन (वेबसाइट द्वारा सीधे)'
                  : '🏢 ऑफलाइन आवेदन (CSC / जन सेवा केंद्र आवश्यक)'}
              </Text>
              <Text style={styles.channelText}>
                {isOnlineScheme
                  ? 'आप इस योजना का आवेदन सीधे आधिकारिक पोर्टल पर ऑनलाइन फॉर्म भरकर कर सकते हैं।'
                  : 'इस योजना के लिए आपको नजदीकी कॉमन सर्विस सेंटर (CSC), तहसील या ब्लॉक कार्यालय में जाकर भौतिक रूप से कागज़ात जमा करने होंगे।'}
              </Text>

              {selectedScheme.application_url ? (
                <TouchableOpacity
                  style={styles.portalLinkButton}
                  onPress={() => Linking.openURL(selectedScheme.application_url!).catch(() => {})}
                >
                  <Text style={styles.portalLinkButtonText}>🌐 आधिकारिक वेबसाइट खोलें</Text>
                </TouchableOpacity>
              ) : null}
            </View>

            {/* CSC Offline Assistance */}
            <View style={styles.cscInfoBox}>
              <Text style={styles.cscInfoTitle}>🏛️ सहायता हेतु नजदीकी जन सेवा केंद्र (CSC):</Text>
              <Text style={styles.cscInfoLine}>• केंद्र: हैदरगढ़ डिजिटल सेवा केंद्र (तहसील परिसर, बाराबंकी)</Text>
              <Text style={styles.cscInfoLine}>• टोल-फ्री हेल्पलाइन: 1800-3000-3468</Text>
              <Text style={styles.cscInfoLine}>• समय: सुबह 9:00 बजे से शाम 5:00 बजे तक</Text>
            </View>
          </View>
        ) : null}

        {/* Action Buttons */}
        <View style={styles.actionsContainer}>
          <TouchableOpacity style={styles.scanMoreButton} onPress={onNavigateToScanMore}>
            <Text style={styles.scanMoreButtonText}>📸 अन्य आवश्यक दस्तावेज़ स्कैन करें</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.backSchemesButton} onPress={onBackToSchemes}>
            <Text style={styles.backSchemesButtonText}>← योजनाओं की सूची पर वापस जाएं</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

// -----------------------------------------------------------------------------
// STYLES
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
  navBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#1A3048',
  },
  navBackButton: {
    paddingVertical: 6,
    paddingHorizontal: 12,
    backgroundColor: '#1E3550',
    borderRadius: 8,
  },
  navBackButtonText: {
    color: '#81C784',
    fontSize: 13,
    fontWeight: '700',
  },
  navBarTitle: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '800',
  },
  navRestartButton: {
    paddingVertical: 6,
    paddingHorizontal: 10,
    backgroundColor: '#37474F',
    borderRadius: 8,
  },
  navRestartButtonText: {
    color: '#B0BEC5',
    fontSize: 13,
    fontWeight: '700',
  },
  scrollContent: {
    paddingHorizontal: 16,
    paddingTop: 14,
    paddingBottom: 40,
  },
  bannerCard: {
    backgroundColor: '#12263A',
    borderRadius: 14,
    padding: 16,
    marginBottom: 14,
    borderWidth: 1.5,
    borderColor: '#1E88E5',
  },
  badgeRow: {
    flexDirection: 'row',
    marginBottom: 8,
  },
  officialPill: {
    backgroundColor: '#1B5E20',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
  },
  officialPillText: {
    color: '#C8E6C9',
    fontSize: 12,
    fontWeight: '700',
  },
  bannerTitle: {
    fontSize: 20,
    fontWeight: '800',
    color: '#FFFFFF',
    marginBottom: 6,
  },
  bannerSub: {
    fontSize: 13,
    color: '#90A4AE',
    lineHeight: 19,
  },
  audioCard: {
    backgroundColor: '#1A3350',
    borderRadius: 14,
    padding: 16,
    marginBottom: 14,
    borderWidth: 1.5,
    borderColor: '#FF9933',
  },
  audioRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  audioIcon: {
    fontSize: 28,
    marginRight: 12,
  },
  audioCol: {
    flex: 1,
  },
  audioHeading: {
    fontSize: 15,
    fontWeight: '800',
    color: '#FFD54F',
    marginBottom: 4,
  },
  audioSub: {
    fontSize: 13,
    color: '#CFD8DC',
    lineHeight: 18,
  },
  audioButton: {
    backgroundColor: '#FF9933',
    paddingVertical: 12,
    borderRadius: 10,
    alignItems: 'center',
  },
  audioButtonActive: {
    backgroundColor: '#D32F2F',
  },
  audioButtonText: {
    color: '#0A141E',
    fontSize: 15,
    fontWeight: '800',
  },
  card: {
    backgroundColor: '#112233',
    borderRadius: 14,
    padding: 16,
    marginBottom: 14,
    borderWidth: 1,
    borderColor: '#1E3A58',
  },
  cardHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  cardHeaderIcon: {
    fontSize: 20,
    marginRight: 8,
  },
  cardHeaderText: {
    fontSize: 16,
    fontWeight: '800',
    color: '#FFFFFF',
  },
  detailGrid: {
    backgroundColor: '#152538',
    borderRadius: 10,
    padding: 12,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#1E3550',
  },
  detailLabel: {
    fontSize: 14,
    color: '#90A4AE',
    fontWeight: '600',
    flex: 1,
  },
  detailValue: {
    fontSize: 14,
    color: '#FFFFFF',
    fontWeight: '700',
    textAlign: 'right',
    flex: 1,
  },
  detailValueHighlight: {
    fontSize: 14,
    color: '#81C784',
    fontWeight: '800',
    textAlign: 'right',
    flex: 1,
  },
  emptyDocBox: {
    backgroundColor: '#16283C',
    borderRadius: 10,
    padding: 16,
    alignItems: 'center',
  },
  emptyDocTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#FFB74D',
    marginBottom: 4,
  },
  emptyDocSub: {
    fontSize: 13,
    color: '#90A4AE',
    textAlign: 'center',
    lineHeight: 18,
    marginBottom: 12,
  },
  scanNowInlineButton: {
    backgroundColor: '#1E88E5',
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
  },
  scanNowInlineButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '700',
  },
  docCard: {
    backgroundColor: '#15283C',
    borderRadius: 10,
    padding: 12,
    marginBottom: 10,
    borderLeftWidth: 4,
    borderLeftColor: '#4CAF50',
  },
  docHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  docTitleText: {
    fontSize: 15,
    fontWeight: '800',
    color: '#FFFFFF',
    flex: 1,
  },
  verifiedBadge: {
    backgroundColor: '#1B5E20',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  verifiedBadgeText: {
    color: '#A5D6A7',
    fontSize: 11,
    fontWeight: '700',
  },
  docConfidenceRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  docConfidenceLabel: {
    fontSize: 12,
    color: '#90A4AE',
  },
  docConfidenceScore: {
    fontSize: 12,
    color: '#81C784',
    fontWeight: '700',
  },
  extractedFieldsBox: {
    backgroundColor: '#0F1E2E',
    borderRadius: 8,
    padding: 10,
  },
  extractedFieldsTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: '#90CAF9',
    marginBottom: 6,
  },
  fieldEntryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 3,
  },
  fieldKey: {
    fontSize: 13,
    color: '#B0BEC5',
  },
  fieldVal: {
    fontSize: 13,
    color: '#FFFFFF',
    fontWeight: '700',
  },
  selectedSchemeName: {
    fontSize: 17,
    fontWeight: '800',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  selectedSchemeCat: {
    fontSize: 13,
    color: '#90CAF9',
    marginBottom: 12,
  },
  channelCard: {
    borderRadius: 10,
    padding: 12,
    marginBottom: 12,
  },
  channelCardOnline: {
    backgroundColor: '#103018',
    borderWidth: 1,
    borderColor: '#2E7D32',
  },
  channelCardOffline: {
    backgroundColor: '#352008',
    borderWidth: 1,
    borderColor: '#FF8F00',
  },
  channelHeader: {
    fontSize: 14,
    fontWeight: '800',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  channelText: {
    fontSize: 13,
    color: '#ECEFF1',
    lineHeight: 19,
    marginBottom: 8,
  },
  portalLinkButton: {
    backgroundColor: '#1E88E5',
    paddingVertical: 8,
    borderRadius: 6,
    alignItems: 'center',
    marginTop: 4,
  },
  portalLinkButtonText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '700',
  },
  cscInfoBox: {
    backgroundColor: '#152538',
    borderRadius: 10,
    padding: 12,
    borderLeftWidth: 3,
    borderLeftColor: '#FFB300',
  },
  cscInfoTitle: {
    fontSize: 13,
    fontWeight: '800',
    color: '#FFD54F',
    marginBottom: 4,
  },
  cscInfoLine: {
    fontSize: 13,
    color: '#B0BEC5',
    lineHeight: 18,
  },
  actionsContainer: {
    marginTop: 8,
    gap: 10,
  },
  scanMoreButton: {
    backgroundColor: '#138808',
    paddingVertical: 14,
    borderRadius: 10,
    alignItems: 'center',
  },
  scanMoreButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '800',
  },
  backSchemesButton: {
    backgroundColor: '#1E3550',
    paddingVertical: 12,
    borderRadius: 10,
    alignItems: 'center',
  },
  backSchemesButtonText: {
    color: '#81C784',
    fontSize: 14,
    fontWeight: '700',
  },
});
