import React, { useState } from 'react';
import { OnboardingScreen } from './src/screens/OnboardingScreen';
import { ConversationScreen } from './src/screens/ConversationScreen';
import { DocumentCaptureScreen } from './src/screens/DocumentCaptureScreen';
import { ResultsScreen, SchemeItem } from './src/screens/ResultsScreen';
import { EscalationScreen, CSCInfo } from './src/screens/EscalationScreen';

export type ScreenName =
  | 'Onboarding'
  | 'Conversation'
  | 'DocumentCapture'
  | 'Results'
  | 'Escalation';

export default function App(): React.JSX.Element {
  const [currentScreen, setCurrentScreen] = useState<ScreenName>('Onboarding');

  // Shared session parameters
  const [activeConversationId, setActiveConversationId] = useState<string>('');
  const [targetDocumentType, setTargetDocumentType] = useState<string>('income_certificate');
  const [resultsSchemes, setResultsSchemes] = useState<SchemeItem[]>([]);
  const [resultsSpokenText, setResultsSpokenText] = useState<string>('');
  const [escalationCscInfo, setEscalationCscInfo] = useState<CSCInfo>({});
  const [escalationSpokenText, setEscalationSpokenText] = useState<string>('');

  const navigateToConversation = () => {
    setCurrentScreen('Conversation');
  };

  const navigateToDocument = (convId: string, docType: string) => {
    setActiveConversationId(convId);
    setTargetDocumentType(docType);
    setCurrentScreen('DocumentCapture');
  };

  const navigateToResults = (convId: string, schemes: SchemeItem[], spokenText: string) => {
    setActiveConversationId(convId);
    setResultsSchemes(schemes);
    setResultsSpokenText(spokenText);
    setCurrentScreen('Results');
  };

  const navigateToEscalation = (convId: string, cscInfo: CSCInfo, spokenText: string) => {
    setActiveConversationId(convId);
    setEscalationCscInfo(cscInfo);
    setEscalationSpokenText(spokenText);
    setCurrentScreen('Escalation');
  };

  const handleDocumentConfirmationComplete = (nextAction: any) => {
    if (nextAction && nextAction.type === 'present_results') {
      navigateToResults(
        activeConversationId,
        nextAction.schemes || resultsSchemes,
        nextAction.text || 'दस्तावेज़ सत्यापन पूर्ण हुआ। योजनाएं प्रस्तुत हैं।'
      );
    } else {
      setCurrentScreen('Conversation');
    }
  };

  const handleRestart = () => {
    setActiveConversationId('');
    setResultsSchemes([]);
    setResultsSpokenText('');
    setCurrentScreen('Conversation');
  };

  switch (currentScreen) {
    case 'Onboarding':
      return <OnboardingScreen onStartConversation={navigateToConversation} />;

    case 'Conversation':
      return (
        <ConversationScreen
          onNavigateToDocument={navigateToDocument}
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
          onCancel={() => setCurrentScreen('Conversation')}
        />
      );

    case 'Results':
      return (
        <ResultsScreen
          conversationId={activeConversationId}
          schemes={resultsSchemes}
          spokenText={resultsSpokenText}
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
