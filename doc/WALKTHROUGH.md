# Second Brain Walkthrough

This document outlines the implemented Second Brain system, its components, and how to run and verify it.

## Implemented Components

1.  **ASR (Speech to Text)**: Uses `speech_recognition` and Google Voice API (via `r.recognize_google`) to convert microphone input to text.
2.  **LLM Providers**:
    - **Base Interface**: Standardized `generate` method.
    - **Gemini**: Default provider using `google-generativeai`.
    - **Anthropic**: Support for Claude 3.
    - **OpenAI**: Support for GPT-4.
3.  **TTS (Text to Speech)**: Uses ElevenLabs WebSocket API to stream audio responses.
4.  **Storage**: Asynchronously appends captured ideas to markdown files.
5.  **Main Loop**: Orchestrates the pipeline: `Listen -> Think -> Speak & Save`.

## Setup

1.  **Virtual Environment**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```
    *Note: You may need system dependencies for PyAudio (e.g., `sudo pacman -S python-pyaudio portaudio` on Arch/Manjaro).*

2.  **Environment Variables**:
    Copy `.env.example` to `.env` and fill in your API keys:
    ```bash
    cp .env.example .env
    # Edit .env with your keys
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

Run the test suite to verify individual components:

1.  **Test 1: Microphone & ASR**
    ```bash
    python test_suite.py --test 1
    ```
    *Speak into the mic and confirm the text is correct.*

2.  **Test 2: LLM JSON Response**
    ```bash
    python test_suite.py --test 2 --provider gemini
    ```
    *Speak a prompt and verify the JSON output structure.*

3.  **Test 3: Full Loop (TTS)**
    ```bash
    python test_suite.py --test 3
    ```
    *Speak "Hello" and confirm you hear the audio response.*
