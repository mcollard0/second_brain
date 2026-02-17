ARCHITECTURE.md

Project: Second Brain
Architect: Michael Collard (yeah, yeah)
Date: 20260217

Python 3.11t if we can make queues to be consumed and prevent corruption.  Limiting factor will be the network io. 

Multidirectional websocket connections. 

User ASR/ user typed Input -> GPT -> Eleven labs streamed voice -> (back to) user

### WebSocket Queue Management

To prevent corruption in Python 3.11, use `asyncio.Queue`.

- **Queue A (TTS):** Feeds `voice_output.text` directly to the ElevenLabs WebSocket.
    
- **Queue B (Disk IO):** Feeds `data_management.capture_payload` to a non-blocking file writer.

System Prompt: "You are an idea refinement agent. Respond **only** in JSON.

If an idea is worth saving, include a `data_management` object with a `filename` and `content` in Markdown.

**Rules:**

1. Keep `voice_output` conversational (no markdown tags here).
    
2. Once a `filename` is chosen for a session, you must use that same filename for all subsequent appends in that thread.
    
3. Use the format: `{"voice_output": {"text": "..."}, "data_management": {"will_capture": true, "capture_payload": {...}}}`"

(End System Prompt Planning)
## Suggested JSON Response Format

The AI should respond with a structured object that separates what the user **hears** from what the system **saves**.

JSON

```
{
  "control": {
    "session_id": "uuid-12345",
    "status": "processing|complete",
    "stream_id": "chunk_001"
  },
  "voice_output": {
    "text": "That's a fascinating idea for a modular garden! I've noted the dimensions for you.",
    "chunk_index": 1
  },
  "data_management": {
    "will_capture": true,
    "capture_payload": {
      "filename": "modular_garden_specs.md",
      "content": "# Modular Garden Dimensions\n- Width: 4ft\n- Length: 8ft\n- Material: Cedar",
      "mode": "append"
    }
  },
  "metadata": {
    "tokens_used": 142,
    "provider": "openai"
  }
}
```

If response back has a capture_payload <text> in it's response text the data is written to disk as an output of value to save. Append using description filename AI chooses but cannot change once chosen. Capture in Markdown? 

Supports top AI providers via api keys in env. 

11Labs url: wss://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream-input

May be able to use chars from 11labs response for capture.  But better to intercept the gpt message and save that. 

Wishlist: AI with start listening button. Auto shut off for silence, restart on speech detection, optimally with buffer so nothing lost.  

Tests: 
1. Mic Voice input, converted to text.  User responds y/n if correct for pass fail. 
2. Using #1, message sent to AI returns json with message and optional capture message. Req: filename.md. verification: user yn input
3. Building on one and two, message is sent to 11labs and played on user computer. Message printed, yn for pass fail.
