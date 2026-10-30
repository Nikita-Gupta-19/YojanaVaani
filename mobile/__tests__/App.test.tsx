/**
 * @format
 */

import React from 'react';
import ReactTestRenderer from 'react-test-renderer';
import App from '../App';
import { OnboardingScreen } from '../src/screens/OnboardingScreen';
import { ConversationScreen } from '../src/screens/ConversationScreen';
import { DocumentCaptureScreen } from '../src/screens/DocumentCaptureScreen';
import { ResultsScreen } from '../src/screens/ResultsScreen';
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
    // Check permission description text
    expect(
      root.findByProps({
        children: 'अपनी आवाज़ में बोलकर जवाब देने और अपनी बात बताने के लिए।',
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
    const label = root.findByProps({ children: 'बातचीत शुरू करें (यहाँ दबाएं) 🎙️' });
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
});
