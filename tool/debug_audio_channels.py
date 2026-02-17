import pyaudio
import sys

def test_audio_configurations():
    p = pyaudio.PyAudio()
    info = p.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')
    
    print(f"\nScanning {numdevices} audio devices for valid output configurations...")
    print(f"{'Index':<6} {'Name':<30} {'Ch':<4} {'Rate':<8} {'Status':<10}")
    print("-" * 65)

    valid_configs = []

    # Iterate over devices
    for i in range(0, numdevices):
        try:
            device_info = p.get_device_info_by_host_api_device_index(0, i)
        except Exception:
            continue
            
        max_output_channels = device_info.get('maxOutputChannels')
        if max_output_channels <= 0:
            continue
            
        name = device_info.get('name')
        
        # Test common channel counts
        # Many Linux systems with PipeWire/Pulse report high max channels (e.g. 32) 
        # but accept 1, 2, or specific counts like 6 (5.1).
        test_channels = [1, 2, max_output_channels]
        if max_output_channels > 2:
             # Add other likely configs if max is high
             if 6 <= max_output_channels: test_channels.append(6)
             if 8 <= max_output_channels: test_channels.append(8)
        
        test_channels = sorted(list(set(test_channels)))

        for ch in test_channels:
            try:
                # Attempt to open a stream (no actual audio written)
                stream = p.open(format=pyaudio.paInt16,
                                channels=ch,
                                rate=44100,
                                output=True,
                                output_device_index=i)
                stream.close()
                print(f"{i:<6} {name[:28]:<30} {ch:<4} {44100:<8} {'OK':<10}")
                valid_configs.append((i, name, ch))
            except Exception as e:
                # print(f"{i:<6} {name[:28]:<30} {ch:<4} {44100:<8} {'FAIL':<10} {str(e)}")
                pass
                
    p.terminate()
    
    print("\n--- Summary of Valid Configurations ---")
    if not valid_configs:
        print("No valid output configurations found.")
    else:
        for idx, name, ch in valid_configs:
            print(f"Device {idx} ({name}): Supports {ch} channels")
            
        print("\n--- Recommendation ---")
        # Heuristic: Prefer Pulse/PipeWire/Default with 2 channels, then 1 channel
        preferred = [c for c in valid_configs if 'pulse' in c[1].lower() or 'pipewire' in c[1].lower() or 'default' in c[1].lower()]
        
        stereo = [c for c in preferred if c[2] == 2]
        mono = [c for c in preferred if c[2] == 1]
        
        if stereo:
            best = stereo[0]
            print(f"Best Match: Device {best[0]} ({best[1]}) with {best[2]} channels.")
            print(f"Run: export AUDIO_OUTPUT_INDEX={best[0]} && export AUDIO_CHANNELS={best[2]}")
        elif mono:
            best = mono[0]
            print(f"Fallback Match: Device {best[0]} ({best[1]}) with {best[2]} channels.")
            print(f"Run: export AUDIO_OUTPUT_INDEX={best[0]} && export AUDIO_CHANNELS={best[2]}")
        elif valid_configs:
            best = valid_configs[0]
            print(f"Hardware Match: Device {best[0]} ({best[1]}) with {best[2]} channels.")
            print(f"Run: export AUDIO_OUTPUT_INDEX={best[0]} && export AUDIO_CHANNELS={best[2]}")


if __name__ == "__main__":
    test_audio_configurations()
