import React, { useState } from 'react';
import { View } from 'react-native';
import { OnboardingScreen } from './src/screens/OnboardingScreen';
import { ConversationScreen } from './src/screens/ConversationScreen';
import { DocumentCaptureScreen } from './src/screens/DocumentCaptureScreen';
import { ResultsScreen, SchemeItem } from './src/screens/ResultsScreen';
import { SchemeDetailScreen, getDocumentTypeInfo } from './src/screens/SchemeDetailScreen';
import { ProfileReportScreen, VerifiedDocument } from './src/screens/ProfileReportScreen';
import { EscalationScreen, CSCInfo } from './src/screens/EscalationScreen';
import { stopTTSAudio } from './src/services/audioService';

export type ScreenName =
  | 'Onboarding'
  | 'Conversation'
  | 'DocumentCapture'
  | 'Results'
  | 'SchemeDetail'
  | 'ProfileReport'
  | 'Escalation';

export default function App(): React.JSX.Element {
  const [currentScreen, setCurrentScreen] = useState<ScreenName>('Onboarding');
  const [sessionKey, setSessionKey] = useState<number>(0);
  const [hasStartedConversation, setHasStartedConversation] = useState<boolean>(false);

  // Shared session parameters
  const [activeConversationId, setActiveConversationId] = useState<string>('');
  const [targetDocumentType, setTargetDocumentType] = useState<string>('income_certificate');
  const [targetDocumentDisplayName, setTargetDocumentDisplayName] = useState<string>('');
  const [documentScanOrigin, setDocumentScanOrigin] = useState<'conversation' | 'schemeDetail'>('conversation');
  const [resultsSchemes, setResultsSchemes] = useState<SchemeItem[]>([]);
  const [resultsSpokenText, setResultsSpokenText] = useState<string>('');
  const [resultsAudioBase64, setResultsAudioBase64] = useState<string | undefined>(undefined);
  const [selectedScheme, setSelectedScheme] = useState<SchemeItem | null>(null);
  const [citizenProfile, setCitizenProfile] = useState<Record<string, any>>({});
  const [verifiedDocuments, setVerifiedDocuments] = useState<VerifiedDocument[]>([]);
  const [escalationCscInfo, setEscalationCscInfo] = useState<CSCInfo>({});
  const [escalationSpokenText, setEscalationSpokenText] = useState<string>('');

  const navigateToConversation = () => {
    stopTTSAudio().catch(() => {});
    setActiveConversationId('');
    setCitizenProfile({});
    setResultsSchemes([]);
    setResultsSpokenText('');
    setResultsAudioBase64(undefined);
    setSelectedScheme(null);
    setVerifiedDocuments([]);
    setSessionKey((prev) => prev + 1);
    setHasStartedConversation(true);
    setCurrentScreen('Conversation');
  };

  const navigateToDocument = (
    convId: string,
    docType: string,
    origin: 'conversation' | 'schemeDetail' = 'conversation',
    docDisplayName?: string
  ) => {
    setActiveConversationId(convId);
    setTargetDocumentType(docType);
    setTargetDocumentDisplayName(docDisplayName || '');
    setDocumentScanOrigin(origin);
    setCurrentScreen('DocumentCapture');
  };

  const navigateToResults = (
    convId: string,
    schemes: SchemeItem[],
    spokenText: string,
    audioBase64?: string,
    profile?: Record<string, any>
  ) => {
    setActiveConversationId(convId);
    setResultsSchemes(schemes);
    setResultsSpokenText(spokenText);
    setResultsAudioBase64(audioBase64);
    if (profile) {
      setCitizenProfile(profile);
    }
    setCurrentScreen('Results');
  };

  const navigateToSchemeDetail = (scheme: SchemeItem) => {
    setSelectedScheme(scheme);
    setCurrentScreen('SchemeDetail');
  };

  const navigateToReport = () => {
    setCurrentScreen('ProfileReport');
  };

  const navigateToEscalation = (convId: string, cscInfo: CSCInfo, spokenText: string) => {
    setActiveConversationId(convId);
    setEscalationCscInfo(cscInfo);
    setEscalationSpokenText(spokenText);
    setCurrentScreen('Escalation');
  };

  const handleDocumentConfirmationComplete = (
    nextAction: any,
    confirmedFields?: any,
    updatedProfile?: any
  ) => {
    if (confirmedFields && Object.keys(confirmedFields).length > 0) {
      const docType = confirmedFields.document_type || targetDocumentType;
      const docName = confirmedFields.document_name || targetDocumentDisplayName || docType;
      const newDoc: VerifiedDocument = {
        document_type: docType,
        extracted_fields: {
          ...confirmedFields,
          document_type: docType,
          document_name: docName,
        },
        verification_status: 'verified',
        confidence_score: confirmedFields.confidence || 0.94,
        confirmed_at: new Date().toISOString(),
      };
      setVerifiedDocuments((prev) => {
        const filtered = prev.filter((d) => d.document_type.toLowerCase() !== docType.toLowerCase());
        return [...filtered, newDoc];
      });
    }

    if (updatedProfile) {
      setCitizenProfile(updatedProfile);
    }

    // If document scan was initiated from Scheme Detail Screen, return to Scheme Detail Screen so user sees the verified badge!
    if (documentScanOrigin === 'schemeDetail') {
      setCurrentScreen('SchemeDetail');
      return;
    }

    if (nextAction && nextAction.type === 'present_results') {
      navigateToResults(
        activeConversationId,
        nextAction.schemes || resultsSchemes,
        nextAction.text || 'दस्तावेज़ सत्यापन पूर्ण हुआ। योजनाएं प्रस्तुत हैं।',
        nextAction.audio_base64,
        updatedProfile || citizenProfile
      );
    } else {
      setCurrentScreen('Conversation');
    }
  };

  const handleRestart = () => {
    stopTTSAudio().catch(() => {});
    setActiveConversationId('');
    setResultsSchemes([]);
    setResultsSpokenText('');
    setResultsAudioBase64(undefined);
    setSelectedScheme(null);
    setCitizenProfile({});
    setVerifiedDocuments([]);
    setSessionKey((prev) => prev + 1);
    setHasStartedConversation(true);
    setCurrentScreen('Conversation');
  };

  const getNextNeededDocumentType = (
    verifiedList: VerifiedDocument[],
    scheme: SchemeItem | null
  ): { key: string; name: string } => {
    const verifiedKeys = new Set((verifiedList || []).map((d) => d.document_type.toLowerCase()));

    if (scheme && scheme.required_documents) {
      let rawDocs: any[] = [];
      const reqDocs = scheme.required_documents;
      if (Array.isArray(reqDocs)) {
        rawDocs = reqDocs;
      } else if (typeof reqDocs === 'string') {
        try {
          rawDocs = JSON.parse(reqDocs);
        } catch (_e) {
          rawDocs = reqDocs.split(',');
        }
      }

      for (const item of rawDocs) {
        const rawName =
          typeof item === 'object' && item !== null
            ? item.accepts?.[0] || item.notes || item.purpose || ''
            : String(item);
        if (rawName) {
          const info = getDocumentTypeInfo(rawName);
          if (!verifiedKeys.has(info.key.toLowerCase())) {
            return { key: info.key, name: info.displayName };
          }
        }
      }
    }

    const defaultPriorities = [
      { key: 'bank_passbook', name: 'बैंक पासबुक (Bank Passbook)' },
      { key: 'income_certificate', name: 'आय प्रमाण पत्र (Income Certificate)' },
      { key: 'aadhaar_card', name: 'आधार कार्ड (Aadhaar Card)' },
      { key: 'ration_card', name: 'राशन कार्ड (Ration Card)' },
      { key: 'khasra_khatauni', name: 'खसरा / खतौनी भू-अभिलेख (Land Record)' },
    ];
    for (const d of defaultPriorities) {
      if (!verifiedKeys.has(d.key.toLowerCase())) {
        return d;
      }
    }
    return { key: 'bank_passbook', name: 'बैंक पासबुक (Bank Passbook)' };
  };

  const renderActiveScreen = () => {
    switch (currentScreen) {
      case 'Onboarding':
        return (
          <OnboardingScreen
            onStartConversation={navigateToConversation}
            onSelectHistorySession={(convId, schemes, profile, text) => {
              stopTTSAudio().catch(() => {});
              navigateToResults(convId, schemes, text, undefined, profile);
            }}
          />
        );

      case 'DocumentCapture':
        return (
          <DocumentCaptureScreen
            conversationId={activeConversationId}
            documentType={targetDocumentType}
            documentDisplayName={targetDocumentDisplayName}
            citizenProfile={citizenProfile}
            alreadyVerifiedDocTypes={verifiedDocuments.map((d) => d.document_type)}
            onConfirmationComplete={handleDocumentConfirmationComplete}
            onCancel={() => {
              if (documentScanOrigin === 'schemeDetail') {
                setCurrentScreen('SchemeDetail');
              } else {
                setCurrentScreen('Conversation');
              }
            }}
          />
        );

      case 'Results':
        return (
          <ResultsScreen
            conversationId={activeConversationId}
            schemes={resultsSchemes}
            spokenText={resultsSpokenText}
            audioBase64={resultsAudioBase64}
            citizenProfile={citizenProfile}
            onSelectScheme={navigateToSchemeDetail}
            onViewReport={navigateToReport}
            onStartNewConversation={handleRestart}
            onBackToQuestionnaire={() => {
              stopTTSAudio().catch(() => {});
              setHasStartedConversation(true);
              setCurrentScreen('Conversation');
            }}
          />
        );

      case 'SchemeDetail':
        return selectedScheme ? (
          <SchemeDetailScreen
            conversationId={activeConversationId}
            scheme={selectedScheme}
            citizenProfile={citizenProfile}
            verifiedDocuments={verifiedDocuments}
            onNavigateToDocumentScan={(docType, docDisplayName) =>
              navigateToDocument(activeConversationId, docType, 'schemeDetail', docDisplayName)
            }
            onNavigateToReport={navigateToReport}
            onBack={() => setCurrentScreen('Results')}
          />
        ) : (
          <ResultsScreen
            conversationId={activeConversationId}
            schemes={resultsSchemes}
            spokenText={resultsSpokenText}
            audioBase64={resultsAudioBase64}
            citizenProfile={citizenProfile}
            onSelectScheme={navigateToSchemeDetail}
            onViewReport={navigateToReport}
            onStartNewConversation={handleRestart}
            onBackToQuestionnaire={() => {
              stopTTSAudio().catch(() => {});
              setHasStartedConversation(true);
              setCurrentScreen('Conversation');
            }}
          />
        );

      case 'ProfileReport':
        return (
          <ProfileReportScreen
            conversationId={activeConversationId}
            citizenProfile={citizenProfile}
            selectedScheme={selectedScheme}
            verifiedDocuments={verifiedDocuments}
            onNavigateToScanMore={() => {
              const nextDoc = getNextNeededDocumentType(verifiedDocuments, selectedScheme);
              navigateToDocument(activeConversationId, nextDoc.key, 'schemeDetail', nextDoc.name);
            }}
            onBackToSchemes={() => setCurrentScreen('Results')}
            onStartNewConversation={handleRestart}
          />
        );

      case 'Escalation':
        return (
          <EscalationScreen
            conversationId={activeConversationId}
            cscInfo={escalationCscInfo}
            spokenText={escalationSpokenText}
            onBackToConversation={() => setCurrentScreen('Conversation')}
          />
        );

      case 'Conversation':
      default:
        return null;
    }
  };

  if (currentScreen === 'Onboarding') {
    return (
      <OnboardingScreen
        onStartConversation={navigateToConversation}
        onSelectHistorySession={(convId, schemes, profile, text) => {
          stopTTSAudio().catch(() => {});
          navigateToResults(convId, schemes, text, undefined, profile);
        }}
      />
    );
  }

  return (
    <View style={{ flex: 1 }}>
      {/* Questionnaire Screen - only mounted when conversation has actually been started */}
      {hasStartedConversation && (
        <View
          style={{
            flex: 1,
            display: currentScreen === 'Conversation' ? 'flex' : 'none',
          }}
        >
          <ConversationScreen
            key={activeConversationId ? `conv_${activeConversationId}` : `conv_session_${sessionKey}`}
            conversationIdProp={activeConversationId}
            initialProfile={citizenProfile}
            initialSchemes={resultsSchemes}
            isActive={currentScreen === 'Conversation'}
            onNavigateToDocument={(cid, dt) => navigateToDocument(cid, dt, 'conversation')}
            onNavigateToResults={navigateToResults}
            onNavigateToEscalation={navigateToEscalation}
            onBackToOnboarding={() => {
              stopTTSAudio().catch(() => {});
              setCurrentScreen('Onboarding');
            }}
          />
        </View>
      )}

      {/* Other active screens rendered when active */}
      {currentScreen !== 'Conversation' && renderActiveScreen()}
    </View>
  );
}
