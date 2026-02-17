import asyncio
import argparse
import os
import json
from dotenv import load_dotenv
from modules.asr import ASR
from modules.llm.gemini import GeminiProvider
from modules.llm.anthropic import AnthropicProvider
from modules.llm.openai import OpenAIProvider
from modules.tts import TTS
from modules.storage import Storage

# Load environment variables
load_dotenv()

async def pipeline(asr, llm, tts, storage):
    """
    Main pipeline: Concurrent ASR -> LLM -> (TTS, Storage)
    Allows listening while speaking.
    """
    # System Prompt with JSON instruction
    SYSTEM_PROMPT = """
You are an idea refinement agent. Respond **only** in JSON.

Format: `{"voice_output": {"text": "..."}, "data_management": {"will_capture": true, "capture_payload": {"filename": "ideas.md", "content": "## Idea\n..."}}}`

**Data Capture Rules:**
1.  If an idea is worth saving, include a `data_management` object.
2.  **Memory**: You must remember the filename you used previously for a topic. Do not change it unless the user explicitly asks to start a new file.
3.  **Content**: Append new details. Do not repeat previously saved details unless they have changed.

Keep voice responses concise and conversational.
"""

    messages = []
    # Shared state for filename memory
    state = {"active_filename": None}
    
    # Queue for decoupled ASR -> LLM processing
    input_queue = asyncio.Queue()

    async def producer_asr():
        """Continuously listens and pushes text to queue"""
        print("[System] ASR Background Task Started")
        while True:
            # This yields control, allowing consumer to run
            text = await asr.listen()
            
            if text:
                print(f"[ASR Input]: {text}")
                await input_queue.put(text)
                
                if text.lower() in ["exit", "quit", "stop"]:
                    print("[ASR] Exit command received.")
                    break

    async def consumer_processing():
        """Consumes text, generates response, and speaks"""
        print("[System] Processing Task Started")
        while True:
            # Wait for input
            text = await input_queue.get()
            
            if text.lower() in ["exit", "quit", "stop"]:
                input_queue.task_done()
                break
                
            # Add to history
            messages.append({"role": "user", "content": text})
            
            # Dynamic System Prompt
            current_prompt = SYSTEM_PROMPT
            if state["active_filename"]:
                 current_prompt += f"\n\nIMPORTANT: You MUST continue appending to the file: '{state['active_filename']}'. Do NOT change the filename."

            print(f"[LLM] Thinking...")
            try:
                response_data = await llm.generate(current_prompt, messages)
                
                voice_output = response_data.get("voice_output", {})
                data_mgmt = response_data.get("data_management", {})
                
                assistant_text = voice_output.get("text", "")
                messages.append({"role": "assistant", "content": assistant_text})
                
                # Handle Data Capture
                if data_mgmt.get("will_capture"):
                    payload = data_mgmt.get("capture_payload", {})
                    
                    proposed_filename = payload.get("filename")
                    content = payload.get("content")
                    
                    if content:
                        if state["active_filename"]:
                            filename = state["active_filename"]
                        elif proposed_filename:
                            state["active_filename"] = proposed_filename
                            filename = proposed_filename
                        else:
                            filename = None
                            
                        if filename:
                            print(f"[STORAGE] Saving to {filename}...")
                            asyncio.create_task(storage.save(filename, content))
                
                # TTS
                if assistant_text:
                    print(f"AI: {assistant_text}")
                    # We await here, but producer_asr continues running!
                    await tts.speak(assistant_text)
                    
            except Exception as e:
                print(f"[Error] Processing failed: {e}")
            finally:
                input_queue.task_done()

    # Run both tasks concurrently
    producer = asyncio.create_task(producer_asr())
    consumer = asyncio.create_task(consumer_processing())
    
    # Wait for them to finish (they finish when 'exit' is spoken)
    await asyncio.gather(producer, consumer)
def main():
    parser = argparse.ArgumentParser(description="Second Brain Voice Assistant")
    parser.add_argument("--provider", choices=["gemini", "anthropic", "openai"], default="gemini", help="LLM Provider")
    parser.add_argument("--model", type=str, help="Specific model name")
    parser.add_argument("--voice-id", type=str, help="ElevenLabs Voice ID")
    parser.add_argument("--audio-output-index", type=int, help="Audio Output Device Index")
    parser.add_argument("--audio-channels", type=int, help="Audio Channels (1 or 2)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging and audio dump")
    
    args = parser.parse_args()
    
    # Initialize Provider
    if args.provider == "gemini":
        # Updated default to Flash (faster/cheaper)
        llm = GeminiProvider(model_name=args.model if args.model else "gemini-3-flash-preview")
    elif args.provider == "anthropic":
        llm = AnthropicProvider(model_name=args.model if args.model else "claude-3-opus-20240229")
    elif args.provider == "openai":
        llm = OpenAIProvider(model_name=args.model if args.model else "gpt-4-turbo-preview")
        
    asr = ASR()
    tts = TTS(voice_id=args.voice_id, device_index=args.audio_output_index, channels=args.audio_channels, debug=args.debug)
    storage = Storage(base_path="brain")
    
    print(f"Starting Second Brain with {args.provider}...")
    try:
        asyncio.run(pipeline(asr, llm, tts, storage))
    except KeyboardInterrupt:
        print("\nExiting...")
        tts.close()

if __name__ == "__main__":
    main()
