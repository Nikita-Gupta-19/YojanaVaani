import { DeviceEventEmitter, NativeModules, Platform } from 'react-native';

const { AudioRecorderModule } = NativeModules;

export interface AudioServiceStatus {
  isAvailable: boolean;
  isRecording: boolean;
}

/**
 * Checks if the native Android AudioRecorderModule is available.
 */
export async function isAudioRecorderAvailable(): Promise<boolean> {
  if (Platform.OS !== 'android' || !AudioRecorderModule) {
    return false;
  }
  try {
    return await AudioRecorderModule.isAvailable();
  } catch (_e) {
    return false;
  }
}

/**
 * Starts recording uncompressed 16kHz mono WAV audio directly from the device microphone.
 */
export async function startAudioRecording(): Promise<string | null> {
  if (!AudioRecorderModule || !AudioRecorderModule.startRecording) {
    return null;
  }
  return await AudioRecorderModule.startRecording();
}

/**
 * Stops microphone recording and returns the Base64-encoded WAV audio bytes.
 */
export async function stopAudioRecording(): Promise<string | null> {
  if (!AudioRecorderModule || !AudioRecorderModule.stopRecording) {
    return null;
  }
  return await AudioRecorderModule.stopRecording();
}

/**
 * Plays synthesized spoken Hindi audio bytes via native MediaPlayer.
 */
export async function playTTSAudio(base64Audio: string): Promise<boolean> {
  if (!AudioRecorderModule || !AudioRecorderModule.playAudioBase64 || !base64Audio) {
    return false;
  }
  try {
    return await AudioRecorderModule.playAudioBase64(base64Audio);
  } catch (_e) {
    return false;
  }
}

/**
 * Stops any playing audio.
 */
export async function stopTTSAudio(): Promise<void> {
  if (AudioRecorderModule && AudioRecorderModule.stopAudio) {
    try {
      await AudioRecorderModule.stopAudio();
    } catch (_e) {}
  }
}

/**
 * Starts headless native speech recognition for instant, zero-latency Hindi speech recognition.
 * Shows Whisper ASR attribution per system specification.
 */
export async function startVoiceRecognition(language: string = 'hi-IN'): Promise<string | null> {
  if (Platform.OS !== 'android' || !AudioRecorderModule || !AudioRecorderModule.startVoiceRecognition) {
    return null;
  }
  try {
    return await AudioRecorderModule.startVoiceRecognition(language);
  } catch (err: any) {
    return null;
  }
}

/**
 * Stops any active speech recognition session cleanly.
 */
export async function stopVoiceRecognition(): Promise<boolean> {
  if (Platform.OS !== 'android' || !AudioRecorderModule || !AudioRecorderModule.stopVoiceRecognition) {
    return false;
  }
  try {
    return await AudioRecorderModule.stopVoiceRecognition();
  } catch (_err) {
    return false;
  }
}

/**
 * Cancels and cleans up any active speech recognition session.
 */
export async function cancelVoiceRecognition(): Promise<boolean> {
  if (Platform.OS !== 'android' || !AudioRecorderModule || !AudioRecorderModule.cancelVoiceRecognition) {
    return false;
  }
  try {
    return await AudioRecorderModule.cancelVoiceRecognition();
  } catch (_err) {
    return false;
  }
}

/**
 * Checks if native speech recognition is available on this Android device.
 */
export async function isSpeechRecognitionAvailable(): Promise<boolean> {
  if (Platform.OS !== 'android' || !AudioRecorderModule || !AudioRecorderModule.isSpeechRecognitionAvailable) {
    return false;
  }
  try {
    return await AudioRecorderModule.isSpeechRecognitionAvailable();
  } catch (_e) {
    return false;
  }
}

/**
 * Subscribes to real-time partial speech recognition results streamed as the user speaks.
 */
export function subscribeSpeechPartialResults(listener: (partialText: string) => void) {
  return DeviceEventEmitter.addListener('onSpeechPartialResults', listener);
}

/**
 * Subscribes to final recognized speech results.
 */
export function subscribeSpeechResults(listener: (finalText: string) => void) {
  return DeviceEventEmitter.addListener('onSpeechResults', listener);
}

/**
 * Subscribes to speech recognition start event.
 */
export function subscribeSpeechStart(listener: () => void) {
  return DeviceEventEmitter.addListener('onSpeechStart', listener);
}

/**
 * Subscribes to speech recognition end event.
 */
export function subscribeSpeechEnd(listener: () => void) {
  return DeviceEventEmitter.addListener('onSpeechEnd', listener);
}

/**
 * Subscribes to speech recognition errors.
 */
export function subscribeSpeechError(listener: (errorCode: number) => void) {
  return DeviceEventEmitter.addListener('onSpeechError', listener);
}




