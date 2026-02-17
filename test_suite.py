import asyncio
import argparse
import os
from dotenv import load_dotenv
from modules.asr import ASR
from modules.tts import TTS
from modules.storage import Storage
import json

# Load environment variables
load_dotenv()

def get_llm(provider="gemini"):
    if provider == "gemini":
        from modules.llm.gemini import GeminiProvider
        return GeminiProvider()
    elif provider == "anthropic":
        from modules.llm.anthropic import AnthropicProvider
        return AnthropicProvider()
    elif provider == "openai":
        from modules.llm.openai import OpenAIProvider
        return OpenAIProvider()
    return None

async def test_single_turn(provider="gemini"):
    """Test 1: Single Turn Full Loop (Mic -> AI -> TTS)"""
    print(f"\n--- Single Turn Loop ({provider}) ---")
    
    llm = get_llm(provider)
    asr = ASR()
    tts = TTS()
    
# Shared System Prompt
# Shared System Prompt
SYSTEM_PROMPT = """
You are an idea refinement agent. Respond **only** in JSON.

Format: `{"voice_output": {"text": "..."}, "data_management": {"will_capture": true, "capture_payload": {"filename": "ideas.md", "content": "## Idea\n..."}}}`

**Data Capture Rules:**
1.  If an idea is worth saving, include a `data_management` object.
2.  **Memory**: You must remember the filename you used previously for a topic. Do not change it unless the user explicitly asks to start a new file.
3.  **Content**: Append new details. Do not repeat previously saved details unless they have changed.

Keep voice responses concise and conversational.
"""

async def test_single_turn(provider="gemini"):
    """Test 1: Single Turn Full Loop (Mic -> AI -> TTS)"""
    print(f"\n--- Single Turn Loop ({provider}) ---")
    
    llm = get_llm(provider)
    asr = ASR()
    tts = TTS()
    storage = Storage(base_path="brain") # Save to 'brain' directory
    
    input("Press Enter to start listening (say 'Hello')...")
    text = await asr.listen()
    print(f"User: {text}")
    if not text:
        print("No speech detected.")
        return
        
    response = await llm.generate(SYSTEM_PROMPT, [{"role": "user", "content": text}])
    voice_text = response.get("voice_output", {}).get("text", "")
    
    # Handle Data Capture
    data_mgmt = response.get("data_management", {})
    if data_mgmt.get("will_capture"):
        payload = data_mgmt.get("capture_payload", {})
        filename = payload.get("filename")
        content = payload.get("content")
        if filename and content:
            print(f"[STORAGE] Saving to {filename}...")
            await storage.save(filename, content)
            
    print(f"AI Response Text: {voice_text}")
    
    if voice_text:
        print("Streaming to TTS...")
        await tts.speak(voice_text)
        
    tts.close()

async def test_continuous_loop(provider="gemini"):
    """Test 2: Continuous Loop (Mic -> AI -> TTS -> Repeat)"""
    print(f"\n--- Continuous Conversation ({provider}) ---")
    print("Say 'exit', 'quit', or 'stop' to end.")
    
    llm = get_llm(provider)
    asr = ASR()
    tts = TTS()
    storage = Storage(base_path="brain")
    
    history = []
    active_filename = None # Memory for filename
    
    try:
        while True:
            # ASR
            print("\nListening...")
            text = await asr.listen()
            if not text:
                continue
                
            print(f"User: {text}")
            if text.lower() in ["exit", "quit", "stop"]:
                print("Exiting loop.")
                break
                
            history.append({"role": "user", "content": text})
            
            # Dynamic System Prompt to enforce filename
            current_prompt = SYSTEM_PROMPT
            if active_filename:
                current_prompt += f"\n\nIMPORTANT: You MUST continue appending to the file: '{active_filename}'. Do NOT change the filename."
            
            # LLM
            print("Thinking...")
            response = await llm.generate(current_prompt, history)
            voice_text = response.get("voice_output", {}).get("text", "")
            
            # Handle Data Capture
            data_mgmt = response.get("data_management", {})
            if data_mgmt.get("will_capture"):
                payload = data_mgmt.get("capture_payload", {})
                
                # Logic: If active_filename is set, FORCE it. If not, set it from payload.
                proposed_filename = payload.get("filename")
                content = payload.get("content")
                
                if content:
                    if active_filename:
                        # Override LLM's filename with our strict memory
                        filename = active_filename
                    elif proposed_filename:
                        # First time setting it
                        active_filename = proposed_filename
                        filename = active_filename
                    else:
                        filename = None

                    if filename:
                        print(f"[STORAGE] Saving to {filename}...")
                        await storage.save(filename, content)
            
            # Update history
            history.append({"role": "model", "content": voice_text}) 
            
            print(f"AI: {voice_text}")
            
            # TTS
            if voice_text:
                await tts.speak(voice_text)
                
    except KeyboardInterrupt:
        print("\nInterrupted.")
    finally:
        tts.close()

async def test_concurrent_loop(provider="gemini"):
    """Test 3: Concurrent Duplex Loop (Mic listens WHILE AI speaks)"""
    print(f"\n--- Concurrent Duplex Conversation ({provider}) ---")
    print("Say 'exit', 'quit', or 'stop' to end.")
    print("NOTE: You can speak while the AI is speaking.")
    
    llm = get_llm(provider)
    asr = ASR()
    tts = TTS()
    storage = Storage(base_path="brain")
    
    # Queue for decoupled ASR -> LLM processing
    input_queue = asyncio.Queue()
    
    history = []
    
    # Shared state for filename memory (needs to be mutable or object to access in closure if needed, but here simple local var in outer scope works if passed/accessed correctly)
    # Actually, needs to be in consumer scope or shared dict
    state = {"active_filename": None}
    
    async def producer_asr():
        """Continuously listens and pushes text to queue"""
        print("[System] ASR Background Task Started")
        while True:
            # This yields control, allowing consumer to run
            text = await asr.listen()
            
            if text:
                print(f"\n[ASR Input]: {text}")
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
            history.append({"role": "user", "content": text})
            
            # Dynamic System Prompt
            current_prompt = SYSTEM_PROMPT
            if state["active_filename"]:
                 current_prompt += f"\n\nIMPORTANT: You MUST continue appending to the file: '{state['active_filename']}'. Do NOT change the filename."

            print(f"[LLM] Thinking...")
            try:
                response = await llm.generate(current_prompt, history)
                voice_text = response.get("voice_output", {}).get("text", "")
                
                # Handle Data Capture
                data_mgmt = response.get("data_management", {})
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
                
                # Update history
                history.append({"role": "model", "content": voice_text})
                
                # TTS
                if voice_text:
                    print(f"AI: {voice_text}")
                    # We await here, but producer_asr continues running!
                    await tts.speak(voice_text)
                    
            except Exception as e:
                print(f"[Error] Processing failed: {e}")
            finally:
                input_queue.task_done()

    # Run both tasks concurrently
    producer = asyncio.create_task(producer_asr())
    consumer = asyncio.create_task(consumer_processing())
    
    # Wait for them to finish (they finish when 'exit' is spoken)
    await asyncio.gather(producer, consumer)
    
    tts.close()

async def main():
    parser = argparse.ArgumentParser(description="Second Brain Test Suite")
    parser.add_argument("--provider", default="gemini", choices=["gemini", "anthropic", "openai"])
    args = parser.parse_args()
    
    while True:
        print("\n--- TEST MENU ---")
        print("1. Single Turn Loop (Mic -> AI -> TTS)")
        print("2. Continuous Conversation Loop (Sequential)")
        print("3. Concurrent Duplex Loop (Simultaneous Listen/Speak)")
        print("q. Quit")
        
        choice = input("Select an option: ").strip().lower()
        
        if choice == '1':
            await test_single_turn(args.provider)
        elif choice == '2':
            await test_continuous_loop(args.provider)
        elif choice == '3':
            await test_concurrent_loop(args.provider)
        elif choice == 'q':
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
