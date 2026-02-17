# Second Brain Implementation Plan

## Goal Description
Build a real-time voice-to-voice AI system that captures and saves valuable ideas to disk. The system uses asynchronous queues to handle audio streaming and file I/O concurrently. It integrates ASR (user voice), LLM (OpenAI GPT), and TTS (ElevenLabs).

## User Review Required
> [!IMPORTANT]
> - **API Keys**: The system requires valid API keys for the selected provider (`GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, or `OPENAI_API_KEY`) and `ELEVENLABS_API_KEY` in the environment.
> - **Audio Hardware**: A working microphone and speakers are required for the full loop.
> - **Python Version**: Python 3.11+ is required for `asyncio` features.

## Proposed Changes

### Project Structure
- `main.py`: Entry point and orchestration.
- `modules/`:
    - `asr.py`: Handles microphone input and transcription.
    - `llm/`: Directory for LLM providers.
        - `base.py`: Abstract base class for LLM providers.
        - `gemini.py`: Google Gemini implementation (Default).
        - `anthropic.py`: Anthropic Claude implementation.
        - `openai.py`: OpenAI GPT implementation.
    - `tts.py`: Handles ElevenLabs streaming interface.
    - `storage.py`: Handles file writing (Data Management).
- `requirements.txt`: Dependencies.
- `.env`: Configuration management.

### [Core Components]

#### [NEW] [modules/asr.py]
- Uses `speech_recognition` or `sounddevice` + Whisper API (or local) for capturing user input.
- *Decision*: Will use `speech_recognition` locally for wake word/silence detection if possible, or simple audio capture sent to Whisper API for accuracy as per "User ASR".

#### [NEW] [modules/llm/]
- `base.py`: Defines the interface (`async def generate(self, system_prompt, messages) -> dict`).
- `gemini.py`: Uses `google-generativeai` library. Default model: `gemini-1.5-pro-latest` (or `gemini-2.0-flash` if available/preferred).
- `anthropic.py`: Uses `anthropic` library. Default model: `claude-3-opus-20240229`.
- `openai.py`: Uses `openai` library. Default model: `gpt-4-turbo-preview`.

#### [NEW] [modules/tts.py]
- Connects to ElevenLabs WebSocket API (`wss://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream-input`).
- Streams audio chunks to the output device (using `pyaudio` or `sounddevice`).

#### [NEW] [modules/storage.py]
- Async file writer.
- Appends content to markdown files as specified in the `data_management` payload.

#### [NEW] [main.py]
- Sets up `asyncio.Queue`s (`tts_queue`, `disk_queue`).
- **cli args**:
    - `--provider`: `gemini` (default), `anthropic`, `openai`.
    - `--model`: Specific model name (optional, overrides default for provider).
- Runs the main event loop.

## Verification Plan

### Automated Tests
- N/A for hardware availability (mic/speaker) in this environment, but unit tests for logic (JSON parsing, Queue handling) can be added.

### Manual Verification
- **Test 1**: Speak into mic -> Verify text printed on screen.
- **Test 2**: Speak -> Verify JSON printed with "voice_output" and optional "data_management".
- **Test 3**: Speak -> Hear response and verify file creation if "save" was triggered.
