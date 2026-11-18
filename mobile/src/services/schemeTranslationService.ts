/**
 * Comprehensive Hindi Scheme Translation Service for YojanaVaani.
 * Ensures ALL government schemes are displayed with proper Hindi titles
 * and dual-script accessibility for rural and low-literacy citizens.
 */

import schemeTranslationsData from './schemeTranslations.json';

const SCHEME_DICT: Record<string, string> = schemeTranslationsData as Record<string, string>;

// Curated high-priority vernacular names
export const CURATED_HINDI_NAMES: Record<string, string> = {
  'pm-yasasvi': 'पीएम-यशस्वी: छात्रवृत्ति योजना (PM-YASASVI)',
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
  'surgical grant for the prevention of disability': 'दिव्यांगता रोकथाम हेतु शल्य चिकित्सा अनुदान योजना',
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
  'motorized tricycle': 'दिव्यांगजन मोटराइज्ड ट्राइसाइकिल सहायता योजना',
  'artificial limbs': 'दिव्यांगजन कृत्रिम अंग एवं सहायक उपकरण योजना',
  'national family benefit': 'राष्ट्रीय पारिवारिक लाभ योजना (मृत्यु उपरांत आर्थिक सहायता)',
  'kanya sumangala': 'मुख्यमंत्री कन्या सुमंगला योजना',
  'shadi anudan': 'विवाह अनुदान योजना (गरीब कन्या विवाह सहायता)',
};

const KEYWORD_TRANSLATIONS: [RegExp, string][] = [
  [/\bSurgical Grant For The Prevention Of Disability\b/gi, 'दिव्यांगता रोकथाम शल्य चिकित्सा अनुदान'],
  [/\bSurgical Grant\b/gi, 'शल्य चिकित्सा अनुदान'],
  [/\bPrevention Of Disability\b/gi, 'दिव्यांगता रोकथाम'],
  [/\bMotorized Tricycle\b/gi, 'मोटराइज्ड ट्राइसाइकिल सहायता'],
  [/\bArtificial Limbs?\b/gi, 'कृत्रिम अंग एवं उपकरण सहायता'],
  [/\bNational Family Benefit\b/gi, 'राष्ट्रीय पारिवारिक लाभ योजना'],
  [/\bFamily Benefit\b/gi, 'पारिवारिक लाभ सहायता'],
  [/\bChief Minister\b/gi, 'मुख्यमंत्री'],
  [/\bPrime Minister\b/gi, 'प्रधानमंत्री'],
  [/\bPre-Matric Scholarship\b/gi, 'प्री-मैट्रिक छात्रवृत्ति'],
  [/\bPost-Matric Scholarship\b/gi, 'पोस्ट-मैट्रिक छात्रवृत्ति'],
  [/\bScholarship\b/gi, 'छात्रवृत्ति योजना'],
  [/\bFellowship\b/gi, 'फेलोशिप योजना'],
  [/\bFinancial Assistance\b/gi, 'आर्थिक सहायता योजना'],
  [/\bAssistance\b/gi, 'सहायता योजना'],
  [/\bPension\b/gi, 'पेंशन योजना'],
  [/\bOld Age\b/gi, 'वृद्धावस्था'],
  [/\bWidow\b/gi, 'विधवा'],
  [/\bDestitute\b/gi, 'निराश्रित'],
  [/\bDisability\b/gi, 'दिव्यांगजन'],
  [/\bDisabled\b/gi, 'दिव्यांग'],
  [/\bConstruction Workers?\b/gi, 'निर्माण श्रमिक'],
  [/\bUnorganized Workers?\b/gi, 'असंगठित श्रमिक'],
  [/\bHousing\b/gi, 'आवास योजना'],
  [/\bMaternity\b/gi, 'मातृत्व सहायता'],
  [/\bMarriage\b/gi, 'विवाह अनुदान'],
  [/\bLoan\b/gi, 'ऋण सहायता'],
  [/\bSubsidy\b/gi, 'सब्सिडी (छूट)'],
  [/\bEducation\b/gi, 'शिक्षा'],
  [/\bSkill Development\b/gi, 'कौशल विकास'],
  [/\bHealth\b/gi, 'स्वास्थ्य'],
  [/\bFarmers?\b/gi, 'किसान'],
  [/\bAgriculture\b/gi, 'कृषि'],
  [/\bStudents?\b/gi, 'विद्यार्थी'],
  [/\bGirls?\b/gi, 'बालिका'],
  [/\bWomen\b/gi, 'महिला'],
  [/\bMinorities\b/gi, 'अल्पसंख्यक'],
  [/\bInsurance\b/gi, 'बीमा योजना'],
  [/\bNational\b/gi, 'राष्ट्रीय'],
  [/\bState\b/gi, 'राज्य'],
  [/\bScheme\b/gi, 'योजना'],
  [/\bYojna\b/gi, 'योजना'],
  [/\bYojana\b/gi, 'योजना'],
  [/\bProgramme\b/gi, 'कार्यक्रम'],
  [/\bProgram\b/gi, 'कार्यक्रम'],
  [/\bFree\b/gi, 'निःशुल्क'],
  [/\bTools?\b/gi, 'कार्य उपकरण'],
  [/\bMedical\b/gi, 'चिकित्सा'],
  [/\bSolar Pump\b/gi, 'सौर ऊर्जा पंप'],
  [/\bSolar\b/gi, 'सौर ऊर्जा'],
  [/\bGrant\b/gi, 'अनुदान'],
  [/\bIncentive\b/gi, 'प्रोत्साहन'],
  [/\bSelf Employment\b/gi, 'स्वरोजगार'],
  [/\bEmployment\b/gi, 'रोजगार'],
  [/\bFor\b/gi, 'हेतु'],
  [/\bAnd\b/gi, 'एवं'],
  [/\bOf\b/gi, ''],
  [/\bThe\b/gi, ''],
];

/**
 * Translates any scheme name reliably to Hindi.
 * Guaranteed to return Hindi text for all 270 schemes and dynamic RAG schemes.
 */
export function translateSchemeName(name: string): string {
  if (!name || !name.trim()) {
    return 'सरकारी कल्याणकारी योजना';
  }

  const trimmed = name.trim();
  const nameLower = trimmed.toLowerCase();

  // 1. Check exact or trimmed key in precomputed 270-scheme dictionary
  if (SCHEME_DICT[trimmed]) {
    return SCHEME_DICT[trimmed];
  }

  // 2. Check curated key inclusions
  for (const [key, hindi] of Object.entries(CURATED_HINDI_NAMES)) {
    if (nameLower.includes(key)) {
      return hindi;
    }
  }

  // 3. Check partial matches in SCHEME_DICT
  for (const [engKey, hindiVal] of Object.entries(SCHEME_DICT)) {
    if (nameLower.includes(engKey.toLowerCase()) || engKey.toLowerCase().includes(nameLower)) {
      return hindiVal;
    }
  }

  // 4. Keyword-level translation
  let translated = trimmed;
  for (const [pattern, hindiSub] of KEYWORD_TRANSLATIONS) {
    translated = translated.replace(pattern, hindiSub);
  }

  // Clean up duplicate "योजना"
  translated = translated.replace(/(योजना\s*)+/g, 'योजना ').trim();

  // If still purely English (no Devanagari characters), prepend Hindi category label
  if (!/[\u0900-\u097F]/.test(translated)) {
    return `सरकारी जनकल्याणकारी योजना: ${trimmed}`;
  }

  return translated;
}
