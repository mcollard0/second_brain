import speech_recognition as sr
import asyncio
from concurrent.futures import ThreadPoolExecutor

class ASR:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        # Adjust energy threshold for silence detection if needed
        self.recognizer.energy_threshold = 300 
        self.recognizer.dynamic_energy_threshold = True
        self.executor = ThreadPoolExecutor(max_workers=1)

    async def listen(self) -> str:
        """
        Asynchronously listens for audio and returns the recognized text.
        Returns an empty string if speech is unintelligible.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self.executor, self._listen_sync)

    def _listen_sync(self) -> str:
        """
        Synchronous wrapper for speech_recognition listening and recognition.
        """
        try:
            with sr.Microphone() as source:
                print("Adjusting for ambient noise... (say something!)")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                print("Listening...")
                # timeout: seconds to wait for speech to start
                # phrase_time_limit: max seconds to record
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=15)
            
            print("Recognizing...")
            text = self.recognizer.recognize_google(audio)
            print(f"Recognized: {text}")
            return text
        
        except sr.WaitTimeoutError:
            print("Listening timed out (no speech detected).")
            return ""
        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand audio")
            return ""
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")
            return ""
        except Exception as e:
            print(f"An error occurred during ASR: {e}")
            return ""

if __name__ == "__main__":
    async def main():
        asr = ASR()
        print("Starting ASR test. Please speak.")
        text = await asr.listen()
        print(f"Final Result: {text}")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopping ASR test.")
 