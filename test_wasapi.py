import pyaudiowpatch as pyaudio
import numpy as np

p = pyaudio.PyAudio()

# Buscar dispositivo loopback automáticamente
wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])

if not default_speakers.get("isLoopbackDevice", False):
    for loopback in p.get_loopback_device_info_generator():
        if default_speakers["name"] in loopback["name"]:
            default_speakers = loopback
            break

print(f"✅ Capturando desde: {default_speakers['name']}")

chunk = 1024
sample_rate = int(default_speakers["defaultSampleRate"])
channels = int(default_speakers["maxInputChannels"])

stream = p.open(
    format=pyaudio.paFloat32,
    channels=channels,
    rate=sample_rate,
    input=True,
    input_device_index=default_speakers["index"],
    frames_per_buffer=chunk
)

print("🎵 Reproduce YouTube ahora — midiendo volumen 5 segundos...")
volumenes = []
for _ in range(int(sample_rate / chunk * 5)):
    data = np.frombuffer(stream.read(chunk), dtype=np.float32)
    volumenes.append(np.abs(data).mean())

stream.stop_stream()
stream.close()
p.terminate()

vol_promedio = np.mean(volumenes)
print(f"Volumen promedio: {vol_promedio:.4f}")
print("✅ AUDIO OK" if vol_promedio > 0.001 else "⚠️ Sin audio detectado")