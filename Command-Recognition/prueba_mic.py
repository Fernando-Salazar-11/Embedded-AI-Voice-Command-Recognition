import serial
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Configuración
PUERTO = 'COM3'
BAUDIOS = 921600
SAMPLES_PER_FRAME = 1600 # Debe coincidir con LIVE_SAMPLES del micro

ser = serial.Serial(PUERTO, BAUDIOS)

# Preparar la figura
fig, ax = plt.subplots()
x = np.arange(0, SAMPLES_PER_FRAME)
line, = ax.plot(x, np.ones(SAMPLES_PER_FRAME) * 2048)
ax.set_ylim(0, 4095) # Rango del ADC
ax.set_title("Micrófono en Tiempo Real")
ax.grid(True)

def update(frame):
    # Leer el bloque de bytes (cada muestra son 2 bytes uint16)
    data_raw = ser.read(SAMPLES_PER_FRAME * 2)
    
    # Convertir bytes a array de enteros (little-endian unsigned short)
    y = np.frombuffer(data_raw, dtype=np.uint16)
    
    if len(y) == SAMPLES_PER_FRAME:
        line.set_ydata(y)
    return line,

ani = FuncAnimation(fig, update, interval=10, blit=True)
plt.show()
ser.close()