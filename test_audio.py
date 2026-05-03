import sounddevice as sd
import numpy as np
import soundfile as sf

DEVICE_ID = 5        # CABLE Output
DURACION = 5         # segundos
SAMPLE_RATE = 16000

print(f"Grabando {DURACION} segundos desde dispositivo {DEVICE_ID}...")
print("¡Reproduce algo en Zoom o YouTube ahora!")

audio = sd.rec(
    int(DURACION * SAMPLE_RATE),
    samplerate=SAMPLE_RATE,
    channels=1,
    dtype='float32',
    device=DEVICE_ID
)
sd.wait()

sf.write("test_grabacion.wav", audio, SAMPLE_RATE)
volumen = np.abs(audio).mean()
print(f"Volumen promedio: {volumen:.4f}")

if volumen > 0.001:
    print("✅ Audio capturado correctamente")
else:
    print("⚠️ Silencio detectado - puede necesitar otro dispositivo")