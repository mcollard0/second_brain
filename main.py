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
    active_filename = None
    
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
            
            # Dynamic System Prompt
            current_prompt = SYSTEM_PROMPT
            if active_filename:
                current_prompt += f"\n\nIMPORTANT: You MUST continue appending to the file: '{active_filename}'. Do NOT change the filename."
            
            # 2. LLM
            print("Generating response...")
            response_data = await llm.generate(current_prompt, messages)
            
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
                
                proposed_filename = payload.get("filename")
                content = payload.get("content")
                
                if content:
                    if active_filename:
                        filename = active_filename
                    elif proposed_filename:
                        active_filename = proposed_filename
                        filename = proposed_filename
                    else:
                        filename = None

                    if filename:
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
        # Updated default to Flash (faster/cheaper)
        llm = GeminiProvider(model_name=args.model if args.model else "gemini-3-flash-preview")
    elif args.provider == "anthropic":
        llm = AnthropicProvider(model_name=args.model if args.model else "claude-3-opus-20240229")
    elif args.provider == "openai":
        llm = OpenAIProvider(model_name=args.model if args.model else "gpt-4-turbo-preview")
        
    asr = ASR()
    tts = TTS()
    storage = Storage(base_path="brain")
    
    print(f"Starting Second Brain with {args.provider}...")
    try:
        asyncio.run(pipeline(asr, llm, tts, storage))
    except KeyboardInterrupt:
        print("\nExiting...")
        tts.close()

if __name__ == "__main__":
    main()
