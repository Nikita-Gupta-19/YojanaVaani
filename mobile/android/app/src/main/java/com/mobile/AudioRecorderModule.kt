package com.mobile

import android.annotation.SuppressLint
import android.app.Activity
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.media.AudioAttributes
import android.media.AudioFocusRequest
import android.media.AudioFormat
import android.media.AudioManager
import android.media.AudioRecord
import android.media.MediaPlayer
import android.media.MediaRecorder
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.util.Base64
import com.facebook.react.bridge.ActivityEventListener
import com.facebook.react.bridge.Promise
import com.facebook.react.bridge.ReactApplicationContext
import com.facebook.react.bridge.ReactContextBaseJavaModule
import com.facebook.react.bridge.ReactMethod
import com.facebook.react.modules.core.DeviceEventManagerModule
import java.io.File
import java.io.FileOutputStream
import java.io.RandomAccessFile
import java.util.concurrent.atomic.AtomicBoolean

class AudioRecorderModule(private val reactContext: ReactApplicationContext) :
    ReactContextBaseJavaModule(reactContext), ActivityEventListener {

    private var audioRecord: AudioRecord? = null
    private var recordingThread: Thread? = null
    private val isRecording = AtomicBoolean(false)
    private var outputFile: File? = null
    private var mediaPlayer: MediaPlayer? = null

    private var speechRecognizer: SpeechRecognizer? = null
    private var activeSpeechPromise: Promise? = null
    private var lastPartialSpeechText: String = ""

    init {
        reactContext.addActivityEventListener(this)
    }

    override fun getName(): String = "AudioRecorderModule"

    private fun sendEvent(eventName: String, params: Any?) {
        try {
            if (reactContext.hasActiveReactInstance()) {
                reactContext
                    .getJSModule(DeviceEventManagerModule.RCTDeviceEventEmitter::class.java)
                    .emit(eventName, params)
            }
        } catch (_: Exception) {}
    }

    override fun onActivityResult(activity: Activity, requestCode: Int, resultCode: Int, data: Intent?) {
        // No external activities used - speech recognition is 100% headless and in-app
    }

    override fun onNewIntent(intent: Intent) {}

    @ReactMethod
    fun isSpeechRecognitionAvailable(promise: Promise) {
        val context = reactContext.currentActivity ?: reactContext
        val available = SpeechRecognizer.isRecognitionAvailable(context)
        promise.resolve(available)
    }

    @ReactMethod
    fun startVoiceRecognition(language: String?, promise: Promise) {
        Handler(Looper.getMainLooper()).post {
            try {
                // If there's an unresolved active promise from a previous invocation, settle it now
                activeSpeechPromise?.let { prevPromise ->
                    try {
                        prevPromise.resolve(lastPartialSpeechText)
                    } catch (_: Exception) {}
                }
                activeSpeechPromise = promise
                lastPartialSpeechText = ""

                // Ensure any prior speech recognizer instance is cleanly cancelled and released
                try {
                    speechRecognizer?.cancel()
                    speechRecognizer?.destroy()
                } catch (_: Exception) {}
                speechRecognizer = null

                val context = reactContext.currentActivity ?: reactContext
                if (!SpeechRecognizer.isRecognitionAvailable(context)) {
                    activeSpeechPromise = null
                    promise.resolve("")
                    return@post
                }

                // Connect to system default Speech Recognition service (Google on Android)
                // 100% headless and in-app without any Google popup dialogs
                val recognizer = SpeechRecognizer.createSpeechRecognizer(context)
                speechRecognizer = recognizer

                val targetLang = language ?: "hi-IN"
                val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
                    putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                    putExtra(RecognizerIntent.EXTRA_LANGUAGE, targetLang)
                    putExtra(RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE, targetLang)
                    putExtra(RecognizerIntent.EXTRA_CALLING_PACKAGE, reactContext.packageName)
                    putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 5)
                    putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
                    putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_MINIMUM_LENGTH_MILLIS, 1500L)
                    putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_COMPLETE_SILENCE_LENGTH_MILLIS, 2000L)
                    putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_POSSIBLY_COMPLETE_SILENCE_LENGTH_MILLIS, 1500L)
                }

                var hasSettled = false

                recognizer.setRecognitionListener(object : RecognitionListener {
                    override fun onReadyForSpeech(params: Bundle?) {
                        sendEvent("onSpeechReady", true)
                    }

                    override fun onBeginningOfSpeech() {
                        sendEvent("onSpeechStart", true)
                    }

                    override fun onRmsChanged(rmsdB: Float) {
                        sendEvent("onSpeechRmsChanged", rmsdB)
                    }

                    override fun onBufferReceived(buffer: ByteArray?) {}

                    override fun onEndOfSpeech() {
                        sendEvent("onSpeechEnd", true)
                    }

                    override fun onError(error: Int) {
                        Handler(Looper.getMainLooper()).post {
                            if (!hasSettled) {
                                hasSettled = true
                                sendEvent("onSpeechError", error)
                                try {
                                    speechRecognizer?.cancel()
                                    speechRecognizer?.destroy()
                                } catch (_: Exception) {}
                                speechRecognizer = null

                                val p = activeSpeechPromise
                                activeSpeechPromise = null
                                val result = if (lastPartialSpeechText.isNotEmpty()) lastPartialSpeechText else ""
                                p?.resolve(result)
                            }
                        }
                    }

                    override fun onResults(results: Bundle?) {
                        Handler(Looper.getMainLooper()).post {
                            if (!hasSettled) {
                                hasSettled = true
                                val matches = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                                try {
                                    speechRecognizer?.destroy()
                                } catch (_: Exception) {}
                                speechRecognizer = null

                                val recognized = if (matches != null && matches.isNotEmpty() && matches[0].trim().isNotEmpty()) {
                                    matches[0].trim()
                                } else if (lastPartialSpeechText.isNotEmpty()) {
                                    lastPartialSpeechText
                                } else {
                                    ""
                                }
                                sendEvent("onSpeechResults", recognized)
                                val p = activeSpeechPromise
                                activeSpeechPromise = null
                                p?.resolve(recognized)
                            }
                        }
                    }

                    override fun onPartialResults(partialResults: Bundle?) {
                        Handler(Looper.getMainLooper()).post {
                            val matches = partialResults?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                            if (matches != null && matches.isNotEmpty()) {
                                val partial = matches[0].trim()
                                if (partial.isNotEmpty()) {
                                    lastPartialSpeechText = partial
                                    sendEvent("onSpeechPartialResults", partial)
                                }
                            }
                        }
                    }

                    override fun onEvent(eventType: Int, params: Bundle?) {}
                })

                recognizer.startListening(intent)
            } catch (e: Exception) {
                try {
                    speechRecognizer?.destroy()
                } catch (_: Exception) {}
                speechRecognizer = null
                val p = activeSpeechPromise
                activeSpeechPromise = null
                p?.resolve(lastPartialSpeechText)
            }
        }
    }

    @ReactMethod
    fun stopVoiceRecognition(promise: Promise) {
        Handler(Looper.getMainLooper()).post {
            try {
                try {
                    speechRecognizer?.stopListening()
                } catch (_: Exception) {}

                // Give recognizer up to 500ms to dispatch onResults; if not settled, resolve active promise with fallback text
                Handler(Looper.getMainLooper()).postDelayed({
                    val p = activeSpeechPromise
                    if (p != null) {
                        activeSpeechPromise = null
                        val fallback = lastPartialSpeechText
                        try {
                            speechRecognizer?.cancel()
                            speechRecognizer?.destroy()
                        } catch (_: Exception) {}
                        speechRecognizer = null
                        try {
                            p.resolve(fallback)
                        } catch (_: Exception) {}
                    }
                }, 500)
                promise.resolve(true)
            } catch (e: Exception) {
                val p = activeSpeechPromise
                activeSpeechPromise = null
                try {
                    p?.resolve(lastPartialSpeechText)
                } catch (_: Exception) {}
                promise.resolve(false)
            }
        }
    }

    @ReactMethod
    fun cancelVoiceRecognition(promise: Promise) {
        Handler(Looper.getMainLooper()).post {
            try {
                val p = activeSpeechPromise
                activeSpeechPromise = null
                try {
                    p?.resolve("")
                } catch (_: Exception) {}
                try {
                    speechRecognizer?.cancel()
                    speechRecognizer?.destroy()
                } catch (_: Exception) {}
                speechRecognizer = null
                promise.resolve(true)
            } catch (e: Exception) {
                promise.resolve(false)
            }
        }
    }

    @SuppressLint("MissingPermission")
    @ReactMethod
    fun startRecording(promise: Promise) {
        if (isRecording.get()) {
            promise.reject("ALREADY_RECORDING", "Audio recording is already in progress.")
            return
        }

        // Cleanly terminate any active SpeechRecognizer to prevent AudioFlinger lockup
        try {
            speechRecognizer?.cancel()
            speechRecognizer?.destroy()
        } catch (_: Exception) {}
        speechRecognizer = null

        try {
            val sampleRate = 16000
            val channelConfig = AudioFormat.CHANNEL_IN_MONO
            val audioFormat = AudioFormat.ENCODING_PCM_16BIT
            val minBufferSize = AudioRecord.getMinBufferSize(sampleRate, channelConfig, audioFormat)
            val bufferSize = minBufferSize.coerceAtLeast(2048)

            audioRecord = AudioRecord(
                MediaRecorder.AudioSource.MIC,
                sampleRate,
                channelConfig,
                audioFormat,
                bufferSize
            )

            if (audioRecord?.state != AudioRecord.STATE_INITIALIZED) {
                promise.reject("INIT_FAILED", "Failed to initialize AudioRecord. Please check RECORD_AUDIO permission.")
                return
            }

            outputFile = File(reactApplicationContext.cacheDir, "citizen_voice_recording.wav")
            isRecording.set(true)
            audioRecord?.startRecording()

            recordingThread = Thread {
                writeAudioDataToWav(outputFile!!, bufferSize, sampleRate)
            }
            recordingThread?.start()

            promise.resolve(outputFile?.absolutePath)
        } catch (e: Exception) {
            isRecording.set(false)
            promise.reject("RECORD_ERROR", e.message, e)
        }
    }

    @ReactMethod
    fun stopRecording(promise: Promise) {
        if (!isRecording.get()) {
            promise.reject("NOT_RECORDING", "No active audio recording found.")
            return
        }

        try {
            isRecording.set(false)
            try {
                audioRecord?.stop()
            } catch (_: Exception) {}
            audioRecord?.release()
            audioRecord = null

            recordingThread?.join(1500)
            recordingThread = null

            val file = outputFile
            if (file != null && file.exists() && file.length() > 44) {
                val bytes = file.readBytes()
                val base64String = Base64.encodeToString(bytes, Base64.NO_WRAP)
                promise.resolve(base64String)
            } else {
                promise.reject("EMPTY_RECORDING", "No audio captured during the recording session.")
            }
        } catch (e: Exception) {
            promise.reject("STOP_ERROR", e.message, e)
        }
    }

    @ReactMethod
    fun isAvailable(promise: Promise) {
        promise.resolve(true)
    }

    @ReactMethod
    fun playAudioBase64(base64Audio: String, promise: Promise) {
        try {
            stopCurrentPlayback()

            try {
                val audioManager = reactApplicationContext.getSystemService(Context.AUDIO_SERVICE) as? AudioManager
                audioManager?.mode = AudioManager.MODE_NORMAL
                audioManager?.isSpeakerphoneOn = true

                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    val focusRequest = AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN_TRANSIENT)
                        .setAudioAttributes(
                            AudioAttributes.Builder()
                                .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
                                .setUsage(AudioAttributes.USAGE_MEDIA)
                                .build()
                        )
                        .build()
                    audioManager?.requestAudioFocus(focusRequest)
                } else {
                    @Suppress("DEPRECATION")
                    audioManager?.requestAudioFocus(null, AudioManager.STREAM_MUSIC, AudioManager.AUDIOFOCUS_GAIN_TRANSIENT)
                }
            } catch (_: Exception) {}

            val audioBytes = Base64.decode(base64Audio, Base64.DEFAULT)
            val extension = if (audioBytes.size >= 4 && audioBytes[0] == 'R'.code.toByte() && audioBytes[1] == 'I'.code.toByte()) ".wav" else ".mp3"
            val tempFile = File.createTempFile("tts_playback_", extension, reactApplicationContext.cacheDir)
            tempFile.writeBytes(audioBytes)

            mediaPlayer = MediaPlayer().apply {
                setAudioAttributes(
                    AudioAttributes.Builder()
                        .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
                        .setUsage(AudioAttributes.USAGE_MEDIA)
                        .build()
                )
                setDataSource(tempFile.absolutePath)
                setVolume(1.0f, 1.0f)
                setOnPreparedListener { mp ->
                    try {
                        mp.start()
                    } catch (_: Exception) {}
                }
                setOnCompletionListener {
                    try { it.release() } catch (_: Exception) {}
                    mediaPlayer = null
                    tempFile.delete()
                }
                setOnErrorListener { mp, _, _ ->
                    try { mp.release() } catch (_: Exception) {}
                    mediaPlayer = null
                    tempFile.delete()
                    true
                }
                prepareAsync()
            }
            promise.resolve(true)
        } catch (e: Exception) {
            promise.resolve(false)
        }
    }

    @ReactMethod
    fun stopAudio(promise: Promise) {
        stopCurrentPlayback()
        promise.resolve(true)
    }

    private fun stopCurrentPlayback() {
        try {
            mediaPlayer?.stop()
            mediaPlayer?.release()
        } catch (_: Exception) {}
        mediaPlayer = null
        try {
            reactApplicationContext.cacheDir?.listFiles { _, name -> name.startsWith("tts_playback_") }?.forEach {
                it.delete()
            }
        } catch (_: Exception) {}
    }

    private fun writeAudioDataToWav(file: File, bufferSize: Int, sampleRate: Int) {
        val data = ByteArray(bufferSize)
        val fos = FileOutputStream(file)
        // Reserve placeholder 44 bytes for standard WAV header
        fos.write(ByteArray(44))

        var totalAudioBytes = 0
        while (isRecording.get()) {
            val bytesRead = audioRecord?.read(data, 0, bufferSize) ?: -1
            if (bytesRead > 0) {
                fos.write(data, 0, bytesRead)
                totalAudioBytes += bytesRead
            }
        }
        fos.flush()
        fos.close()

        // Seek back to start and inject complete WAV header with byte counts
        val raf = RandomAccessFile(file, "rw")
        raf.seek(0)
        writeWavHeader(raf, totalAudioBytes, sampleRate)
        raf.close()
    }

    private fun writeWavHeader(raf: RandomAccessFile, totalAudioLen: Int, sampleRate: Int) {
        val totalDataLen = totalAudioLen + 36
        val channels = 1
        val byteRate = 16 * sampleRate * channels / 8

        val header = ByteArray(44)
        header[0] = 'R'.code.toByte()
        header[1] = 'I'.code.toByte()
        header[2] = 'F'.code.toByte()
        header[3] = 'F'.code.toByte()
        header[4] = (totalDataLen and 0xff).toByte()
        header[5] = (totalDataLen shr 8 and 0xff).toByte()
        header[6] = (totalDataLen shr 16 and 0xff).toByte()
        header[7] = (totalDataLen shr 24 and 0xff).toByte()
        header[8] = 'W'.code.toByte()
        header[9] = 'A'.code.toByte()
        header[10] = 'V'.code.toByte()
        header[11] = 'E'.code.toByte()
        header[12] = 'f'.code.toByte()
        header[13] = 'm'.code.toByte()
        header[14] = 't'.code.toByte()
        header[15] = ' '.code.toByte()
        header[16] = 16 // PCM chunk size
        header[17] = 0
        header[18] = 0
        header[19] = 0
        header[20] = 1 // Linear PCM format code
        header[21] = 0
        header[22] = channels.toByte()
        header[23] = 0
        header[24] = (sampleRate and 0xff).toByte()
        header[25] = (sampleRate shr 8 and 0xff).toByte()
        header[26] = (sampleRate shr 16 and 0xff).toByte()
        header[27] = (sampleRate shr 24 and 0xff).toByte()
        header[28] = (byteRate and 0xff).toByte()
        header[29] = (byteRate shr 8 and 0xff).toByte()
        header[30] = (byteRate shr 16 and 0xff).toByte()
        header[31] = (byteRate shr 24 and 0xff).toByte()
        header[32] = (channels * 16 / 8).toByte() // block align
        header[33] = 0
        header[34] = 16 // bits per sample
        header[35] = 0
        header[36] = 'd'.code.toByte()
        header[37] = 'a'.code.toByte()
        header[38] = 't'.code.toByte()
        header[39] = 'a'.code.toByte()
        header[40] = (totalAudioLen and 0xff).toByte()
        header[41] = (totalAudioLen shr 8 and 0xff).toByte()
        header[42] = (totalAudioLen shr 16 and 0xff).toByte()
        header[43] = (totalAudioLen shr 24 and 0xff).toByte()

        raf.write(header, 0, 44)
    }
}

