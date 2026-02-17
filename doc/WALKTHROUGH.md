# Second Brain Walkthrough

This document outlines the implemented Second Brain system, its components, and how to run and verify it.

## Implemented Components

1.  **ASR (Speech to Text)**: Uses `speech_recognition` and Google Voice API (via `r.recognize_google`) to convert microphone input to text.
2.  **LLM Providers**:
    - **Base Interface**: Standardized `generate` method.
    - **Gemini**: Default provider using `google-genai` (Default model: `gemini-3-flash-preview`).
    - **Anthropic**: Support for Claude 3.
    - **OpenAI**: Support for GPT-4.
3.  **TTS (Text to Speech)**: Uses ElevenLabs WebSocket API to stream audio responses.
4.  **Storage**: Asynchronously appends captured ideas to markdown files.
5.  **Main Loop**: Orchestrates the pipeline: `Listen -> Think -> Speak & Save`.

## Setup

1.  **Virtual Environment**:
    ```bash
    python3.11 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```
    *Note: You may need system dependencies for PyAudio (e.g., `sudo pacman -S python-pyaudio portaudio` on Arch/Manjaro). Python 3.11 is recommended due to CFFI compatibility issues with 3.13t.*

2.  **Environment Variables**:
    ```bash
    cp .env.example .env
    # Edit .env with your keys
    # Optional: Set ELEVENLABS_VOICE_ID to change the voice (Default: LjNqOSdRGIUUmAcEINh7)
    ```

## Running the Application

To run the main assistant with the default Gemini provider:
```bash
python main.py
```

To use other providers:
```bash
python main.py --provider anthropic
python main.py --provider openai --model gpt-4
```

## Verification

Run the test suite to access the verification menu:

```bash
./venv/bin/python test_suite.py
```

**Menu Options:**
1.  **Single Turn Loop**: Tests one full cycle (`Listen -> Think -> Speak`) to verify all components work together.
2.  **Continuous Conversation Loop (Sequential)**: Runs the assistant in a simple loop (Listen -> Think -> Speak).
3.  **Concurrent Duplex Loop**: Runs with decoupled input/output queues. You can speak *while* the AI is speaking.

## Troubleshooting

### Audio Output Errors (ALSA/PipeWire)
The system defaults to **Output Index 21** and **2 Channels** (Stereo) as this is the most common working configuration for PipeWire.

If you encounter errors or no sound, you can override these defaults:

1.  List available devices:
    ```bash
    ./venv/bin/python list_audio_devices.py
    ```
2.  Override the default index (e.g., to 20):
    ```bash
    export AUDIO_OUTPUT_INDEX=20
    ./venv/bin/python test_suite.py
    ```

### Invalid Number of Channels
The system defaults to **2 Channels** to support PipeWire/PulseAudio. If you need Mono (1 channel):

```bash
export AUDIO_CHANNELS=1
./venv/bin/python test_suite.py
```

### Automatic Data Capture
Use **Test Mode 3 (Concurrent Duplex)** for the best experience.
-   Speak naturally.
-   If you say "Save this idea...", the system will capture it to `brain/ideas.md` (or similar file chosen by the LLM).
-   Memory is maintained during the session.

