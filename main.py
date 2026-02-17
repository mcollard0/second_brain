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
    Main pipeline: ASR -> LLM -> (TTS, Storage)
    """
    # System Prompt with JSON instruction
    SYSTEM_PROMPT = """
You are an idea refinement agent. Respond **only** in JSON.

If an idea is worth saving, include a `data_management` object with a `filename` and `content` in Markdown.

**Rules:**

1. Keep `voice_output` conversational (no markdown tags here).
2. Once a `filename` is chosen for a session, you must use that same filename for all subsequent appends in that thread (unless capturing a distinctly new idea).
3. Use the format: `{"voice_output": {"text": "..."}, "data_management": {"will_capture": true, "capture_payload": {...}}}`
    """

    messages = []
    
    while True:
        try:
            # 1. ASR
            user_text = await asr.listen()
            if not user_text:
                continue # Listen again if nothing heard
            
            if user_text.lower() in ["exit", "quit", "stop"]:
                break
                
            print(f"User: {user_text}")
            messages.append({"role": "user", "content": user_text})
            
            # 2. LLM
            print("Generating response...")
            response_data = await llm.generate(SYSTEM_PROMPT, messages)
            
            # 3. Process Response
            voice_output = response_data.get("voice_output", {})
            data_mgmt = response_data.get("data_management", {})
            
            # Add assistant message to history (using the voice text as content representation for history context?)
            # Ideally we store the structured interaction, but for simple chat history, text is fine.
            assistant_text = voice_output.get("text", "")
            messages.append({"role": "assistant", "content": assistant_text})
            
            # 4. Storage (Parallel if possible, but small writes are fast)
            if data_mgmt.get("will_capture"):
                payload = data_mgmt.get("capture_payload", {})
                filename = payload.get("filename")
                content = payload.get("content")
                if filename and content:
                    asyncio.create_task(storage.save(filename, content))
            
            # 5. TTS (Blocking/Streaming)
            if assistant_text:
                print(f"AI: {assistant_text}")
                await tts.speak(assistant_text)
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"An error occurred in pipeline: {e}")
            await asyncio.sleep(1)

def main():
    parser = argparse.ArgumentParser(description="Second Brain Voice Assistant")
    parser.add_argument("--provider", choices=["gemini", "anthropic", "openai"], default="gemini", help="LLM Provider")
    parser.add_argument("--model", type=str, help="Specific model name")
    
    args = parser.parse_args()
    
    # Initialize Provider
    if args.provider == "gemini":
        llm = GeminiProvider(model_name=args.model if args.model else "gemini-1.5-pro-latest")
    elif args.provider == "anthropic":
        llm = AnthropicProvider(model_name=args.model if args.model else "claude-3-opus-20240229")
    elif args.provider == "openai":
        llm = OpenAIProvider(model_name=args.model if args.model else "gpt-4-turbo-preview")
        
    asr = ASR()
    tts = TTS()
    storage = Storage()
    
    print(f"Starting Second Brain with {args.provider}...")
    try:
        asyncio.run(pipeline(asr, llm, tts, storage))
    except KeyboardInterrupt:
        print("\nExiting...")
        tts.close()

if __name__ == "__main__":
    main()
