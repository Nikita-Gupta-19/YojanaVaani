import React, { useState } from 'react';
import { OnboardingScreen } from './src/screens/OnboardingScreen';
import { ConversationScreen } from './src/screens/ConversationScreen';
import { DocumentCaptureScreen } from './src/screens/DocumentCaptureScreen';
import { ResultsScreen, SchemeItem } from './src/screens/ResultsScreen';
import { SchemeDetailScreen } from './src/screens/SchemeDetailScreen';
import { ProfileReportScreen, VerifiedDocument } from './src/screens/ProfileReportScreen';
import { EscalationScreen, CSCInfo } from './src/screens/EscalationScreen';

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

  // Shared session parameters
  const [activeConversationId, setActiveConversationId] = useState<string>('');
  const [targetDocumentType, setTargetDocumentType] = useState<string>('income_certificate');
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
    setCurrentScreen('Conversation');
  };

  const navigateToDocument = (
    convId: string,
    docType: string,
    origin: 'conversation' | 'schemeDetail' = 'conversation'
  ) => {
    setActiveConversationId(convId);
    setTargetDocumentType(docType);
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
      const newDoc: VerifiedDocument = {
        document_type: confirmedFields.document_type || targetDocumentType,
        extracted_fields: confirmedFields,
        verification_status: 'verified',
        confidence_score: confirmedFields.confidence || 0.94,
        confirmed_at: new Date().toISOString(),
      };
      setVerifiedDocuments((prev) => [...prev, newDoc]);
    }

    if (updatedProfile) {
      setCitizenProfile(updatedProfile);
    }

    // If document scan was initiated from Scheme Detail Screen, transition immediately to Profile Report
    if (documentScanOrigin === 'schemeDetail') {
      setCurrentScreen('ProfileReport');
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
    setActiveConversationId('');
    setResultsSchemes([]);
    setResultsSpokenText('');
    setResultsAudioBase64(undefined);
    setSelectedScheme(null);
    setCitizenProfile({});
    setVerifiedDocuments([]);
    setCurrentScreen('Conversation');
  };

  switch (currentScreen) {
    case 'Onboarding':
      return <OnboardingScreen onStartConversation={navigateToConversation} />;

    case 'Conversation':
      return (
        <ConversationScreen
          onNavigateToDocument={(cid, dt) => navigateToDocument(cid, dt, 'conversation')}
          onNavigateToResults={navigateToResults}
          onNavigateToEscalation={navigateToEscalation}
          onBackToOnboarding={() => setCurrentScreen('Onboarding')}
        />
      );

    case 'DocumentCapture':
      return (
        <DocumentCaptureScreen
          conversationId={activeConversationId}
          documentType={targetDocumentType}
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
        />
      );

    case 'SchemeDetail':
      return selectedScheme ? (
        <SchemeDetailScreen
          conversationId={activeConversationId}
          scheme={selectedScheme}
          citizenProfile={citizenProfile}
          onNavigateToDocumentScan={(docType) =>
            navigateToDocument(activeConversationId, docType, 'schemeDetail')
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
        />
      );

    case 'ProfileReport':
      return (
        <ProfileReportScreen
          conversationId={activeConversationId}
          citizenProfile={citizenProfile}
          selectedScheme={selectedScheme}
          verifiedDocuments={verifiedDocuments}
          onNavigateToScanMore={() =>
            navigateToDocument(activeConversationId, 'income_certificate', 'schemeDetail')
          }
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

    default:
      return <OnboardingScreen onStartConversation={navigateToConversation} />;
  }
}
