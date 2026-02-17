import pyaudio

def list_audio_devices():
    p = pyaudio.PyAudio()
    info = p.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')
    
    input_devices = []
    output_devices = []

    for i in range(0, numdevices):
        device_info = p.get_device_info_by_host_api_device_index(0, i)
        if (device_info.get('maxInputChannels')) > 0:
            input_devices.append((i, device_info.get('name'), device_info.get('maxInputChannels'), device_info.get('defaultSampleRate')))
        if (device_info.get('maxOutputChannels')) > 0:
            output_devices.append((i, device_info.get('name'), device_info.get('maxOutputChannels'), device_info.get('defaultSampleRate')))

    p.terminate()
    return input_devices, output_devices

if __name__ == "__main__":
    inputs, outputs = list_audio_devices()
    
    print("\n--- Input Devices ---")
    print(f"{'Index':<6} {'Name':<40} {'Ch':<5} {'Rate':<8}")
    for idx, name, ch, rate in inputs:
        print(f"{idx:<6} {name[:38]:<40} {ch:<5} {int(rate):<8}")

    print("\n--- Output Devices ---")
    print(f"{'Index':<6} {'Name':<40} {'Ch':<5} {'Rate':<8}")
    for idx, name, ch, rate in outputs:
        print(f"{idx:<6} {name[:38]:<40} {ch:<5} {int(rate):<8}")
