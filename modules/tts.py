import asyncio
import websockets
import json
import base64
import os
import pyaudio
import audioop

class TTS:
    def __init__(self, voice_id=None):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY not found in environment variables.")
        
        # Use provided voice_id, or env var, or default to LjNqOSdRGIUUmAcEINh7
        if voice_id is None:
            self.voice_id = os.getenv("ELEVENLABS_VOICE_ID", "LjNqOSdRGIUUmAcEINh7")
        else:
            self.voice_id = voice_id

        # Request raw PCM 24000Hz (Free Tier compatible)
        self.uri = f"wss://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}/stream-input?model_id=eleven_flash_v2_5&output_format=pcm_24000"
        
        # Audio setup
        self.p = pyaudio.PyAudio()
        
        # Get device index from env if set (Default 21)
        device_index_env = os.getenv("AUDIO_OUTPUT_INDEX", "21")
        try:
            device_index = int(device_index_env)
        except ValueError:
            print(f"Invalid AUDIO_OUTPUT_INDEX: {device_index_env}, using default 21.")
            device_index = 21
        
        # Get channels from env (Default 2)
        self.channels = 2
        env_channels = os.getenv("AUDIO_CHANNELS", "2")
        try:
            self.channels = int(env_channels)
        except ValueError:
            self.channels = 2 

        self.stream = self.p.open(format=pyaudio.paInt16,
                                  channels=self.channels,
                                  rate=24000,
                                  output=True,
                                  output_device_index=device_index)
        
        self.debug_file = "/tmp/elevenlabs_debug.pcm"
        # Clear debug file on init
        try:
            with open(self.debug_file, "wb") as f:
                pass
            print(f"[TTS DEBUG] cleared {self.debug_file}")
        except Exception as e:
            print(f"[TTS DEBUG] start file error: {e}")

    async def _process_and_play(self, data_json):
        if data_json.get("audio"):
            audio_data = base64.b64decode(data_json["audio"])
            
            # Debug logging
            print(f"[TTS DEBUG] Received chunk: {len(audio_data)} bytes (B64: {len(data_json['audio'])})")
            try:
                with open(self.debug_file, "ab") as f:
                    f.write(audio_data)
            except Exception as e:
                print(f"[TTS DEBUG] Error writing to debug file: {e}")

            # If we decoded MP3, we would need pydub here. But checking header, we requested PCM.
            # However, if channels=2, upmix mono -> stereo
            if self.channels == 2:
                # audioop.tostereo(fragment, width, lfactor, rfactor)
                # width=2 (16-bit)
                try:
                    audio_data = audioop.tostereo(audio_data, 2, 1, 1)
                except Exception as e:
                    print(f"Error upmixing: {e}")
            
            # If channels > 2, we might be sending mono to multi-channel stream.
            # Result depends on OS mixing.
            
            self.stream.write(audio_data)
        else:
            print(f"[TTS DEBUG] Received non-audio message: {data_json.keys()}")

    async def stream_audio(self, text_iterator):
        """
        Connects to ElevenLabs WebSocket and streams audio.
        text_iterator: An async iterator yielding text chunks.
        """
        async with websockets.connect(self.uri) as websocket:
            # Sender task: sends text to WebSocket
            async def send_text():
                # Start frame
                payload = {
                    "text": " ",
                    "voice_settings": {"stability": 0.5, "similarity_boost": 0.8},
                    "xi_api_key": self.api_key, 
                }
                print(f"[TTS DEBUG] Sending init payload: {payload}")
                await websocket.send(json.dumps(payload))

                async for text in text_iterator:
                    if text.strip():
                        print(f"[TTS DEBUG] Streaming text: '{text}'")
                        await websocket.send(json.dumps({"text": text + " ", "try_trigger_generation": True}))
                
                # End of stream
                print("[TTS DEBUG] Sending EOS")
                await websocket.send(json.dumps({"text": ""}))

            # Receiver task: plays audio
            async def receive_audio():
                while True:
                    try:
                        message = await websocket.recv()
                        data = json.loads(message)
                        await self._process_and_play(data)
                        
                        if data.get("isFinal"):
                            print("[TTS DEBUG] Received isFinal signal")
                            break
                    except websockets.exceptions.ConnectionClosed:
                        print("[TTS DEBUG] WebSocket connection closed")
                        break
            pass

    async def speak(self, text: str):
        """
        Simple wrapper for single text string.
        """
        async def text_gen():
            yield text
        
        # Re-implement logic with headers correct for the connection
        async with websockets.connect(self.uri, additional_headers={"xi-api-key": self.api_key}) as websocket:
            # Initial config
            init_payload = {
                "text": " ",
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
            }
            print(f"[TTS DEBUG] Sending Init: {init_payload}")
            await websocket.send(json.dumps(init_payload))

            # Send text
            print(f"[TTS DEBUG] Sending Text: '{text}'")
            await websocket.send(json.dumps({"text": text, "try_trigger_generation": True}))
            await websocket.send(json.dumps({"text": ""})) # EOS

            while True:
                try:
                    message = await websocket.recv()
                    data = json.loads(message)
                    await self._process_and_play(data)
                    
                    if data.get("isFinal"):
                        print("[TTS DEBUG] Stream Complete (isFinal)")
                        break
                except websockets.exceptions.ConnectionClosed as e:
                    print(f"[TTS DEBUG] Connection Closed: {e}")
                    break

    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
