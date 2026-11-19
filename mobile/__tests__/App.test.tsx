/**
 * @format
 */

import React from 'react';
import ReactTestRenderer from 'react-test-renderer';
import App from '../App';
import { OnboardingScreen } from '../src/screens/OnboardingScreen';
import { ConversationScreen } from '../src/screens/ConversationScreen';
import { DocumentCaptureScreen } from '../src/screens/DocumentCaptureScreen';
import { ResultsScreen, SchemeItem } from '../src/screens/ResultsScreen';
import { SchemeDetailScreen } from '../src/screens/SchemeDetailScreen';
import { ProfileReportScreen } from '../src/screens/ProfileReportScreen';
import { EscalationScreen } from '../src/screens/EscalationScreen';
import {
  clearQueue,
  enqueueResponse,
  getQueuedCount,
  getQueuedResponses,
  removeQueuedResponse,
  setConnectivityStatus,
  subscribeConnectivity,
} from '../src/services/offlineQueue';

declare const global: any;

// Mock fetch globally for network calls
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    status: 200,
    json: () =>
      Promise.resolve({
        status: 'ok',
        conversation_id: 'test_uuid_123',
        question_index: 0,
        total_questions: 9,
        action: {
          type: 'ask_question',
          text: 'नमस्ते! आपका शुभ नाम क्या है?',
          field_name: 'name',
        },
      }),
  })
) as jest.Mock;

function findParentWithProp(instance: any, prop: string): any {
  let curr = instance;
  while (curr) {
    if (curr.props && curr.props[prop]) {
      return curr;
    }
    curr = curr.parent;
  }
  return null;
}

describe('Phase 7 React Native Mobile App Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    clearQueue();
  });

  test('App renders OnboardingScreen with Hindi branding and permission cards', async () => {
    let renderer: ReactTestRenderer.ReactTestRenderer;
    await ReactTestRenderer.act(async () => {
      renderer = ReactTestRenderer.create(<App />);
    });

    const root = renderer!.root;
    // Check Devanagari title branding
    expect(root.findByProps({ children: 'योजनावाणी' })).toBeTruthy();
    // Check English title
    expect(root.findByProps({ children: 'YojanaVaani' })).toBeTruthy();
    // Check greeting text
    expect(
      root.findByProps({
        children: 'नमस्ते! सिर्फ अपनी आवाज़ में बोलकर अपने हक की सरकारी योजनाएं खोजें।',
      })
    ).toBeTruthy();

    await ReactTestRenderer.act(async () => {
      renderer.unmount();
    });
  });

  test('OnboardingScreen calls onStartConversation when start button is pressed', async () => {
    const mockStart = jest.fn();
    let renderer: ReactTestRenderer.ReactTestRenderer;
    await ReactTestRenderer.act(async () => {
      renderer = ReactTestRenderer.create(
        <OnboardingScreen onStartConversation={mockStart} />
      );
    });

    const root = renderer!.root;
    const label = root.findByProps({ children: 'शुरू करने के लिए यहाँ दबाएं' });
    const touchable = findParentWithProp(label, 'onPress');
    expect(touchable).toBeTruthy();

    await ReactTestRenderer.act(async () => {
      touchable.props.onPress();
    });

    expect(mockStart).toHaveBeenCalled();

    await ReactTestRenderer.act(async () => {
      renderer.unmount();
    });
  });

  test('ConversationScreen initializes session and renders voice assistant prompt', async () => {
    let renderer: ReactTestRenderer.ReactTestRenderer;
    await ReactTestRenderer.act(async () => {
      renderer = ReactTestRenderer.create(
        <ConversationScreen
          onNavigateToDocument={jest.fn()}
          onNavigateToResults={jest.fn()}
          onNavigateToEscalation={jest.fn()}
          onBackToOnboarding={jest.fn()}
        />
      );
    });

    const root = renderer!.root;
    expect(root.findByProps({ children: 'योजनावाणी सहायक' })).toBeTruthy();

    await ReactTestRenderer.act(async () => {
      renderer.unmount();
    });
  });

  test('DocumentCaptureScreen renders viewfinder and handles OCR confirmation', async () => {
    const mockConfirm = jest.fn();
    let renderer: ReactTestRenderer.ReactTestRenderer;
    await ReactTestRenderer.act(async () => {
      renderer = ReactTestRenderer.create(
        <DocumentCaptureScreen
          conversationId="test_uuid_123"
          documentType="income_certificate"
          onConfirmationComplete={mockConfirm}
          onCancel={jest.fn()}
        />
      );
    });

    const root = renderer!.root;
    expect(root.findByProps({ children: 'दस्तावेज़ सत्यापन (OCR)' })).toBeTruthy();

    // Trigger mock photo capture
    const captureBtnLabel = root.findByProps({ children: '📸 फोटो खींचें (Capture Photo)' });
    const captureTouchable = findParentWithProp(captureBtnLabel, 'onPress');
    expect(captureTouchable).toBeTruthy();

    await ReactTestRenderer.act(async () => {
      captureTouchable.props.onPress();
    });

    // Check confirmation button appears
    const confirmYesLabel = root.findByProps({ children: '✓ हाँ, यह सही है' });
    const confirmTouchable = findParentWithProp(confirmYesLabel, 'onPress');
    expect(confirmTouchable).toBeTruthy();

    await ReactTestRenderer.act(async () => {
      confirmTouchable.props.onPress();
    });

    expect(mockConfirm).toHaveBeenCalled();

    await ReactTestRenderer.act(async () => {
      renderer.unmount();
    });
  });

  test('ResultsScreen displays ranked schemes with correct verdict badges', async () => {
    const mockSchemes = [
      {
        id: 1,
        name: 'PM-KISAN Samman Nidhi',
        category: 'Agriculture',
        verdict: 'QUALIFIES' as const,
        reason: 'नागरिक सभी निर्धारित पात्रता शर्तों को पूरा करते हैं।',
        benefits: '₹6,000 प्रति वर्ष 3 समान किस्तों में।',
      },
      {
        id: 2,
        name: 'Pragati Scholarship (Girls)',
        category: 'Education',
        verdict: 'DOES_NOT_QUALIFY' as const,
        reason: 'यह योजना केवल बालिकाओं के लिए है।',
      },
    ];

    let renderer: ReactTestRenderer.ReactTestRenderer;
    await ReactTestRenderer.act(async () => {
      renderer = ReactTestRenderer.create(
        <ResultsScreen
          conversationId="test_uuid_123"
          schemes={mockSchemes}
          spokenText="आप पीएम किसान योजना के लिए पात्र हैं।"
          onStartNewConversation={jest.fn()}
        />
      );
    });

    const root = renderer!.root;
    expect(root.findByProps({ children: 'PM-KISAN Samman Nidhi' })).toBeTruthy();
    expect(root.findByProps({ children: '✓ आप पात्र हैं (यह योजना मिलेगी)' })).toBeTruthy();
    expect(root.findByProps({ children: '✕ यह योजना नहीं मिल सकती' })).toBeTruthy();

    await ReactTestRenderer.act(async () => {
      renderer.unmount();
    });
  });

  test('EscalationScreen displays CSC kiosk information and helpline dialer', async () => {
    const mockCsc = {
      csc_name: 'Haidergarh Digital Seva Kendra',
      helpline: '1800-3000-3468',
      address: 'Near Tehsil Complex, Haidergarh, Barabanki, UP - 225126',
    };

    let renderer: ReactTestRenderer.ReactTestRenderer;
    await ReactTestRenderer.act(async () => {
      renderer = ReactTestRenderer.create(
        <EscalationScreen
          conversationId="test_uuid_123"
          cscInfo={mockCsc}
          spokenText="कृपया निकटतम जन सेवा केंद्र पर जाएं।"
          onBackToConversation={jest.fn()}
        />
      );
    });

    const root = renderer!.root;
    expect(root.findByProps({ children: 'Haidergarh Digital Seva Kendra' })).toBeTruthy();
    expect(root.findByProps({ children: '1800-3000-3468' })).toBeTruthy();

    await ReactTestRenderer.act(async () => {
      renderer.unmount();
    });
  });

  test('offlineQueue correctly queues and restores responses during network drop', () => {
    expect(getQueuedCount()).toBe(0);

    // Queue two responses
    const item1 = enqueueResponse('conv_1', 'मेरा नाम राम है');
    const item2 = enqueueResponse('conv_1', 'मेरी उम्र 40 साल है');

    expect(getQueuedCount()).toBe(2);
    expect(getQueuedResponses()[0].text).toBe('मेरा नाम राम है');

    // Remove one item
    removeQueuedResponse(item1.id);
    expect(getQueuedCount()).toBe(1);
    expect(getQueuedResponses()[0].id).toBe(item2.id);

    // Test connectivity subscription
    let onlineStatus = true;
    const unsub = subscribeConnectivity((isOnline) => {
      onlineStatus = isOnline;
    });

    setConnectivityStatus(false);
    expect(onlineStatus).toBe(false);

    setConnectivityStatus(true);
    expect(onlineStatus).toBe(true);

    unsub();
  });

  test('SchemeDetailScreen displays elaborate description, online vs CSC mention, and bulleted documents', async () => {
    const mockScheme: SchemeItem = {
      id: 542,
      name: 'PM SVANidhi Micro Credit Scheme',
      category: 'Labour & Employment',
      government_name: 'Central Government',
      verdict: 'QUALIFIES',
      description: 'पीएम स्वनिधि योजना शहरी पथ विक्रेताओं (स्ट्रीट वेंडर्स) के लिए एक विशेष सूक्ष्म ऋण योजना है जिसके तहत कार्यशील पूंजी ऋण प्रदान किया जाता है।',
      benefits: '₹10,000 से ₹50,000 तक का कार्यशील पूंजी ऋण एवं 7% ब्याज अनुदान सीधे बैंक खाते में।',
      required_documents: [
        { purpose: 'identity_proof', accepts: ['Aadhaar Card'], required: true },
        { purpose: 'vendor_proof', accepts: ['Vending Certificate / LOR'], required: true },
        { purpose: 'bank_account_proof', accepts: ['Bank Passbook'], required: true },
      ],
      application_process: 'Mode: Online. URL: https://pmsvanidhi.mohua.gov.in. Apply through portal or visit nearest CSC kiosk.',
      application_url: 'https://pmsvanidhi.mohua.gov.in',
    };

    const mockScanDocs = jest.fn();
    const mockViewReport = jest.fn();
    const mockBack = jest.fn();

    let renderer: ReactTestRenderer.ReactTestRenderer;
    await ReactTestRenderer.act(async () => {
      renderer = ReactTestRenderer.create(
        <SchemeDetailScreen
          conversationId="test_uuid_123"
          scheme={mockScheme}
          citizenProfile={{ name: 'रामवती', occupation: 'दुकानदार' }}
          onNavigateToDocumentScan={mockScanDocs}
          onNavigateToReport={mockViewReport}
          onBack={mockBack}
        />
      );
    });

    const root = renderer!.root;
    // Check scheme name and elaborate description
    expect(root.findByProps({ children: 'PM SVANidhi Micro Credit Scheme' })).toBeTruthy();
    expect(root.findByProps({ children: 'योजना का विस्तृत विवरण' })).toBeTruthy();
    expect(
      root.findByProps({
        children: 'पीएम स्वनिधि योजना शहरी पथ विक्रेताओं (स्ट्रीट वेंडर्स) के लिए एक विशेष सूक्ष्म ऋण योजना है जिसके तहत कार्यशील पूंजी ऋण प्रदान किया जाता है।',
      })
    ).toBeTruthy();

    // Check online vs offline CSC mention
    expect(root.findByProps({ children: 'आवेदन का माध्यम (ऑनलाइन या सीएससी केंद्र?)' })).toBeTruthy();
    expect(
      root.findAllByProps({
        children: '🌐 ऑनलाइन आवेदन (वेबसाइट / पोर्टल द्वारा सीधे घर बैठे)',
      }).length
    ).toBeGreaterThan(0);

    // Check bulleted documents section
    expect(root.findByProps({ children: 'आवश्यक दस्तावेज़ (Required Documents)' })).toBeTruthy();
    expect(root.findByProps({ children: 'आधार कार्ड (Aadhaar Card)' })).toBeTruthy();
    expect(root.findByProps({ children: 'बैंक पासबुक (Bank Passbook)' })).toBeTruthy();

    // Check document scanning button triggers callback
    const scanBtnLabel = root.find(
      node =>
        typeof node.props.children === 'string' &&
        node.props.children.includes('आवश्यक दस्तावेज़ स्कैन करें')
    );
    const scanTouchable = findParentWithProp(scanBtnLabel, 'onPress');
    expect(scanTouchable).toBeTruthy();

    await ReactTestRenderer.act(async () => {
      scanTouchable.props.onPress();
    });
    expect(mockScanDocs).toHaveBeenCalled();

    await ReactTestRenderer.act(async () => {
      renderer.unmount();
    });
  });

  test('ProfileReportScreen renders complete personal details, verified document facts, and scheme summary', async () => {
    const mockProfile = {
      name: 'रामवती',
      age: 42,
      gender: 'Female',
      state: 'उत्तर प्रदेश',
      district: 'बाराबंकी',
      social_category: 'अन्य पिछड़ा वर्ग (OBC)',
      occupation: 'खेती / किसान',
      disability_status: false,
      approx_income_bracket: 'below_2_lakh',
      stated_need: 'सोलर पंप सिंचाई सहायता योजना',
    };

    const mockDocs = [
      {
        document_type: 'income_certificate',
        extracted_fields: {
          annual_income: 45000,
          name: 'रामवती',
          district: 'बाराबंकी',
        },
        confidence_score: 0.95,
        verification_status: 'verified',
      },
    ];

    const mockScheme: SchemeItem = {
      id: 101,
      name: 'पीएम कुसुम सोलर पंप योजना',
      category: 'Agriculture',
      verdict: 'QUALIFIES',
      application_process: 'Mode: Offline via CSC and Agriculture Department',
    };

    let renderer: ReactTestRenderer.ReactTestRenderer;
    await ReactTestRenderer.act(async () => {
      renderer = ReactTestRenderer.create(
        <ProfileReportScreen
          conversationId="test_uuid_123"
          citizenProfile={mockProfile}
          selectedScheme={mockScheme}
          verifiedDocuments={mockDocs}
          onNavigateToScanMore={jest.fn()}
          onBackToSchemes={jest.fn()}
          onStartNewConversation={jest.fn()}
        />
      );
    });

    const root = renderer!.root;
    // Check Title
    expect(root.findByProps({ children: 'नागरिक संपूर्ण व्यक्तिगत विवरण' })).toBeTruthy();

    // Check personal details
    expect(root.findAllByProps({ children: 'रामवती' }).length).toBeGreaterThan(0);
    expect(root.findByProps({ children: '42 वर्ष' })).toBeTruthy();
    expect(root.findByProps({ children: 'महिला (Female)' })).toBeTruthy();
    expect(root.findByProps({ children: 'राज्य व जिला (Location):' })).toBeTruthy();
    expect(root.findByProps({ children: '₹2,00,000 से कम (गरीबी रेखा/कम आय वर्ग)' })).toBeTruthy();

    // Check verified document OCR details
    expect(root.findByProps({ children: 'आय प्रमाण पत्र (Income Certificate)' })).toBeTruthy();
    expect(root.findByProps({ children: '45000' })).toBeTruthy();
    expect(root.findByProps({ children: '✓ प्रमाणित (OCR)' })).toBeTruthy();
    expect(root.findByProps({ children: '95% मैच' })).toBeTruthy();

    // Check scheme and application mode
    expect(root.findByProps({ children: 'पीएम कुसुम सोलर पंप योजना' })).toBeTruthy();
    expect(
      root.findByProps({
        children: '🏢 ऑफलाइन आवेदन (CSC / जन सेवा केंद्र आवश्यक)',
      })
    ).toBeTruthy();

    await ReactTestRenderer.act(async () => {
      renderer.unmount();
    });
  });

  test('ResultsScreen provides back button to return to questionnaire and edit answers', async () => {
    const mockBackToQuestionnaire = jest.fn();
    const mockSchemes: SchemeItem[] = [
      {
        id: 101,
        name: 'PM-KISAN Samman Nidhi',
        verdict: 'QUALIFIES',
        benefits: '₹6,000 प्रति वर्ष',
      },
    ];

    let renderer: ReactTestRenderer.ReactTestRenderer;
    await ReactTestRenderer.act(async () => {
      renderer = ReactTestRenderer.create(
        <ResultsScreen
          conversationId="test_uuid_edit_123"
          schemes={mockSchemes}
          spokenText="योजनाएं प्रस्तुत हैं"
          citizenProfile={{ name: 'सुनीता देवी', age: 35 }}
          onStartNewConversation={jest.fn()}
          onBackToQuestionnaire={mockBackToQuestionnaire}
        />
      );
    });

    const root = renderer!.root;
    const backBtn = root.findByProps({ children: 'प्रश्नावली पर वापस जाएं (Edit Answers)' });
    expect(backBtn).toBeTruthy();

    const touchable = findParentWithProp(backBtn, 'onPress');
    expect(touchable).toBeTruthy();
    await ReactTestRenderer.act(async () => {
      touchable.props.onPress();
    });

    expect(mockBackToQuestionnaire).toHaveBeenCalledTimes(1);

    await ReactTestRenderer.act(async () => {
      renderer.unmount();
    });
  });

  test('userHistoryService correctly saves and retrieves citizen assessment history', () => {
    const {
      saveUserSession,
      getUserSessions,
      getUserSessionById,
      clearAllUserSessions,
    } = require('../src/services/userHistoryService');

    clearAllUserSessions();
    expect(getUserSessions().length).toBe(0);

    const saved = saveUserSession({
      id: 'session_hist_001',
      citizenProfile: { name: 'राजेश कुमार', age: 40, occupation: 'किसान' },
      recommendedSchemes: [{ id: 1, name: 'पीएम-किसान', verdict: 'QUALIFIES' }],
      statedNeed: 'खेती के लिए सहायता',
    });

    expect(saved.id).toBe('session_hist_001');
    expect(getUserSessions().length).toBe(1);

    const retrieved = getUserSessionById('session_hist_001');
    expect(retrieved).toBeTruthy();
    expect(retrieved?.citizenProfile?.name).toBe('राजेश कुमार');
    expect(retrieved?.recommendedSchemes.length).toBe(1);

    clearAllUserSessions();
    expect(getUserSessions().length).toBe(0);
  });

  test('DocumentCaptureScreen and SchemeDetailScreen handle any required document dynamically (e.g. Bank Passbook, Caste Certificate)', async () => {
    const { getDocumentTypeInfo } = require('../src/screens/SchemeDetailScreen');

    // 1. Verify getDocumentTypeInfo maps documents distinctly
    const bankInfo = getDocumentTypeInfo('बैंक पासबुक');
    expect(bankInfo.key).toBe('bank_passbook');
    expect(bankInfo.displayName).toContain('बैंक पासबुक');

    const casteInfo = getDocumentTypeInfo('जाति प्रमाण पत्र');
    expect(casteInfo.key).toBe('caste_certificate');
    expect(casteInfo.displayName).toContain('जाति प्रमाण पत्र');

    const customInfo = getDocumentTypeInfo('मत्स्य पालन पंजीकरण प्रमाण');
    expect(customInfo.key).toContain('custom_');

    // 2. Render DocumentCaptureScreen with Bank Passbook and verify banner shows exact title
    let renderer: ReactTestRenderer.ReactTestRenderer;
    await ReactTestRenderer.act(async () => {
      renderer = ReactTestRenderer.create(
        <DocumentCaptureScreen
          conversationId="test_conv_doc_dynamic"
          documentType="bank_passbook"
          documentDisplayName="बैंक पासबुक (Bank Passbook)"
          alreadyVerifiedDocTypes={['aadhaar_card']}
          onConfirmationComplete={jest.fn()}
          onCancel={jest.fn()}
        />
      );
    });

    const root = renderer!.root;
    // Must display the exact requested document title at top, NOT one of the 4 predefined fallback ones
    const banners = root.findAllByProps({ children: 'बैंक पासबुक (Bank Passbook)' });
    expect(banners.length).toBeGreaterThanOrEqual(1);

    await ReactTestRenderer.act(async () => {
      renderer.unmount();
    });
  });

  test('Saved record answers display automatically when clicking edit answers from results screen', async () => {
    const { saveUserSession } = require('../src/services/userHistoryService');
    const mockProfile = {
      name: 'सुनीता शर्मा',
      age: 42,
      gender: 'Female',
      state: 'Uttar Pradesh',
      district: 'Barabanki',
      approx_income_bracket: 'below_2_lakh',
      social_category: 'OBC',
      occupation: 'Farmer',
      disability_status: false,
      stated_need: 'खेत के लिए सोलर पंप',
    };

    saveUserSession({
      id: 'saved_session_999',
      citizenProfile: mockProfile,
      recommendedSchemes: [
        {
          id: 1,
          name: 'PM-KISAN Samman Nidhi',
          category: 'Agriculture',
          verdict: 'QUALIFIES',
        },
      ],
      statedNeed: 'खेत के लिए सोलर पंप',
    });

    let renderer: ReactTestRenderer.ReactTestRenderer;
    await ReactTestRenderer.act(async () => {
      renderer = ReactTestRenderer.create(
        <ConversationScreen
          conversationIdProp="saved_session_999"
          initialProfile={mockProfile}
          initialSchemes={[{ id: 1, name: 'PM-KISAN Samman Nidhi' }]}
          onNavigateToDocument={jest.fn()}
          onNavigateToResults={jest.fn()}
          onNavigateToEscalation={jest.fn()}
          onBackToOnboarding={jest.fn()}
        />
      );
    });

    const root = renderer!.root;

    // 1. Verify that previously given answers are automatically rendered on screen
    expect(root.findAllByProps({ children: 'सुनीता शर्मा' }).length).toBeGreaterThanOrEqual(1);
    expect(root.findAllByProps({ children: '42 साल' }).length).toBeGreaterThanOrEqual(1);
    expect(root.findAllByProps({ children: 'महिला' }).length).toBeGreaterThanOrEqual(1);
    expect(root.findAllByProps({ children: 'उत्तर प्रदेश, बाराबंकी' }).length).toBeGreaterThanOrEqual(1);
    expect(root.findAllByProps({ children: '2 लाख से कम' }).length).toBeGreaterThanOrEqual(1);
    expect(root.findAllByProps({ children: 'ओबीसी' }).length).toBeGreaterThanOrEqual(1);
    expect(root.findAllByProps({ children: 'खेती / किसान' }).length).toBeGreaterThanOrEqual(1);
    expect(root.findAllByProps({ children: 'खेत के लिए सोलर पंप' }).length).toBeGreaterThanOrEqual(1);

    // 2. Verify header shows saved record progress (9/9)
    expect(root.findAllByProps({ children: 'सहेजा गया रिकॉर्ड (9/9)' }).length).toBeGreaterThanOrEqual(1);

    // 3. Verify "योजनाएं देखें →" button is visible to immediately return to results
    const viewResultsBtns = root.findAllByProps({ children: 'योजनाएं देखें →' });
    expect(viewResultsBtns.length).toBeGreaterThanOrEqual(1);

    // 4. Verify editing mode activates when selecting a field
    const editChips = root.findAllByProps({ children: '✏️ बदलें' });
    expect(editChips.length).toBeGreaterThanOrEqual(1);

    await ReactTestRenderer.act(async () => {
      renderer.unmount();
    });
  });

  test('Full App flow: opening saved record from history and clicking edit answers shows answers automatically', async () => {
    const { saveUserSession } = require('../src/services/userHistoryService');
    const fullProfile = {
      name: 'रामवती देवी',
      age: 45,
      gender: 'Female',
      state: 'Uttar Pradesh',
      district: 'Barabanki',
      approx_income_bracket: 'below_2_lakh',
      social_category: 'OBC',
      occupation: 'Farmer',
      disability_status: false,
      stated_need: 'खेत के लिए सोलर पंप',
    };

    saveUserSession({
      id: 'flow_session_777',
      citizenProfile: fullProfile,
      recommendedSchemes: [
        {
          id: 1,
          name: 'PM-KISAN',
          category: 'Agriculture',
          verdict: 'QUALIFIES',
        },
      ],
      statedNeed: 'खेत के लिए सोलर पंप',
    });

    let renderer: ReactTestRenderer.ReactTestRenderer;
    await ReactTestRenderer.act(async () => {
      renderer = ReactTestRenderer.create(<App />);
    });

    const root = renderer!.root;

    // 1. App starts on OnboardingScreen; open the history modal
    const historyBtn = root.findByProps({ accessibilityLabel: 'सहेजे गए आवेदन व पिछला इतिहास देखें' });
    expect(historyBtn).toBeTruthy();

    await ReactTestRenderer.act(async () => {
      historyBtn.props.onPress();
    });

    // 2. Select the saved session
    const selectSessionLabel = root.findAllByProps({ children: '➔ परिणाम व रिपोर्ट देखें' });
    expect(selectSessionLabel.length).toBeGreaterThanOrEqual(1);
    const selectTouchable = findParentWithProp(selectSessionLabel[0], 'onPress');
    expect(selectTouchable).toBeTruthy();

    await ReactTestRenderer.act(async () => {
      selectTouchable.props.onPress();
    });

    // 3. User is now on ResultsScreen; find "प्रश्नावली पर वापस जाएं (Edit Answers)" button
    const backToQuestionnaireBtn = root.findByProps({ accessibilityLabel: 'प्रश्नावली पर वापस जाएं और उत्तर बदलें' });
    expect(backToQuestionnaireBtn).toBeTruthy();

    await ReactTestRenderer.act(async () => {
      backToQuestionnaireBtn.props.onPress();
    });

    // 4. User is on ConversationScreen: verify Ramwati Devi and her answers are displayed automatically!
    expect(root.findAllByProps({ children: 'रामवती देवी' }).length).toBeGreaterThanOrEqual(1);
    expect(root.findAllByProps({ children: '45 साल' }).length).toBeGreaterThanOrEqual(1);
    expect(root.findAllByProps({ children: 'महिला' }).length).toBeGreaterThanOrEqual(1);
    expect(root.findAllByProps({ children: 'उत्तर प्रदेश, बाराबंकी' }).length).toBeGreaterThanOrEqual(1);
    expect(root.findAllByProps({ children: '2 लाख से कम' }).length).toBeGreaterThanOrEqual(1);
    expect(root.findAllByProps({ children: 'खेती / किसान' }).length).toBeGreaterThanOrEqual(1);

    // 5. Ensure it is in saved record mode and NOT asking question 1
    expect(root.findAllByProps({ children: 'सहेजा गया रिकॉर्ड (9/9)' }).length).toBeGreaterThanOrEqual(1);

    await ReactTestRenderer.act(async () => {
      renderer.unmount();
    });
  });
});
