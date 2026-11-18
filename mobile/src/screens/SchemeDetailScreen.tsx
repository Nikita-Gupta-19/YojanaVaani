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

interface SchemeDetailScreenProps {
  conversationId: string;
  scheme: SchemeItem;
  citizenProfile?: Record<string, any>;
  verifiedDocuments?: any[];
  onNavigateToDocumentScan: (documentType: string, documentDisplayName?: string) => void;
  onNavigateToReport: () => void;
  onBack: () => void;
}

// -----------------------------------------------------------------------------
// HINDI NORMALIZATION & FORMATTING HELPERS
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

const cleanText = (text: string): string => {
  return text
    .replace(/[{}"]/g, '')
    .replace(/\\n/g, '\n')
    .replace(/\*\*/g, '')
    .replace(/>/g, '')
    .trim();
};

// -----------------------------------------------------------------------------
// CURATED PURE HINDI SCHEME DESCRIPTIONS (NO ENGLISH JARGON)
// -----------------------------------------------------------------------------

const SCHEME_HINDI_DESCRIPTIONS: Record<string, string> = {
  // Education & Scholarships
  'pm-yasasvi':
    'पीएम-यशस्वी योजना अन्य पिछड़ा वर्ग (OBC), आर्थिक रूप से कमजोर वर्ग (EBC) और गैर-अधिसूचित/विमुक्त जनजातियों (DNT) के छात्र-छात्राओं के लिए केंद्र सरकार की प्रमुख राष्ट्रीय छात्रवृत्ति योजना है। इसका उद्देश्य कक्षा 10वीं के बाद उच्च शिक्षा, कॉलेज और तकनीकी संस्थानों में पढ़ाई कर रहे जरूरतमंद विद्यार्थियों को वार्षिक वित्तीय सहायता प्रदान कर उच्च शिक्षा को सुलभ बनाना है।',
  'jai bhim':
    'जय भीम मुख्यमंत्री प्रतिभा विकास योजना दिल्ली सरकार द्वारा अनुसूचित जाति (SC), अन्य पिछड़ा वर्ग (OBC) और आर्थिक रूप से कमजोर वर्ग के प्रतिभाशाली छात्र-छात्राओं को सिविल सेवा (UPSC), इंजीनियरिंग (JEE), मेडिकल (NEET) और अन्य प्रतिष्ठित प्रतियोगी परीक्षाओं की तैयारी हेतु निःशुल्क कोचिंग और प्रतिमाह वित्तीय वजीफा (स्टाइपेंड) प्रदान करने के लिए चलाई जा रही है।',
  'delhi higher & technical education':
    'दिल्ली उच्च एवं तकनीकी शिक्षा सहायता योजना दिल्ली के स्थायी निवासी छात्र-छात्राओं को उच्च शिक्षा संस्थानों और विश्वविद्यालयों में डिप्लोमा, स्नातक अथवा स्नातकोत्तर की पढ़ाई के दौरान ट्यूशन फीस और शैक्षणिक खर्चों में सीधी आर्थिक राहत प्रदान करने हेतु संचालित एक महत्वपूर्ण योजना है।',
  'higher education and skill development':
    'उच्च शिक्षा और कौशल विकास गारंटी योजना के अंतर्गत दिल्ली के मेधावी छात्रों को उच्च शिक्षण संस्थानों में पढ़ाई जारी रखने के लिए बिना किसी जमीन-जायदाद के बंधक अथवा तीसरे पक्ष की गारंटी के बैंकों द्वारा रियायती ब्याज दर पर ₹10 लाख तक का शिक्षा ऋण (एजुकेशन लोन) और सरकारी वित्तीय गारंटी उपलब्ध कराई जाती है।',
  'shreyas':
    'श्रेयस (SHREYAS) योजना अन्य पिछड़ा वर्ग और मेधावी युवाओं को उच्च शिक्षण संस्थानों, विश्वविद्यालयों और शोध संस्थानों में एम.फिल या पीएचडी जैसी उच्चतर शिक्षा व शोध कार्य पूरा करने के लिए राष्ट्रीय स्तर पर फैलोशिप व आर्थिक सहायता प्रदान करती है।',
  'persons with disabilities scheme in colleges':
    'कॉलेजों में दिव्यांगजन योजना (HEPSN) का मुख्य उद्देश्य उच्च शिक्षण संस्थानों और कॉलेजों में अध्ययनरत विशेष आवश्यकता वाले दिव्यांग छात्र-छात्राओं को शिक्षण सामग्री, सहायक उपकरण, सुगम्यता तथा वित्तीय अनुदान उपलब्ध कराकर उच्च शिक्षा को उनके अनुकूल बनाना है।',
  'post-matric scholarship for students with disabilities':
    'दिव्यांग विद्यार्थियों के लिए पोस्ट-मैट्रिक छात्रवृत्ति योजना के अंतर्गत 40% या अधिक दिव्यांगता वाले छात्र-छात्राओं को मान्यता प्राप्त कॉलेजों व विश्वविद्यालयों में उच्च शिक्षा पूरी करने के लिए वार्षिक रखरखाव भत्ता, पुस्तक अनुदान तथा अध्ययन शुल्क की पूर्ण आर्थिक सहायता प्रदान की जाती है।',
  'free supply of text books':
    'मुफ्त पाठ्य पुस्तक योजना दिल्ली सरकार के शिक्षा विभाग द्वारा सरकारी व सहायता प्राप्त विद्यालयों में पढ़ने वाले जरूरतमंद छात्र-छात्राओं को निःशुल्क पाठ्य पुस्तकें अथवा पुस्तकों के क्रय हेतु नकद अनुदान प्रदान करने के लिए संचालित की जाती है।',
  'merit cum means linked':
    'मेरिट-कम-मीन्स लिंक्ड वित्तीय सहायता योजना दिल्ली के सरकारी विश्वविद्यालयों में उच्च शिक्षा प्राप्त कर रहे आर्थिक रूप से कमजोर परिवारों के मेधावी छात्र-छात्राओं को ट्यूशन फीस में 25% से 100% तक की छूट व वित्तीय प्रतिपूर्ति प्रदान करती है।',
  'financial assistance to sc students for pursuing higher studies abroad':
    'अनुसूचित जाति के मेधावी छात्रों के लिए विदेश में उच्च शिक्षा सहायता योजना के तहत स्नातकोत्तर और पीएचडी स्तर की अंतरराष्ट्रीय पढ़ाई के लिए दिल्ली सरकार द्वारा ट्यूशन फीस और जीवन-यापन भत्ते का वित्तीय अनुदान दिया जाता है।',

  // Pensions & Social Security
  'old age pension':
    'इंदिरा गांधी राष्ट्रीय वृद्धावस्था पेंशन योजना के तहत 60 वर्ष या उससे अधिक आयु के गरीबी रेखा (BPL) से नीचे जीवन-यापन करने वाले बुजुर्ग नागरिकों को हर महीने सीधे उनके बैंक खाते में मासिक पेंशन प्रदान की जाती है ताकि वे सम्मानपूर्वक जीवन जी सकें।',
  'widow pension':
    'निराश्रित महिला एवं विधवा पेंशन योजना के अंतर्गत पति की मृत्यु के बाद आर्थिक रूप से असहाय महिलाओं को आत्मनिर्भर बनाने और परिवार के भरण-पोषण के लिए सरकार द्वारा मासिक वित्तीय पेंशन सीधे बैंक खाते में दी जाती है।',
  'divyang pension':
    'दिव्यांगजन पेंशन योजना के अंतर्गत 40 प्रतिशत अथवा उससे अधिक शारीरिक दिव्यांगता वाले पात्र नागरिकों को जीवन-यापन, चिकित्सा एवं बुनियादी ज़रूरतों के लिए प्रतिमाह सरकारी पेंशन सहायता सीधे बैंक खाते में अंतरित की जाती है।',
  'pension benefit for the construction workers':
    'भवन एवं अन्य सन्निर्माण कर्मकार कल्याण बोर्ड द्वारा पंजीकृत 60 वर्ष की आयु पूर्ण कर चुके निर्माण श्रमिकों को जीवन-यापन हेतु नियमित मासिक पेंशन सहायता प्रदान की जाती है।',
  'disability pension for the construction workers':
    'पंजीकृत निर्माण श्रमिकों के लिए दिव्यांगता पेंशन योजना के अंतर्गत कार्य के दौरान अथवा स्थायी रूप से दिव्यांग होने पर श्रमिक को नियमित मासिक आर्थिक पेंशन दी जाती है।',

  // Health, Housing & Family Welfare
  'delhi arogya kosh':
    'दिल्ली आरोग्य कोष योजना के तहत दिल्ली के सरकारी अस्पतालों में इलाज करा रहे जरूरतमंद नागरिकों को गंभीर बीमारियों, बड़े ऑपरेशनों, विशेष जांचों (MRI, CT Scan) और प्रत्यारोपण के लिए वित्तीय सहायता प्रदान की जाती है।',
  'financial assistance for the marriage of daughters of poor widows':
    'गरीब विधवाओं और अनाथ कन्याओं के विवाह हेतु वित्तीय सहायता योजना के अंतर्गत आर्थिक रूप से कमजोर परिवारों की बेटियों के विवाह के खर्च में मदद हेतु सरकार द्वारा एकमुश्त आर्थिक अनुदान दिया जाता है।',
  'financial assistance as interest subsidy on home loan':
    'गृह ऋण ब्याज सब्सिडी योजना के तहत पूर्व सैनिकों और उनके परिवारों को अपना पक्का मकान बनाने अथवा खरीदने के लिए लिए गए बैंक होम लोन पर ब्याज में सरकारी सब्सिडी और वित्तीय छूट प्रदान की जाती है।',
  'pm-kisan':
    'प्रधानमंत्री किसान सम्मान निधि योजना के तहत सभी पात्र भूमिधारक किसान परिवारों को प्रति वर्ष ₹6,000 की वित्तीय सहायता ₹2,000 की तीन समान किस्तों में सीधे उनके बैंक खातों में डीबीटी के माध्यम से भेजी जाती है।',
  'pm svanidhi':
    'पीएम स्वनिधि योजना शहरी एवं ग्रामीण क्षेत्रों में रेहड़ी, पटरी, ठेला और खोमचा लगाने वाले छोटे विक्रेताओं को बिना किसी गारंटी के आसान कार्यशील पूंजी ऋण (वर्किंग कैपिटल लोन) उपलब्ध कराने के लिए संचालित है।',
  'mukhyamantri pragatisheel pashupalak':
    'मुख्यमंत्री प्रगतिशील पशुपालक प्रोत्साहन योजना उत्तर प्रदेश में देशी नस्ल की दुधारू गायों (गिर, साहीवाल आदि) के पालन व दूध उत्पादन को बढ़ावा देने के लिए पशुपालकों को वित्तीय प्रोत्साहन देने हेतु संचालित है।',
};

// -----------------------------------------------------------------------------
// CURATED HINDI SCHEME NAMES & TITLES (DUAL-SCRIPT ACCESSIBILITY)
// -----------------------------------------------------------------------------
export const SCHEME_HINDI_NAMES: Record<string, string> = {
  'pm-yasasvi': 'पीएम-यशस्वी: ओबीसी, ईबीसी व डीएनटी छात्रवृत्ति योजना (PM-YASASVI)',
  'jai bhim': 'जय भीम मुख्यमंत्री प्रतिभा विकास योजना (निःशुल्क कोचिंग)',
  'delhi higher & technical education': 'दिल्ली उच्च एवं तकनीकी शिक्षा सहायता योजना',
  'higher education and skill development': 'उच्च शिक्षा एवं कौशल विकास गारंटी योजना (शिक्षा ऋण)',
  'shreyas': 'श्रेयस राष्ट्रीय उच्चतर शिक्षा फेलोशिप योजना',
  'persons with disabilities scheme in colleges': 'कॉलेजों में दिव्यांगजन सुगम्यता व सहायता योजना (HEPSN)',
  'post-matric scholarship for students with disabilities': 'दिव्यांग विद्यार्थियों के लिए पोस्ट-मैट्रिक छात्रवृत्ति योजना',
  'free supply of text books': 'निःशुल्क पाठ्य पुस्तक सहायता योजना',
  'merit cum means linked': 'मेरिट-कम-मीन्स लिंक्ड वित्तीय सहायता योजना (फीस माफ़ी)',
  'financial assistance to sc students for pursuing higher studies abroad': 'एससी विद्यार्थियों हेतु विदेश में उच्च शिक्षा सहायता योजना',
  'old age pension': 'इंदिरा गांधी राष्ट्रीय वृद्धावस्था पेंशन योजना',
  'widow pension': 'निराश्रित महिला एवं विधवा पेंशन योजना',
  'divyang pension': 'दिव्यांगजन पेंशन योजना',
  'pension benefit for the construction workers': 'निर्माण श्रमिकों के लिए वृद्धावस्था पेंशन योजना',
  'disability pension for the construction workers': 'निर्माण श्रमिकों के लिए दिव्यांगता पेंशन योजना',
  'natural death assistance': 'निर्माण श्रमिक सामान्य मृत्यु आर्थिक सहायता योजना',
  'accidental death assistance': 'निर्माण श्रमिक दुर्घटना मृत्यु आर्थिक सहायता योजना',
  'funeral assistance': 'निर्माण श्रमिक अंत्येष्टि (अंतिम संस्कार) सहायता योजना',
  'medical assistance for the construction': 'निर्माण श्रमिक चिकित्सा सहायता योजना',
  'delhi arogya kosh': 'दिल्ली आरोग्य कोष योजना (निःशुल्क गंभीर इलाज)',
  'financial assistance for the marriage of daughters of poor widows': 'गरीब विधवाओं की पुत्रियों के विवाह हेतु आर्थिक सहायता',
  'financial assistance as interest subsidy on home loan': 'गृह ऋण ब्याज सब्सिडी योजना (होम लोन सहायता)',
  'rajiv gandhi swavlamban': 'राजीव गांधी स्वावलंबन स्वरोजगार योजना',
  'pm-kisan': 'प्रधानमंत्री किसान सम्मान निधि (पीएम-किसान)',
  'pm svanidhi': 'पीएम स्वनिधि योजना (रेहड़ी-पटरी विक्रेता ऋण)',
  'delhi arogya nidhi': 'दिल्ली आरोग्य निधि योजना',
  'pre-matric scholarship': 'अन्य पिछड़ा वर्ग (OBC) प्री-मैट्रिक छात्रवृत्ति योजना',
  'education loan scheme': 'दिल्ली उच्च शिक्षा ऋण योजना',
  'mahila samriddhi': 'महिला समृद्धि योजना (लघु व्यवसाय ऋण)',
  'nikshay poshan': 'निक्षय पोषण योजना (टीबी मरीज सहायता)',
  'pradhan mantri awaas yojana': 'प्रधानमंत्री आवास योजना (ग्रामीण पक्का मकान)',
  'mukhyamantri pragatisheel pashupalak': 'मुख्यमंत्री प्रगतिशील पशुपालक प्रोत्साहन योजना (दूध उत्पादन)',
};

import { translateSchemeName as translateSchemeNameHelper } from '../services/schemeTranslationService';

export const translateSchemeName = (name: string): string => {
  return translateSchemeNameHelper(name);
};

// -----------------------------------------------------------------------------
// CURATED PURE HINDI BENEFITS (ZERO UNFORMATTED ENGLISH TABLES)
// -----------------------------------------------------------------------------
export const SCHEME_HINDI_BENEFITS: Record<string, string> = {
  'pm-yasasvi':
    '• ग्रुप 1 (डिग्री एवं पीजी स्तर के प्रोफेशनल कोर्स): ₹20,000/- प्रति वर्ष (₹10,000 शैक्षणिक भत्ता + ₹10,000 ट्यूशन फीस)\n• ग्रुप 2 (अन्य वोकेशनल/डिप्लोमा कोर्स): ₹13,000/- प्रति वर्ष\n• ग्रुप 3 (सामान्य स्नातक एवं स्नातकोत्तर): ₹8,000/- प्रति वर्ष\n• ग्रुप 4 (10वीं के बाद के नॉन-डिग्री कोर्स): ₹5,000/- प्रति वर्ष\n• छात्रवृत्ति की पूरी राशि डीबीटी (DBT) के माध्यम से सीधे आपके आधार लिंक्ड बैंक खाते में भेजी जाएगी।',

  'jai bhim':
    '• संघ लोक सेवा आयोग (UPSC), इंजीनियरिंग (JEE), मेडिकल (NEET) जैसी प्रतियोगी परीक्षाओं की तैयारी हेतु प्रतिष्ठित संस्थानों में 100% निःशुल्क कोचिंग।\n• कोचिंग के दौरान ₹2,500 प्रति माह भोजन व यात्रा भत्ता सीधे बैंक खाते में।',

  'delhi higher & technical education':
    '• दिल्ली के मान्यता प्राप्त कॉलेजों व विश्वविद्यालयों में पढ़ाई के दौरान ट्यूशन फीस और शैक्षणिक खर्चों पर 50% से 100% तक की वित्तीय प्रतिपूर्ति।',

  'higher education and skill development':
    '• उच्च शिक्षण संस्थानों में उच्च शिक्षा हेतु ₹10 लाख तक का शिक्षा ऋण (एजुकेशन लोन) बिना किसी बंधक अथवा तीसरे पक्ष की गारंटी के।\n• ब्याज दरों में सरकारी छूट एवं ऋण पर 100% क्रेडिट गारंटी।',

  'shreyas':
    '• एम.फिल और पीएचडी शोध कार्य हेतु ₹31,000 से ₹35,000 प्रति माह जूनियर/सीनियर रिसर्च फेलोशिप (JRF/SRF)।\n• शोध सामग्री व पुस्तकों हेतु वार्षिक आकस्मिक अनुदान।',

  'persons with disabilities scheme in colleges':
    '• दिव्यांग विद्यार्थियों के लिए कॉलेज में विशेष शिक्षण सामग्री, सहायक उपकरण व सुगम्यता सुविधाएं निःशुल्क।\n• ₹4,000 प्रति माह तक की आर्थिक सहायता व प्रोत्साहन भत्ता।',

  'post-matric scholarship for students with disabilities':
    '• ट्यूशन फीस की पूर्ण प्रतिपूर्ति एवं ₹13,000 से ₹20,000 तक वार्षिक शैक्षणिक भत्ता।\n• दृष्टिबाधित छात्रों हेतु वाचक भत्ता (Reader Allowance) सीधे बैंक खाते में।',

  'free supply of text books':
    '• कक्षा 1 से 5वीं तक: ₹550 प्रति वर्ष पाठ्य-पुस्तकों हेतु नकद सहायता।\n• कक्षा 6 से 8वीं तक: ₹700 प्रति वर्ष नकद सहायता।\n• कक्षा 9वीं से 12वीं तक: ₹800 से ₹1,000 प्रति वर्ष सीधे बैंक खाते में।',

  'merit cum means linked':
    '• अंत्योदय (AAY) व बीपीएल परिवारों के छात्रों के लिए 100% ट्यूशन फीस माफ़।\n• ₹2.5 लाख तक आय वाले परिवारों के छात्रों के लिए 50% फीस माफ़।\n• ₹2.5 से ₹6 लाख आय वाले परिवारों हेतु 25% फीस माफ़ी।',

  'financial assistance to sc students for pursuing higher studies abroad':
    '• विदेश में उच्च शिक्षा (मास्टर्स/पीएचडी) हेतु ₹5,00,000 प्रति वर्ष (अधिकतम ₹20 लाख तक) का संपूर्ण वित्तीय अनुदान।',

  'old age pension':
    '• 60 से 69 वर्ष के बुजुर्गों हेतु ₹2,000 प्रति माह तथा 70 वर्ष से अधिक आयु पर ₹2,500 प्रति माह पेंशन सीधे बैंक खाते में।',

  'widow pension':
    '• निराश्रित एवं विधवा महिलाओं के जीवन-यापन हेतु ₹2,500 प्रति माह नियमित पेंशन सहायता सीधे बैंक खाते में।',

  'divyang pension':
    '• 40% या अधिक दिव्यांगता वाले नागरिकों को ₹2,500 प्रति माह दिव्यांगता पेंशन सीधे बैंक खाते में।',

  'pension benefit for the construction workers':
    '• पंजीकृत निर्माण श्रमिकों को 60 वर्ष की आयु के बाद ₹3,00,0 प्रति माह नियमित पेंशन सहायता।',

  'disability pension for the construction workers':
    '• निर्माण कार्य के दौरान या दुर्घटना में स्थायी दिव्यांग होने पर ₹3,000 प्रति माह पेंशन।',

  'natural death assistance':
    '• पंजीकृत श्रमिक की सामान्य मृत्यु होने पर आश्रित परिवार को ₹1,00,000 की एकमुश्त सहायता।',

  'accidental death assistance':
    '• दुर्घटना में मृत्यु होने पर आश्रित परिवार को ₹2,00,000 की एकमुश्त वित्तीय सहायता।',

  'funeral assistance':
    '• अंतिम संस्कार हेतु ₹10,000 की तत्काल नकद सहायता।',

  'medical assistance for the construction':
    '• अस्पताल में भर्ती रहने पर ₹2,000 से अधिकतम ₹10,000 तक की चिकित्सा सहायता।',

  'delhi arogya kosh':
    '• सरकारी व पैनल अस्पतालों में गंभीर बीमारियों, सर्जरी और जांच के लिए ₹5 लाख तक का निःशुल्क कैशलेस उपचार।',

  'financial assistance for the marriage of daughters of poor widows':
    '• गरीब विधवाओं की बेटियों के विवाह हेतु ₹30,000 की एकमुश्त सरकारी आर्थिक सहायता (अधिकतम 2 बेटियों हेतु)।',

  'financial assistance as interest subsidy on home loan':
    '• होम लोन (मकान ऋण) पर चुकाए जाने वाले ब्याज पर 50% की सीधी ब्याज सब्सिडी (छूट)।',

  'rajiv gandhi swavlamban':
    '• नया व्यवसाय या दुकान खोलने हेतु ₹3,00,000 तक का आसान व्यापार ऋण एवं सरकारी ब्याज सब्सिडी।',

  'pm-kisan':
    '• सभी पात्र किसान परिवारों को प्रति वर्ष ₹6,000 की वित्तीय सहायता (₹2,000 की तीन समान किस्तों में सीधे बैंक खाते में)।',

  'pm svanidhi':
    '• रेहड़ी-पटरी विक्रेताओं को प्रथम चरण में ₹10,000, दूसरे में ₹20,000 तथा तीसरे में ₹50,000 का बिना गारंटी आसान ऋण।',

  'delhi arogya nidhi':
    '• बीपीएल राशन कार्ड धारक मरीजों को गंभीर बीमारियों के इलाज हेतु ₹1.5 लाख तक की आर्थिक मदद।',

  'education loan scheme':
    '• भारत में उच्च शिक्षा हेतु ₹7.5 लाख तथा विदेश में पढ़ाई हेतु ₹15 लाख तक का रियायती शिक्षा ऋण।',

  'mahila samriddhi':
    '• महिलाओं को स्वरोजगार व छोटे व्यापार हेतु ₹1,40,000 तक का आसान सूक्ष्म ऋण व ब्याज में छूट।',

  'nikshay poshan':
    '• टीबी (क्षयरोग) के मरीजों को पौष्टिक आहार हेतु इलाज चलने तक ₹1,000 प्रति माह सीधे बैंक खाते में।',

  'pradhan mantri awaas yojana':
    '• पक्का मकान बनाने हेतु मैदानी क्षेत्रों में ₹1,20,000 तथा पहाड़ी/दुर्गम क्षेत्रों में ₹1,30,000 की सीधी सरकारी आर्थिक सहायता।',

  'mukhyamantri pragatisheel pashupalak':
    '• देशी नस्ल की गायों (गिर, साहीवाल, हरियाणा आदि) के पालन व दूध उत्पादन पर ₹10,000 से ₹15,000 प्रति गाय का प्रोत्साहन पुरस्कार।',
};

const translateDescriptionToHindi = (scheme: SchemeItem): string => {
  // 1. If raw description is already provided in Devanagari Hindi, use it directly
  if (scheme.description && /[\u0900-\u097F]/.test(scheme.description)) {
    return cleanText(scheme.description);
  }

  const nameLower = (scheme.name || '').toLowerCase();

  // 2. Check curated mapping
  for (const [key, desc] of Object.entries(SCHEME_HINDI_DESCRIPTIONS)) {
    if (nameLower.includes(key)) {
      return desc;
    }
  }

  // 3. Dynamic synthesis from scheme metadata in pure vernacular Hindi
  const gov = translateGov(scheme.government_name);
  const cat = translateCategory(scheme.category);

  let targetBeneficiary = 'पात्र नागरिकों';
  if (nameLower.includes('student') || nameLower.includes('scholarship') || nameLower.includes('matric') || nameLower.includes('education') || nameLower.includes('fellowship')) {
    targetBeneficiary = 'जरूरतमंद छात्र-छात्राओं और उच्च शिक्षा के विद्यार्थियों';
  } else if (nameLower.includes('disability') || nameLower.includes('divyang')) {
    targetBeneficiary = 'दिव्यांग भाई-बहनों और विशेष आवश्यकता वाले नागरिकों';
  } else if (nameLower.includes('farmer') || nameLower.includes('kisan') || nameLower.includes('agri')) {
    targetBeneficiary = 'किसान परिवारों और पशुपालकों';
  } else if (nameLower.includes('worker') || nameLower.includes('labour') || nameLower.includes('construction') || nameLower.includes('shramik')) {
    targetBeneficiary = 'मेहनतकश श्रमिकों, मजदूरों और निर्माण कामगारों';
  } else if (nameLower.includes('widow') || nameLower.includes('women') || nameLower.includes('mahila')) {
    targetBeneficiary = 'निराश्रित महिलाओं, विधवाओं और बालिकाओं';
  } else if (nameLower.includes('pension') || nameLower.includes('old age') || nameLower.includes('senior')) {
    targetBeneficiary = 'वरिष्ठ नागरिक बुजुर्गों';
  } else if (nameLower.includes('vendor') || nameLower.includes('loan') || nameLower.includes('thela')) {
    targetBeneficiary = 'छोटे रेहड़ी-पटरी और स्वरोजगार करने वाले व्यापारियों';
  }

  let benefitType = 'आर्थिक सहायता, सब्सिडी और कल्याणकारी लाभ';
  if (nameLower.includes('scholarship') || nameLower.includes('fellowship') || nameLower.includes('fee')) {
    benefitType = 'छात्रवृत्ति, फीस प्रतिपूर्ति और शैक्षणिक अनुदान';
  } else if (nameLower.includes('pension')) {
    benefitType = 'मासिक आर्थिक पेंशन और सामाजिक सुरक्षा';
  } else if (nameLower.includes('loan') || nameLower.includes('credit') || nameLower.includes('guarantee')) {
    benefitType = 'सुलभ ऋण, ब्याज सब्सिडी और वित्तीय सहायता';
  } else if (nameLower.includes('health') || nameLower.includes('arogya') || nameLower.includes('medical')) {
    benefitType = 'निःशुल्क चिकित्सा, स्वास्थ्य बीमा और अस्पताल सहायता';
  } else if (nameLower.includes('marriage')) {
    benefitType = 'विवाह हेतु एकमुश्त सरकारी आर्थिक अनुदान';
  }

  return `${scheme.name} ${gov} के ${cat} विभाग द्वारा संचालित एक प्रमुख जनकल्याणकारी योजना है। इस योजना का मुख्य उद्देश्य ${targetBeneficiary} को सीधे उनके बैंक खाते में ${benefitType} पहुंचाकर उनका सामाजिक व आर्थिक सशक्तिकरण सुनिश्चित करना है।`;
};

const getDisqualificationReasons = (
  scheme: SchemeItem,
  profile?: Record<string, any>
): string[] => {
  const reasons: string[] = [];

  // 1. From scheme.disqualification_reasons
  if (scheme.disqualification_reasons && Array.isArray(scheme.disqualification_reasons)) {
    for (const r of scheme.disqualification_reasons) {
      if (r && typeof r === 'string' && r.trim().length > 0) {
        // Strip English annotations in brackets if any
        const cleanR = r.replace(/\s*\([^)]*\b(Citizen|age|below|exceeds|income|category)\b[^)]*\)/gi, '').trim();
        reasons.push(cleanR);
      }
    }
  }

  // 2. From scheme.missing_fields
  if (scheme.missing_fields && Array.isArray(scheme.missing_fields)) {
    for (const f of scheme.missing_fields) {
      if (f === 'approx_income_bracket' || f === 'income') {
        reasons.push('वार्षिक पारिवारिक आय सीमा का सत्यापन आवश्यक है।');
      } else if (f === 'social_category' || f === 'caste') {
        reasons.push('आरक्षित जाति/सामाजिक वर्ग प्रमाण पत्र आवश्यक है।');
      } else if (f === 'age') {
        reasons.push('नागरिक की उम्र का सरकारी प्रमाण आवश्यक है।');
      } else if (f === 'state' || f === 'district') {
        reasons.push('मूल निवास राज्य और ज़िले का स्थायी प्रमाण पत्र आवश्यक है।');
      } else if (f === 'disability_status') {
        reasons.push('न्यूनतम 40% दिव्यांगता प्रमाण पत्र का सत्यापन आवश्यक है।');
      } else {
        reasons.push(`पात्रता सत्यापन हेतु '${f}' की जानकारी आवश्यक है।`);
      }
    }
  }

  // 3. From scheme.reason if verdict is DOES_NOT_QUALIFY and not yet added
  if (reasons.length === 0 && scheme.reason) {
    const cleanR = scheme.reason.replace(/\s*\([^)]*\b(Citizen|age|below|exceeds|income|category)\b[^)]*\)/gi, '').trim();
    reasons.push(cleanR);
  }

  // 4. Demographic cross-checks against scheme criteria if reasons is still empty
  if (reasons.length === 0 && profile) {
    const sName = (scheme.name || '').toLowerCase();
    const sCat = (scheme.category || '').toLowerCase();

    if (profile.state && profile.state.toLowerCase() !== 'uttar pradesh' && (sName.includes('uttar pradesh') || sCat.includes('up'))) {
      reasons.push(`यह योजना केवल उत्तर प्रदेश राज्य के स्थायी निवासियों के लिए है (आप ${profile.state} के निवासी हैं)।`);
    } else if (profile.state && profile.state.toLowerCase() !== 'delhi' && (sName.includes('delhi') || sName.includes('दिल्ली'))) {
      reasons.push(`यह योजना केवल दिल्ली राज्य के स्थायी निवासियों के लिए है (आप ${profile.state} के निवासी हैं)।`);
    }

    if (profile.age && profile.age < 60 && (sName.includes('old age') || sName.includes('वृद्धावस्था') || sName.includes('senior citizen'))) {
      reasons.push(`इस योजना के लिए नागरिक की न्यूनतम आयु 60 वर्ष होनी चाहिए (आपकी वर्तमान आयु ${profile.age} वर्ष है)।`);
    }

    if (profile.occupation && !profile.occupation.toLowerCase().includes('kisan') && !profile.occupation.toLowerCase().includes('farmer') && (sName.includes('kisan') || sName.includes('कृषि') || sName.includes('crop'))) {
      reasons.push(`यह योजना केवल किसानों व कृषि कार्य करने वालों के लिए है (आपका वर्तमान व्यवसाय '${profile.occupation}' है)।`);
    }

    if (reasons.length === 0) {
      reasons.push('आपकी दर्ज जानकारी इस योजना के पात्रता नियमों के अनुकूल नहीं है।');
    }
  }

  return reasons;
};

export const formatBenefitsHindi = (benefits: any, schemeName?: string): string => {
  const nameLower = (schemeName || '').toLowerCase();

  // 1. Check curated Hindi benefits first
  for (const [key, text] of Object.entries(SCHEME_HINDI_BENEFITS)) {
    if (nameLower.includes(key)) {
      return text;
    }
  }

  if (!benefits) {
    return 'नियमों के अनुसार आर्थिक सहायता एवं सरकारी अनुदान सीधे बैंक खाते में प्रदान किया जाएगा।';
  }

  let bObj = benefits;
  if (typeof bObj === 'string') {
    if (bObj.trim().startsWith('{')) {
      try {
        bObj = JSON.parse(bObj);
      } catch (_e) {
        bObj = null;
      }
    } else if (/[\u0900-\u097F]/.test(bObj)) {
      return cleanText(bObj);
    }
  }

  if (typeof bObj === 'object' && bObj !== null) {
    const min = bObj.benefit_min;
    const max = bObj.benefit_max;
    const freq = bObj.frequency;
    const rawText = bObj.raw_text ? cleanText(bObj.raw_text) : '';

    // If rawText is in Devanagari Hindi, use it
    if (rawText && /[\u0900-\u097F]/.test(rawText)) {
      return rawText;
    }

    if (min && max && min === max) {
      if (freq === 'per_month') {
        return `• ₹${Number(min).toLocaleString('en-IN')} हर महीने पेंशन सीधे बैंक खाते (DBT) में।`;
      }
      return `• ₹${Number(min).toLocaleString('en-IN')} की एकमुश्त सरकारी आर्थिक सहायता सीधे बैंक खाते में।`;
    }

    if (min && max) {
      return `• ₹${Number(min).toLocaleString('en-IN')} से लेकर ₹${Number(max).toLocaleString('en-IN')} तक की आर्थिक सहायता व अनुदान।`;
    }

    if (max) {
      return `• अधिकतम ₹${Number(max).toLocaleString('en-IN')} तक की सरकारी आर्थिक सहायता एवं सब्सिडी।`;
    }
  }

  // Domain-specific vernacular fallback
  if (nameLower.includes('scholarship') || nameLower.includes('छात्रवृत्ति') || nameLower.includes('matric') || nameLower.includes('education') || nameLower.includes('yasasvi')) {
    return '• पाठ्यक्रम की संपूर्ण ट्यूशन फीस, वार्षिक शैक्षणिक भत्ता एवं अध्ययन सामग्री हेतु आर्थिक अनुदान सीधे बैंक खाते (DBT) में देय है।';
  }
  if (nameLower.includes('pension') || nameLower.includes('पेंशन')) {
    return '• प्रतिमाह निर्धारित पेंशन राशि सीधे लाभार्थी के बैंक खाते में डीबीटी (DBT) के माध्यम से भेजी जाएगी।';
  }
  if (nameLower.includes('loan') || nameLower.includes('ऋण') || nameLower.includes('subsidy')) {
    return '• आसान शर्तों पर रियायती ब्याज दर ऋण एवं सरकारी ब्याज सब्सिडी का पूर्ण लाभ प्रदान किया जाएगा।';
  }

  return 'सरकारी नियमों के अनुसार निर्धारित आर्थिक सहायता, सब्सिडी अथवा छात्रवृत्ति सीधे लाभार्थी के बैंक खाते (DBT) में प्रदान की जाएगी।';
};

export interface DocumentTypeInfo {
  key: string;
  displayName: string;
  hindiName: string;
  emoji: string;
}

export const getDocumentTypeInfo = (docName: string): DocumentTypeInfo => {
  const dLower = (docName || '').toLowerCase();

  // 1. Aadhaar Card
  if (dLower.includes('aadhaar') || dLower.includes('आधार') || dLower.includes('uidai') || dLower.includes('identity')) {
    return {
      key: 'aadhaar_card',
      displayName: 'आधार कार्ड (Aadhaar Card)',
      hindiName: 'आधार पहचान पत्र',
      emoji: '🪪',
    };
  }

  // 2. Land Record / Khasra-Khatauni
  if (
    dLower.includes('khasra') ||
    dLower.includes('khatauni') ||
    dLower.includes('खसरा') ||
    dLower.includes('खतौनी') ||
    dLower.includes('भू-अभिलेख') ||
    dLower.includes('land') ||
    dLower.includes('रकबा') ||
    dLower.includes('patta') ||
    dLower.includes('पट्टा')
  ) {
    return {
      key: 'khasra_khatauni',
      displayName: 'खसरा / खतौनी भू-अभिलेख (Land Record)',
      hindiName: 'खसरा / खतौनी भू-अभिलेख',
      emoji: '🚜',
    };
  }

  // 3. Ration Card
  if (dLower.includes('ration') || dLower.includes('राशन') || dLower.includes('bpl') || dLower.includes('aay')) {
    return {
      key: 'ration_card',
      displayName: 'राशन कार्ड (Ration Card)',
      hindiName: 'राशन कार्ड',
      emoji: '🌾',
    };
  }

  // 4. Income Certificate
  if (dLower.includes('income') || dLower.includes('आय प्रमाण') || dLower.includes('salary slip')) {
    return {
      key: 'income_certificate',
      displayName: 'आय प्रमाण पत्र (Income Certificate)',
      hindiName: 'आय प्रमाण पत्र',
      emoji: '📄',
    };
  }

  // 5. Bank Passbook / Account
  if (
    dLower.includes('bank') ||
    dLower.includes('passbook') ||
    dLower.includes('बैंक') ||
    dLower.includes('पासबुक') ||
    dLower.includes('खाता') ||
    dLower.includes('ifsc')
  ) {
    return {
      key: 'bank_passbook',
      displayName: 'बैंक पासबुक (Bank Passbook)',
      hindiName: 'बैंक खाता पासबुक',
      emoji: '🏦',
    };
  }

  // 6. Caste Certificate
  if (dLower.includes('caste') || dLower.includes('जाति') || dLower.includes('sc/st') || dLower.includes('obc')) {
    return {
      key: 'caste_certificate',
      displayName: 'जाति प्रमाण पत्र (Caste Certificate)',
      hindiName: 'जाति प्रमाण पत्र',
      emoji: '📜',
    };
  }

  // 7. Disability / Divyangjan
  if (
    dLower.includes('disability') ||
    dLower.includes('divyang') ||
    dLower.includes('दिव्यांग') ||
    dLower.includes('udid') ||
    dLower.includes('विकलांग')
  ) {
    return {
      key: 'disability_certificate',
      displayName: 'दिव्यांगता प्रमाण पत्र (Disability / UDID Card)',
      hindiName: 'दिव्यांगता प्रमाण पत्र',
      emoji: '♿',
    };
  }

  // 8. Domicile / Residence
  if (dLower.includes('domicile') || dLower.includes('residence') || dLower.includes('निवास') || dLower.includes('मूल निवास')) {
    return {
      key: 'domicile_certificate',
      displayName: 'मूल निवास प्रमाण पत्र (Domicile Certificate)',
      hindiName: 'मूल निवास प्रमाण पत्र',
      emoji: '🏠',
    };
  }

  // 9. Death Certificate
  if (dLower.includes('death') || dLower.includes('मृत्यु') || dLower.includes('विधवा') || dLower.includes('widow')) {
    return {
      key: 'death_certificate',
      displayName: 'पति का मृत्यु प्रमाण पत्र (Death Certificate)',
      hindiName: 'मृत्यु प्रमाण पत्र',
      emoji: '🕊️',
    };
  }

  // 10. Age / Birth
  if (dLower.includes('birth') || dLower.includes('जन्म') || dLower.includes('age') || dLower.includes('आयु')) {
    return {
      key: 'birth_certificate',
      displayName: 'आयु / जन्म प्रमाण पत्र (Age / Birth Certificate)',
      hindiName: 'आयु / जन्म प्रमाण पत्र',
      emoji: '🎂',
    };
  }

  // 11. Marksheet / Academic
  if (
    dLower.includes('marksheet') ||
    dLower.includes('education') ||
    dLower.includes('academic') ||
    dLower.includes('शैक्षणिक') ||
    dLower.includes('अंकतालिका') ||
    dLower.includes('डिग्री') ||
    dLower.includes('degree') ||
    dLower.includes('transcript')
  ) {
    return {
      key: 'academic_certificate',
      displayName: 'शैक्षणिक योग्यता अंकतालिका (Academic Marksheet / Certificate)',
      hindiName: 'शैक्षणिक योग्यता प्रमाण पत्र',
      emoji: '🎓',
    };
  }

  // 12. Job Card / MGNREGA
  if (dLower.includes('job card') || dLower.includes('mgnrega') || dLower.includes('मनरेगा') || dLower.includes('जॉब कार्ड')) {
    return {
      key: 'job_card',
      displayName: 'मनरेगा जॉब कार्ड (MGNREGA Job Card)',
      hindiName: 'मनरेगा जॉब कार्ड',
      emoji: '👷',
    };
  }

  // 13. Kisan Credit Card
  if (dLower.includes('kcc') || dLower.includes('kisan credit') || dLower.includes('क्रेडिट')) {
    return {
      key: 'kisan_credit_card',
      displayName: 'किसान क्रेडिट कार्ड (KCC)',
      hindiName: 'किसान क्रेडिट कार्ड',
      emoji: '💳',
    };
  }

  // 14. Voter ID
  if (dLower.includes('voter') || dLower.includes('मतदाता') || dLower.includes('epic') || dLower.includes('election')) {
    return {
      key: 'voter_id',
      displayName: 'मतदाता पहचान पत्र (Voter ID Card)',
      hindiName: 'मतदाता पहचान पत्र',
      emoji: '🗳️',
    };
  }

  // Clean custom document slug
  const rawClean = cleanText(docName);
  const slug = rawClean
    .replace(/[^a-zA-Z0-9\u0900-\u097F]/g, '_')
    .replace(/_+/g, '_')
    .replace(/^_|_$/g, '')
    .toLowerCase() || 'custom_document';

  return {
    key: `custom_${slug}`,
    displayName: `${rawClean}`,
    hindiName: rawClean,
    emoji: '📄',
  };
};

export interface FormattedDocItem {
  name: string;
  purpose: string;
  required: boolean;
  docTypeKey: string;
  docDisplayName: string;
  emoji: string;
}

const getDocumentList = (docs: any): FormattedDocItem[] => {
  if (!docs) {
    return [
      {
        name: 'आधार कार्ड (Aadhaar Card)',
        purpose: 'नागरिक पहचान एवं निवास प्रमाण पत्र',
        required: true,
        docTypeKey: 'aadhaar_card',
        docDisplayName: 'आधार कार्ड (Aadhaar Card)',
        emoji: '🪪',
      },
      {
        name: 'बैंक पासबुक (Bank Passbook)',
        purpose: 'सरकारी डीबीटी राशि सीधे खाते में प्राप्त करने हेतु',
        required: true,
        docTypeKey: 'bank_passbook',
        docDisplayName: 'बैंक पासबुक (Bank Passbook)',
        emoji: '🏦',
      },
    ];
  }

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

  const result: FormattedDocItem[] = [];

  for (const item of list) {
    let rawName = '';
    let purpose = 'सरकारी पात्रता सत्यापन';
    let req = true;

    if (typeof item === 'object' && item !== null) {
      rawName = item.accepts?.[0] || item.notes || item.purpose || JSON.stringify(item);
      if (item.purpose) purpose = String(item.purpose).replace(/_/g, ' ');
      if (item.required !== undefined) req = Boolean(item.required);
    } else {
      rawName = String(item);
    }

    const info = getDocumentTypeInfo(rawName);

    // Contextual purpose description based on detected document key
    if (info.key === 'aadhaar_card') {
      purpose = 'पहचान एवं स्थायी पता प्रमाण';
    } else if (info.key === 'income_certificate') {
      purpose = 'सक्षम राजस्व अधिकारी द्वारा जारी वार्षिक आय प्रमाण';
    } else if (info.key === 'ration_card') {
      purpose = 'गरीबी रेखा (BPL/AAY) परिवार पात्रता प्रमाण';
    } else if (info.key === 'bank_passbook') {
      purpose = 'डीबीटी (DBT) भुगतान हेतु बैंक खाता विवरण एवं IFSC कोड';
    } else if (info.key === 'disability_certificate') {
      purpose = 'मुख्य चिकित्सा अधिकारी (CMO) द्वारा 40%+ दिव्यांगता प्रमाण पत्र';
    } else if (info.key === 'khasra_khatauni') {
      purpose = 'कृषि भूमि स्वामित्व का राजस्व अभिलेख (रकबा विवरण)';
    } else if (info.key === 'caste_certificate') {
      purpose = 'आरक्षित सामाजिक श्रेणी प्रमाण (SC / ST / OBC)';
    } else if (info.key === 'death_certificate') {
      purpose = 'निराश्रित महिला / विधवा पेंशन पात्रता हेतु पति का मृत्यु प्रमाण';
    } else if (info.key === 'birth_certificate') {
      purpose = 'आयु एवं जन्म सत्यापन प्रमाण';
    } else if (info.key === 'academic_certificate') {
      purpose = 'शैक्षणिक पात्रता एवं न्यूनतम योग्यता प्रमाण';
    } else if (info.key === 'job_card') {
      purpose = 'मनरेगा पंजीकृत श्रमिक प्रमाण पत्र';
    } else if (info.key === 'kisan_credit_card') {
      purpose = 'संस्थागत कृषि ऋण खाता प्रमाण';
    } else if (info.key === 'voter_id') {
      purpose = 'निर्वाचन पहचान एवं निवास प्रमाण';
    }

    result.push({
      name: info.displayName,
      purpose,
      required: req,
      docTypeKey: info.key,
      docDisplayName: info.displayName,
      emoji: info.emoji,
    });
  }

  if (result.length === 0) {
    result.push(
      {
        name: 'आधार कार्ड (Aadhaar Card)',
        purpose: 'पहचान एवं निवास प्रमाण',
        required: true,
        docTypeKey: 'aadhaar_card',
        docDisplayName: 'आधार कार्ड (Aadhaar Card)',
        emoji: '🪪',
      },
      {
        name: 'बैंक पासबुक (Bank Passbook)',
        purpose: 'बैंक खाता व IFSC कोड',
        required: true,
        docTypeKey: 'bank_passbook',
        docDisplayName: 'बैंक पासबुक (Bank Passbook)',
        emoji: '🏦',
      }
    );
  }

  return result;
};

interface ApplicationChannelInfo {
  isOnline: boolean;
  isOfflineRequired: boolean;
  channelTitle: string;
  channelDescription: string;
  portalUrl?: string;
  steps: string[];
}

const determineApplicationChannel = (scheme: SchemeItem): ApplicationChannelInfo => {
  const proc = scheme.application_process;
  const url = scheme.application_url || scheme.source_url;
  let procStr = '';

  if (typeof proc === 'string') {
    procStr = proc.toLowerCase();
  } else if (typeof proc === 'object' && proc !== null) {
    procStr = JSON.stringify(proc).toLowerCase();
  }

  const mentionsOnline = procStr.includes('online') || Boolean(scheme.application_url);
  const mentionsOffline =
    procStr.includes('offline') ||
    procStr.includes('csc') ||
    procStr.includes('panchayat') ||
    procStr.includes('tehsil') ||
    procStr.includes('block office') ||
    procStr.includes('physical submission');

  // If strictly offline or primarily requires visiting an office
  if (mentionsOffline && !mentionsOnline) {
    return {
      isOnline: false,
      isOfflineRequired: true,
      channelTitle: '🏢 ऑफलाइन आवेदन (जन सेवा केंद्र / CSC या ब्लॉक कार्यालय)',
      channelDescription:
        'इस योजना का लाभ लेने के लिए आपको नजदीकी कॉमन सर्विस सेंटर (CSC), तहसील अथवा ब्लॉक कार्यालय में जाकर भौतिक रूप से कागज़ात जमा करने होंगे। केवल वेबसाइट से सीधे फॉर्म नहीं भरा जा सकता।',
      portalUrl: url,
      steps: [
        'नजदीकी जन सेवा केंद्र (CSC Kiosk) अथवा ब्लॉक विकास कार्यालय जाएं।',
        'अपने सभी मूल दस्तावेज़ (आधार, आय प्रमाण पत्र, बैंक पासबुक) साथ ले जाएं।',
        'अधिकारी द्वारा आवेदन फॉर्म सत्यापित करवाकर रसीद (Acknowledgment Slip) प्राप्त करें।',
      ],
    };
  }

  // If online form filling is supported
  if (mentionsOnline) {
    return {
      isOnline: true,
      isOfflineRequired: false,
      channelTitle: '🌐 ऑनलाइन आवेदन (वेबसाइट / पोर्टल द्वारा सीधे घर बैठे)',
      channelDescription:
        'आप इस योजना का लाभ घर बैठे आधिकारिक सरकारी वेबसाइट पर ऑनलाइन फॉर्म भरकर ले सकते हैं। यदि आपके पास कंप्यूटर या इंटरनेट नहीं है, तो आप नजदीकी जन सेवा केंद्र (CSC) जाकर भी इसे भरवा सकते हैं।',
      portalUrl: url,
      steps: [
        'आधिकारिक सरकारी पोर्टल खोलें और अपना मोबाइल नंबर व आधार दर्ज करें।',
        'ऑनलाइन आवेदन फॉर्म में अपनी व्यक्तिगत जानकारी भरें।',
        'वांछित दस्तावेज़ों की फोटो/पीडीएफ अपलोड करें और सबमिट करें।',
        'आवेदन क्रमांक (Application Reference Number) सुरक्षित रखें।',
      ],
    };
  }

  // Default balanced recommendation for rural citizens
  return {
    isOnline: true,
    isOfflineRequired: false,
    channelTitle: '🌐 ऑनलाइन पोर्टल अथवा 🏢 जन सेवा केंद्र (CSC)',
    channelDescription:
      'यह योजना सरकारी पोर्टल पर ऑनलाइन आवेदन की सुविधा देती है। ग्रामीण नागरिक नजदीकी जन सेवा केंद्र (CSC) जाकर भी ऑपरेटर से आसानी से फॉर्म भरवा सकते हैं।',
    portalUrl: url,
    steps: [
      'वेबसाइट पर ऑनलाइन फॉर्म भरें या नजदीकी जन सेवा केंद्र (CSC) जाएं।',
      'आवश्यक सरकारी दस्तावेज़ प्रस्तुत करें और पावती रसीद लें।',
    ],
  };
};

export const SchemeDetailScreen: React.FC<SchemeDetailScreenProps> = ({
  scheme,
  citizenProfile,
  verifiedDocuments = [],
  onNavigateToDocumentScan,
  onNavigateToReport,
  onBack,
}) => {
  const [isPlayingAudio, setIsPlayingAudio] = useState<boolean>(false);
  const [isLoadingAudio, setIsLoadingAudio] = useState<boolean>(false);

  const docList = getDocumentList(scheme.required_documents);
  const channelInfo = determineApplicationChannel(scheme);
  const benefitsText = formatBenefitsHindi(scheme.benefits, scheme.name);

  const isDisqualified =
    scheme.verdict === 'DOES_NOT_QUALIFY' ||
    Boolean(scheme.disqualification_reasons && scheme.disqualification_reasons.length > 0);

  const disqualificationReasonsList = getDisqualificationReasons(scheme, citizenProfile);

  // Build clean elaborate vernacular Hindi narrative description (No English jargon)
  const elaborateDescription = translateDescriptionToHindi(scheme);
  const hindiSchemeName = translateSchemeName(scheme.name);

  // Normalize verified document types
  const verifiedDocTypes = new Set(
    (verifiedDocuments || []).map((d) => (d.document_type || '').toLowerCase())
  );

  const isDocAlreadyVerified = (docName: string): boolean => {
    const info = getDocumentTypeInfo(docName);
    const targetKey = info.key.toLowerCase();

    return (verifiedDocuments || []).some((d) => {
      const dType = (d.document_type || '').toLowerCase();
      const extType = ((d.extracted_fields as any)?.document_type || '').toLowerCase();
      const extName = ((d.extracted_fields as any)?.document_name || '').toLowerCase();
      const targetNameLower = info.displayName.toLowerCase();

      if (dType === targetKey || extType === targetKey) return true;

      // Special alias checks
      if (targetKey === 'khasra_khatauni' && (dType === 'land_record' || dType.includes('khasra') || dType.includes('land'))) {
        return true;
      }
      if (targetKey === 'aadhaar_card' && (dType.includes('aadhaar') || dType === 'identity_proof')) {
        return true;
      }
      if (targetKey === 'ration_card' && (dType.includes('ration') || dType.includes('bpl'))) {
        return true;
      }
      if (targetKey === 'income_certificate' && (dType.includes('income') || dType.includes('आय'))) {
        return true;
      }
      if (targetKey === 'bank_passbook' && (dType.includes('bank') || dType.includes('passbook'))) {
        return true;
      }
      if (targetKey === 'caste_certificate' && (dType.includes('caste') || dType.includes('जाति'))) {
        return true;
      }
      if (targetKey === 'disability_certificate' && (dType.includes('disability') || dType.includes('divyang'))) {
        return true;
      }

      if (extName && (extName.includes(targetNameLower) || targetNameLower.includes(extName))) {
        return true;
      }
      return false;
    });
  };

  // Find remaining documents from the scheme that need verification
  const pendingSchemeDocs = docList.filter((d) => !isDocAlreadyVerified(d.name));

  // Determine next target document to scan:
  const nextTarget = pendingSchemeDocs[0];
  const targetDocType = nextTarget ? nextTarget.docTypeKey : 'income_certificate';
  const targetDocDisplayName = nextTarget ? nextTarget.name : 'आय प्रमाण पत्र (Income Certificate)';

  /**
   * Constructs the complete spoken script that reads:
   * 1. Clear disqualification announcement if citizen does not qualify
   * 2. Elaborate description of the scheme in Hindi
   * 3. Application channel (Online website vs CSC offline center)
   * 4. Required documents in bullet points
   */
  const buildSpokenSpeechText = (): string => {
    if (isDisqualified) {
      const topReasons = disqualificationReasonsList.slice(0, 2).join('। ');
      return `सूचना: ${hindiSchemeName}। आप इस योजना के लिए अपात्र हैं, इसलिए इसमें आवेदन नहीं कर सकते। अपात्रता के मुख्य कारण: ${topReasons}। योजना का विवरण: ${elaborateDescription.slice(0, 200)}।`;
    }

    // 1. Description
    const descSpeech = `${hindiSchemeName}। ${elaborateDescription.slice(0, 240)}।`;

    // 2. Channel info
    const channelSpeech = channelInfo.isOfflineRequired
      ? 'आवेदन का तरीका: इस योजना का लाभ लेने के लिए आपको नजदीकी कॉमन सर्विस सेंटर यानी जन सेवा केंद्र या ब्लॉक कार्यालय जाकर ऑफलाइन आवेदन करना होगा।'
      : 'आवेदन का तरीका: आप इस योजना का आवेदन वेबसाइट के जरिए ऑनलाइन घर बैठे कर सकते हैं, अथवा जन सेवा केंद्र जाकर भरवा सकते हैं।';

    // 3. Bullets of required documents
    const docBulletsSpeech =
      'इस योजना के लिए आवश्यक दस्तावेज़ इस प्रकार हैं: ' +
      docList
        .slice(0, 4)
        .map((d, idx) => `नंबर ${idx + 1}, ${d.name}`)
        .join('। ');

    return `${descSpeech} ${channelSpeech} ${docBulletsSpeech}। दस्तावेज़ स्कैन करने के लिए नीचे दिए गए बटन को दबाएं।`;
  };

  /**
   * Play the complete elaborate description and bulleted documents speech.
   */
  const handlePlayVoice = async () => {
    if (isPlayingAudio) {
      await stopTTSAudio();
      setIsPlayingAudio(false);
      return;
    }

    setIsLoadingAudio(true);
    try {
      const speechText = buildSpokenSpeechText();
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

  // Automatically speak out the elaborate description and documents when screen opens
  useEffect(() => {
    let isMounted = true;
    const autoPlaySpeech = async () => {
      try {
        setIsLoadingAudio(true);
        const speechText = buildSpokenSpeechText();
        const res = await fetch(API_ENDPOINTS.tts, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            text: speechText,
            return_format: 'base64',
            language_code: 'hi',
          }),
        });
        if (res.ok && isMounted) {
          const data = await res.json();
          if (data.audio_base64 && isMounted) {
            setIsLoadingAudio(false);
            setIsPlayingAudio(true);
            await playTTSAudio(data.audio_base64);
          }
        }
      } catch (_e) {
      } finally {
        if (isMounted) {
          setIsLoadingAudio(false);
          setIsPlayingAudio(false);
        }
      }
    };

    autoPlaySpeech();

    return () => {
      isMounted = false;
      stopTTSAudio();
    };
  }, [scheme.id]);

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" />

      {/* Tricolor Accent Header */}
      <View style={styles.topAccentBar}>
        <View style={[styles.tricolorSegment, { backgroundColor: '#FF9933' }]} />
        <View style={[styles.tricolorSegment, { backgroundColor: '#FFFFFF' }]} />
        <View style={[styles.tricolorSegment, { backgroundColor: '#138808' }]} />
      </View>

      {/* Top Navigation Bar */}
      <View style={styles.navBar}>
        <TouchableOpacity onPress={onBack} style={styles.backButton} accessibilityRole="button">
          <Text style={styles.backButtonText}>← वापस (Back)</Text>
        </TouchableOpacity>
        <Text style={styles.navBarTitle}>योजना संपूर्ण विवरण</Text>
        <TouchableOpacity onPress={onNavigateToReport} style={styles.reportNavButton}>
          <Text style={styles.reportNavButtonText}>📋 मेरी रिपोर्ट</Text>
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        {/* TOP ALERT BANNER WHEN CITIZEN DOES NOT QUALIFY */}
        {isDisqualified && (
          <View style={styles.disqualifiedBannerCard}>
            <View style={styles.disqualifiedHeaderRow}>
              <Text style={styles.disqualifiedBannerIcon}>🚫</Text>
              <View style={{ flex: 1 }}>
                <Text style={styles.disqualifiedBannerTitle}>
                  आप इस योजना के लिए अपात्र हैं (आवेदन नहीं कर सकते)
                </Text>
                <Text style={styles.disqualifiedBannerSubtitle}>
                  सरकारी नियमों के अनुसार आप इस योजना की आवश्यक पात्रता शर्तें पूरी नहीं करते हैं।
                </Text>
              </View>
            </View>
          </View>
        )}

        {/* MISSING FEATURES / DISQUALIFICATION REASONS SECTION */}
        {isDisqualified && disqualificationReasonsList.length > 0 && (
          <View style={styles.missingFeaturesCard}>
            <View style={styles.sectionHeaderRow}>
              <Text style={styles.sectionIcon}>⚠️</Text>
              <Text style={styles.sectionTitle}>
                अपात्रता के कारण / शर्तें जो पूरी नहीं हुईं (Missing Criteria)
              </Text>
            </View>
            <Text style={styles.missingFeaturesIntro}>
              निम्नलिखित कारणों से आप इस योजना का लाभ प्राप्त करने के पात्र नहीं हैं:
            </Text>

            <View style={styles.missingFeaturesList}>
              {disqualificationReasonsList.map((reasonText, idx) => (
                <View key={idx} style={styles.missingFeatureRow}>
                  <View style={styles.missingFeatureBullet}>
                    <Text style={styles.missingFeatureBulletText}>✕</Text>
                  </View>
                  <Text style={styles.missingFeatureText}>{reasonText}</Text>
                </View>
              ))}
            </View>
          </View>
        )}

        {/* Scheme Header Card */}
        <View style={styles.headerCard}>
          <View style={styles.metaRow}>
            <Text style={styles.metaBadge}>{translateCategory(scheme.category)}</Text>
            <Text style={styles.metaGovBadge}>{translateGov(scheme.government_name)}</Text>
          </View>
          <Text style={styles.schemeTitle}>{hindiSchemeName}</Text>
          {scheme.name ? (
            <Text style={styles.schemeSubTitleEng}>{scheme.name}</Text>
          ) : null}
          {scheme.verdict === 'QUALIFIES' ? (
            <View style={styles.verdictPillQualifies}>
              <Text style={styles.verdictPillTextQualifies}>✓ आप इस योजना के लिए पूरी तरह पात्र हैं</Text>
            </View>
          ) : isDisqualified ? (
            <View style={styles.verdictPillDisqualified}>
              <Text style={styles.verdictPillTextDisqualified}>✕ आप इस योजना के लिए पात्र नहीं हैं (अपात्र)</Text>
            </View>
          ) : (
            <View style={styles.verdictPillNeedsInfo}>
              <Text style={styles.verdictPillTextNeedsInfo}>⏳ दस्तावेज़ सत्यापन उपरांत अंतिम निर्णय</Text>
            </View>
          )}
        </View>

        {/* Audio Speech Announcement Box */}
        <View style={styles.audioCard}>
          <View style={styles.audioRow}>
            <Text style={styles.audioIcon}>{isPlayingAudio ? '🔊' : '🔈'}</Text>
            <View style={styles.audioTextCol}>
              <Text style={styles.audioHeading}>
                {isPlayingAudio ? '🔊 योजनावाणी विवरण व दस्तावेज़ सुना रही है...' : '🔊 आवाज़ में पूरा विवरण सुनें'}
              </Text>
              <Text style={styles.audioSubtext}>
                योजना का विवरण, आवेदन का तरीका और आवश्यक दस्तावेज़ बुलेट में सुनें।
              </Text>
            </View>
          </View>
          <TouchableOpacity
            style={[styles.playAudioButton, isPlayingAudio && styles.playAudioButtonActive]}
            onPress={handlePlayVoice}
            disabled={isLoadingAudio}
            accessibilityRole="button"
          >
            {isLoadingAudio ? (
              <ActivityIndicator size="small" color="#FFFFFF" />
            ) : (
              <Text style={styles.playAudioButtonText}>
                {isPlayingAudio ? '⏹️ बोलना बंद करें' : '🔁 आवाज़ में दोबारा सुनें (Listen Again)'}
              </Text>
            )}
          </TouchableOpacity>
        </View>

        {/* Section 1: Elaborate Scheme Description */}
        <View style={styles.sectionCard}>
          <View style={styles.sectionHeaderRow}>
            <Text style={styles.sectionIcon}>📖</Text>
            <Text style={styles.sectionTitle}>योजना का विस्तृत विवरण</Text>
          </View>
          <Text style={styles.descriptionText}>{elaborateDescription}</Text>
        </View>

        {/* Section 2: Financial Benefits */}
        <View style={styles.sectionCard}>
          <View style={styles.sectionHeaderRow}>
            <Text style={styles.sectionIcon}>💰</Text>
            <Text style={styles.sectionTitle}>आर्थिक लाभ व सरकारी सहायता</Text>
          </View>
          <View style={styles.benefitContainer}>
            <Text style={styles.benefitText}>{benefitsText}</Text>
          </View>
        </View>

        {/* Section 3: Online vs. CSC Offline Centers (MANDATORY REQUIREMENT) */}
        <View
          style={[
            styles.sectionCard,
            channelInfo.isOfflineRequired ? styles.sectionCardOffline : styles.sectionCardOnline,
          ]}
        >
          <View style={styles.sectionHeaderRow}>
            <Text style={styles.sectionIcon}>{channelInfo.isOfflineRequired ? '🏢' : '🌐'}</Text>
            <Text style={styles.sectionTitle}>आवेदन का माध्यम (ऑनलाइन या सीएससी केंद्र?)</Text>
          </View>

          {/* Mode Pill Badge */}
          <View
            style={[
              styles.channelBadge,
              channelInfo.isOfflineRequired ? styles.channelBadgeOffline : styles.channelBadgeOnline,
            ]}
          >
            <Text
              style={[
                styles.channelBadgeText,
                channelInfo.isOfflineRequired ? styles.channelBadgeTextOffline : styles.channelBadgeTextOnline,
              ]}
            >
              {channelInfo.channelTitle}
            </Text>
          </View>

          <Text style={styles.channelDescriptionText}>{channelInfo.channelDescription}</Text>

          {/* Step by step process */}
          <View style={styles.stepsContainer}>
            <Text style={styles.stepsHeading}>आवेदन कैसे पूरा करें:</Text>
            {channelInfo.steps.map((st, idx) => (
              <View key={idx} style={styles.stepRow}>
                <View style={styles.stepNumberBadge}>
                  <Text style={styles.stepNumberText}>{idx + 1}</Text>
                </View>
                <Text style={styles.stepText}>{st}</Text>
              </View>
            ))}
          </View>

          {/* Action button for Online Portal Link if available */}
          {channelInfo.portalUrl ? (
            <TouchableOpacity
              style={styles.portalButton}
              onPress={() => Linking.openURL(channelInfo.portalUrl!).catch(() => {})}
            >
              <Text style={styles.portalButtonText}>🌐 आधिकारिक सरकारी पोर्टल खोलें (Visit Portal)</Text>
            </TouchableOpacity>
          ) : null}

          {/* CSC Helpline & Location Assistance */}
          <View style={styles.cscHelpBox}>
            <Text style={styles.cscHelpTitle}>📍 नजदीकी कॉमन सर्विस सेंटर (CSC सहायता केंद्र):</Text>
            <Text style={styles.cscHelpLine}>• केंद्र: हैदरगढ़ डिजिटल सेवा केंद्र (तहसील परिसर के पास)</Text>
            <Text style={styles.cscHelpLine}>• हेल्पलाइन टोल-फ्री: 1800-3000-3468</Text>
            <Text style={styles.cscHelpLine}>• समय: सुबह 9:00 बजे से शाम 5:00 बजे तक</Text>
          </View>
        </View>

        {/* Section 4: Required Documents in Bullets (MANDATORY REQUIREMENT) */}
        <View style={styles.sectionCard}>
          <View style={styles.sectionHeaderRow}>
            <Text style={styles.sectionIcon}>📄</Text>
            <Text style={styles.sectionTitle}>आवश्यक दस्तावेज़ (Required Documents)</Text>
          </View>
          <Text style={styles.docIntroText}>
            इस योजना में आवेदन करने हेतु निम्नलिखित दस्तावेज़ों की आवश्यकता होगी:
          </Text>

          {docList.map((doc, idx) => {
            const isVerified = isDocAlreadyVerified(doc.name);
            return (
              <View key={idx} style={styles.docBulletItem}>
                <View style={styles.docBulletIcon}>
                  <Text style={[styles.bulletSymbol, isVerified && { color: '#34D399' }]}>
                    {isVerified ? '✓' : '•'}
                  </Text>
                </View>
                <View style={styles.docBulletContent}>
                  <View style={styles.docNameRow}>
                    <Text style={styles.docBulletName}>{doc.name}</Text>
                    {isVerified ? (
                      <View style={styles.verifiedBadgeRow}>
                        <Text style={styles.verifiedBadgeText}>✓ सत्यापित (Verified)</Text>
                      </View>
                    ) : doc.required ? (
                      <View style={styles.mandatoryBadge}>
                        <Text style={styles.mandatoryBadgeText}>अनिवार्य (सत्यापन शेष)</Text>
                      </View>
                    ) : null}
                  </View>
                  <Text style={styles.docBulletPurpose}>प्रयोजन: {doc.purpose}</Text>
                  {!isVerified && (
                    <TouchableOpacity
                      style={styles.scanDirectButton}
                      onPress={() => onNavigateToDocumentScan(doc.docTypeKey, doc.name)}
                      activeOpacity={0.8}
                      accessibilityRole="button"
                    >
                      <Text style={styles.scanDirectButtonText}>📸 यह दस्तावेज़ स्कैन करें</Text>
                    </TouchableOpacity>
                  )}
                </View>
              </View>
            );
          })}
        </View>

        {/* Section 5: Document Scanning CTA or Return to Eligible Schemes */}
        {isDisqualified ? (
          <View style={styles.disqualifiedCtaCard}>
            <Text style={styles.disqualifiedCtaIcon}>ℹ️</Text>
            <Text style={styles.disqualifiedCtaHeading}>अन्य पात्र योजनाओं की सूची देखें</Text>
            <Text style={styles.disqualifiedCtaSubtext}>
              चूंकि आप इस योजना के नियमों को पूरा नहीं करते हैं, इसलिए कृपया वापस जाकर उन योजनाओं को देखें जिनमें आप पात्र (Eligible) हैं।
            </Text>
            <TouchableOpacity
              style={styles.backToEligibleButton}
              onPress={onBack}
              accessibilityRole="button"
            >
              <Text style={styles.backToEligibleButtonText}>← वापस जाएं और पात्र योजनाएं देखें</Text>
            </TouchableOpacity>
          </View>
        ) : (
          <View style={styles.scanCtaCard}>
            <Text style={styles.scanCtaIcon}>{pendingSchemeDocs.length === 0 ? '🎉' : '📸'}</Text>
            <Text style={styles.scanCtaHeading}>
              {pendingSchemeDocs.length === 0
                ? '✓ इस योजना के सभी आवश्यक दस्तावेज़ सत्यापित हैं!'
                : 'दस्तावेज़ स्कैन करें और अपनी प्रोफाइल रिपोर्ट बनाएं'}
            </Text>
            <Text style={styles.scanCtaSubtext}>
              {pendingSchemeDocs.length === 0
                ? 'इस योजना के सभी ज़रूरी कागज़ात Tesseract OCR द्वारा सफलतापूर्वक प्रमाणित कर लिए गए हैं।'
                : 'उपरोक्त आवश्यक दस्तावेज़ की फोटो खींचकर Tesseract OCR द्वारा तुरंत सत्यापन करवाएं। सत्यापन के बाद आपका संपूर्ण नागरिक व्यक्तिगत विवरण तैयार होकर आपको दिखाई देगा।'}
            </Text>

            {pendingSchemeDocs.length > 0 ? (
              <TouchableOpacity
                style={styles.scanPrimaryButton}
                onPress={() => onNavigateToDocumentScan(targetDocType, targetDocDisplayName)}
                activeOpacity={0.8}
                accessibilityRole="button"
              >
                <Text style={styles.scanPrimaryButtonText}>
                  {`📸 अगला आवश्यक दस्तावेज़ स्कैन करें: ${targetDocDisplayName}`}
                </Text>
              </TouchableOpacity>
            ) : null}

            <TouchableOpacity
              style={styles.viewReportSecondaryButton}
              onPress={onNavigateToReport}
              activeOpacity={0.8}
            >
              <Text style={styles.viewReportSecondaryText}>📋 मेरी संपूर्ण व्यक्तिगत रिपोर्ट देखें</Text>
            </TouchableOpacity>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
};

// -----------------------------------------------------------------------------
// HIGH-CONTRAST ACCESSIBLE STYLES
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
  backButton: {
    paddingVertical: 6,
    paddingHorizontal: 12,
    backgroundColor: '#1E3550',
    borderRadius: 8,
  },
  backButtonText: {
    color: '#81C784',
    fontSize: 14,
    fontWeight: '700',
  },
  navBarTitle: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '800',
  },
  reportNavButton: {
    paddingVertical: 6,
    paddingHorizontal: 10,
    backgroundColor: '#0D47A1',
    borderRadius: 8,
  },
  reportNavButtonText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '700',
  },
  scrollContent: {
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 40,
  },
  headerCard: {
    backgroundColor: '#13283E',
    borderRadius: 14,
    padding: 16,
    marginBottom: 14,
    borderWidth: 1.5,
    borderColor: '#1E88E5',
  },
  metaRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: 10,
    gap: 8,
  },
  metaBadge: {
    fontSize: 12,
    color: '#90CAF9',
    backgroundColor: '#0D2D4B',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
    fontWeight: '600',
  },
  metaGovBadge: {
    fontSize: 12,
    color: '#A5D6A7',
    backgroundColor: '#103820',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
    fontWeight: '600',
  },
  schemeTitle: {
    fontSize: 20,
    fontWeight: '800',
    color: '#FFFFFF',
    lineHeight: 28,
    marginBottom: 4,
  },
  schemeSubTitleEng: {
    fontSize: 14,
    color: '#94A3B8',
    marginBottom: 12,
  },
  verdictPillQualifies: {
    backgroundColor: '#1B5E20',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    alignSelf: 'flex-start',
  },
  verdictPillTextQualifies: {
    color: '#C8E6C9',
    fontSize: 14,
    fontWeight: '700',
  },
  verdictPillNeedsInfo: {
    backgroundColor: '#E65100',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    alignSelf: 'flex-start',
  },
  verdictPillTextNeedsInfo: {
    color: '#FFE0B2',
    fontSize: 14,
    fontWeight: '700',
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
  audioTextCol: {
    flex: 1,
  },
  audioHeading: {
    fontSize: 15,
    fontWeight: '800',
    color: '#FFD54F',
    marginBottom: 4,
  },
  audioSubtext: {
    fontSize: 13,
    color: '#CFD8DC',
    lineHeight: 18,
  },
  playAudioButton: {
    backgroundColor: '#FF9933',
    paddingVertical: 12,
    borderRadius: 10,
    alignItems: 'center',
  },
  playAudioButtonActive: {
    backgroundColor: '#D32F2F',
  },
  playAudioButtonText: {
    color: '#0A141E',
    fontSize: 15,
    fontWeight: '800',
  },
  sectionCard: {
    backgroundColor: '#112233',
    borderRadius: 14,
    padding: 16,
    marginBottom: 14,
    borderWidth: 1,
    borderColor: '#1E3A58',
  },
  sectionCardOnline: {
    borderColor: '#2E7D32',
    borderWidth: 1.5,
  },
  sectionCardOffline: {
    borderColor: '#FF8F00',
    borderWidth: 1.5,
  },
  sectionHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  sectionIcon: {
    fontSize: 20,
    marginRight: 8,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: '#FFFFFF',
    letterSpacing: 0.2,
  },
  descriptionText: {
    fontSize: 15,
    color: '#ECEFF1',
    lineHeight: 24,
  },
  benefitContainer: {
    backgroundColor: '#0D3820',
    borderRadius: 10,
    padding: 12,
    borderLeftWidth: 4,
    borderLeftColor: '#4CAF50',
  },
  benefitText: {
    fontSize: 15,
    color: '#E8F5E9',
    lineHeight: 23,
    fontWeight: '600',
  },
  channelBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    alignSelf: 'flex-start',
    marginBottom: 10,
  },
  channelBadgeOnline: {
    backgroundColor: '#1B5E20',
  },
  channelBadgeOffline: {
    backgroundColor: '#E65100',
  },
  channelBadgeText: {
    fontSize: 13,
    fontWeight: '800',
  },
  channelBadgeTextOnline: {
    color: '#A5D6A7',
  },
  channelBadgeTextOffline: {
    color: '#FFE0B2',
  },
  channelDescriptionText: {
    fontSize: 14,
    color: '#CFD8DC',
    lineHeight: 21,
    marginBottom: 12,
  },
  stepsContainer: {
    marginTop: 8,
    marginBottom: 12,
  },
  stepsHeading: {
    fontSize: 14,
    fontWeight: '700',
    color: '#90CAF9',
    marginBottom: 8,
  },
  stepRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  stepNumberBadge: {
    width: 22,
    height: 22,
    borderRadius: 11,
    backgroundColor: '#1E88E5',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
    marginTop: 2,
  },
  stepNumberText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '800',
  },
  stepText: {
    flex: 1,
    fontSize: 14,
    color: '#ECEFF1',
    lineHeight: 20,
  },
  portalButton: {
    backgroundColor: '#1565C0',
    paddingVertical: 12,
    borderRadius: 10,
    alignItems: 'center',
    marginBottom: 12,
  },
  portalButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '800',
  },
  cscHelpBox: {
    backgroundColor: '#1B2C3E',
    borderRadius: 10,
    padding: 12,
    borderLeftWidth: 3,
    borderLeftColor: '#FFB300',
  },
  cscHelpTitle: {
    fontSize: 13,
    fontWeight: '800',
    color: '#FFD54F',
    marginBottom: 4,
  },
  cscHelpLine: {
    fontSize: 13,
    color: '#B0BEC5',
    lineHeight: 19,
  },
  docIntroText: {
    fontSize: 14,
    color: '#B0BEC5',
    marginBottom: 12,
  },
  docBulletItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#152538',
    borderRadius: 10,
    padding: 12,
    marginBottom: 8,
    borderLeftWidth: 3,
    borderLeftColor: '#64B5F6',
  },
  docBulletIcon: {
    marginRight: 10,
    marginTop: -2,
  },
  bulletSymbol: {
    fontSize: 22,
    color: '#64B5F6',
    fontWeight: '900',
  },
  docBulletContent: {
    flex: 1,
  },
  docNameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  docBulletName: {
    fontSize: 15,
    fontWeight: '700',
    color: '#FFFFFF',
    flex: 1,
  },
  mandatoryBadge: {
    backgroundColor: '#B71C1C',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    marginLeft: 6,
  },
  mandatoryBadgeText: {
    color: '#FFCDD2',
    fontSize: 11,
    fontWeight: '700',
  },
  verifiedBadgeRow: {
    backgroundColor: '#065F46',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 6,
    marginLeft: 6,
  },
  verifiedBadgeText: {
    color: '#6EE7B7',
    fontSize: 11,
    fontWeight: '800',
  },
  docBulletPurpose: {
    fontSize: 13,
    color: '#90A4AE',
    lineHeight: 18,
  },
  scanDirectButton: {
    backgroundColor: '#0F766E',
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 8,
    alignSelf: 'flex-start',
    marginTop: 8,
    borderWidth: 1,
    borderColor: '#2DD4BF',
  },
  scanDirectButtonText: {
    color: '#F0FDFA',
    fontSize: 12,
    fontWeight: '800',
  },
  scanCtaCard: {
    backgroundColor: '#162F4A',
    borderRadius: 14,
    padding: 18,
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#4CAF50',
    marginTop: 8,
  },
  scanCtaIcon: {
    fontSize: 36,
    marginBottom: 8,
  },
  scanCtaHeading: {
    fontSize: 17,
    fontWeight: '800',
    color: '#FFFFFF',
    textAlign: 'center',
    marginBottom: 6,
  },
  scanCtaSubtext: {
    fontSize: 13,
    color: '#CFD8DC',
    textAlign: 'center',
    lineHeight: 19,
    marginBottom: 16,
  },
  scanPrimaryButton: {
    backgroundColor: '#138808',
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderRadius: 10,
    width: '100%',
    alignItems: 'center',
    marginBottom: 10,
  },
  scanPrimaryButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '800',
  },
  viewReportSecondaryButton: {
    backgroundColor: '#1E3550',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 10,
    width: '100%',
    alignItems: 'center',
  },
  viewReportSecondaryText: {
    color: '#90CAF9',
    fontSize: 14,
    fontWeight: '700',
  },

  // Disqualified Alert Banner at Top
  disqualifiedBannerCard: {
    backgroundColor: '#3A0E12',
    borderRadius: 14,
    padding: 16,
    marginBottom: 16,
    borderWidth: 2,
    borderColor: '#EF4444',
  },
  disqualifiedHeaderRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  disqualifiedBannerIcon: {
    fontSize: 32,
    marginRight: 14,
    marginTop: 2,
  },
  disqualifiedBannerTitle: {
    fontSize: 18,
    fontWeight: '900',
    color: '#FF6B6B',
    lineHeight: 24,
    marginBottom: 4,
  },
  disqualifiedBannerSubtitle: {
    fontSize: 14,
    color: '#FFCDD2',
    lineHeight: 20,
    fontWeight: '500',
  },

  // Missing Features / Disqualification Criteria Section
  missingFeaturesCard: {
    backgroundColor: '#261214',
    borderRadius: 14,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1.5,
    borderColor: '#F87171',
  },
  missingFeaturesIntro: {
    fontSize: 14,
    color: '#FFA8A8',
    fontWeight: '600',
    marginBottom: 12,
  },
  missingFeaturesList: {
    gap: 10,
  },
  missingFeatureRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#3E161B',
    padding: 10,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#7F1D1D',
  },
  missingFeatureBullet: {
    width: 22,
    height: 22,
    borderRadius: 11,
    backgroundColor: '#EF4444',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
    marginTop: 2,
  },
  missingFeatureBulletText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '900',
  },
  missingFeatureText: {
    flex: 1,
    fontSize: 15,
    color: '#FFE4E6',
    fontWeight: '600',
    lineHeight: 22,
  },

  // Verdict Pill Disqualified
  verdictPillDisqualified: {
    alignSelf: 'flex-start',
    backgroundColor: '#7F1D1D',
    paddingVertical: 5,
    paddingHorizontal: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#EF4444',
    marginTop: 4,
  },
  verdictPillTextDisqualified: {
    color: '#FEE2E2',
    fontSize: 14,
    fontWeight: '800',
  },

  // Back to Eligible Schemes Button
  disqualifiedCtaCard: {
    backgroundColor: '#1E293B',
    borderRadius: 14,
    padding: 18,
    alignItems: 'center',
    borderWidth: 1.5,
    borderColor: '#475569',
    marginBottom: 20,
  },
  disqualifiedCtaIcon: {
    fontSize: 32,
    marginBottom: 8,
  },
  disqualifiedCtaHeading: {
    fontSize: 17,
    fontWeight: '800',
    color: '#F8FAFC',
    marginBottom: 6,
    textAlign: 'center',
  },
  disqualifiedCtaSubtext: {
    fontSize: 13,
    color: '#94A3B8',
    textAlign: 'center',
    lineHeight: 20,
    marginBottom: 16,
  },
  backToEligibleButton: {
    backgroundColor: '#2563EB',
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderRadius: 10,
    width: '100%',
    alignItems: 'center',
  },
  backToEligibleButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '800',
  },
});

