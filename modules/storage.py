import aiofiles
import asyncio
import os

class Storage:
    def __init__(self, base_path: str = "."):
        self.base_path = base_path

    async def save(self, filename: str, content: str, mode: str = "a"):
        """
        Asynchronously writes content to a file.
        """
        filepath = os.path.join(self.base_path, filename)
        # Ensure directory exists if filename contains path separators
        dir_name = os.path.dirname(filepath)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
            
        async with aiofiles.open(filepath, mode=mode) as f:
            await f.write(content + "\n")
            
        print(f"Saved content to {filename}")
