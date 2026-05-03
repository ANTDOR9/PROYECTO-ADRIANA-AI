import sounddevice as sd
import numpy as np

# Dispositivos candidatos a probar
candidatos = [
    (2,  "Voicemeeter Out A4"),
    (3,  "Voicemeeter Out B3"),
    (4,  "Voicemeeter Out A1"),
    (5,  "CABLE Output"),
    (9,  "Voicemeeter Out B1"),
    (10, "Voicemeeter Out B2"),
]

DURACION = 3
SAMPLE_RATE = 16000

print("🎵 Reproduce algo en YouTube AHORA y no pares...")
print()

for device_id, nombre in candidatos:
    try:
        audio = sd.rec(
            int(DURACION * SAMPLE_RATE),
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype='float32',
            device=device_id
        )
        sd.wait()
        volumen = np.abs(audio).mean()
        estado = "✅ TIENE AUDIO" if volumen > 0.001 else "❌ silencio"
        print(f"Dispositivo {device_id:2d} | {nombre:25s} | vol={volumen:.4f} | {estado}")
    except Exception as e:
        print(f"Dispositivo {device_id:2d} | {nombre:25s} | ERROR: {e}")