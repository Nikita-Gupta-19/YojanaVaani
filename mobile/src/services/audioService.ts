import { NativeModules, Platform } from 'react-native';

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

