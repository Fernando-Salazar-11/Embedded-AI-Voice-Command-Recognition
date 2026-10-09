# Embedded AI Voice Command Recognition on STM32

Real-time, on-device voice command recognition (Keyword Spotting) running on an **STM32 NUCLEO-F401RE** microcontroller using **TinyML** and **Edge Impulse**.

This repository implements the complete end-to-end TinyML workflow, divided into two distinct operational modes:

1. **Phase A (Data Acquisition Firmware):** Continuous high-frequency audio sampling streaming over UART to create cloud datasets.

2. **Phase B (On-Device Inference Firmware):** Standalone, offline classification running an INT8-quantized neural network using memory-efficient chunked buffer slicing.

## 🛠️ What It Does

* **Phase A — Real-Time Dataset Generator:** Samples analog audio at 16 kHz via ADC+DMA and streams raw PCM data continuously to the Edge Impulse Data Forwarder via UART.

* **Phase B — Standalone Edge AI Classifier:** Runs an embedded TensorFlow Lite for Microcontrollers model to classify spoken keywords ( *"Now"*, *"Enciende"*, “Apaga”, *"Background Noise"*, *"Unknown"*) locally without internet connection or external compute.

* **RAM-Optimized Memory Management:** Prevents SRAM buffer overflows on the constrained ARM Cortex-M4 (96 KB SRAM) by using a dual ping-pong buffer during acquisition and incremental chunk-slicing during inference.

## 🚀 Technologies

* **Hardware:**

  * **MCU Board:** STMicroelectronics NUCLEO-F401RE (ARM Cortex-M4 @ 84 MHz, 96 KB SRAM, 512 KB Flash)

  * **Sensor:** Analog Electret / MEMS Microphone Module (e.g., MAX4466 / MAX9814)

* **Software & Toolchains:**

  * **IDE & Drivers:** STM32CubeIDE (HAL C/C++ Drivers for ADC, DMA, TIM, UART)

  * **ML Platform:** Edge Impulse Studio & Edge Impulse C++ SDK

  * **Runtime Engine:** TensorFlow Lite for Microcontrollers

  * **CLI Tooling:** Node.js & `edge-impulse-cli`

## 🧠 How It Works

### Architecture Diagram

```
========================================================================================
                               PHASE A: DATA CAPTURE MODE
========================================================================================
[ Micro ] ─► [ ADC1 + TIM ] ─► [ DMA Ping-Pong Buffer ] ─► [ UART Streaming ] ─► [ PC / Edge Impulse ]
                                 ├── Half-Buffer  (Chunk 1) ──► Transmit UART
                                 └── Full-Buffer  (Chunk 2) ──► Transmit UART

========================================================================================
                           PHASE B: REAL-TIME INFERENCE MODE
========================================================================================
[ Micro ] ─► [ ADC1 + TIM ] ─► [ Ping-Pong Chunk ] ──► [ Slice Ingest (100ms) ]
                                                              │
                                                              ▼
[ Command Result ] ◄── [ TFLite Model ] ◄── [ MFCC Features ] ◄── [ Sliding Window Buffer (1s) ]
========================================================================================

```

### Mode Breakdown

#### Phase A: Audio Capture & Streaming

1. A hardware timer triggers the 12-bit ADC at a strict **16 kHz sampling rate**.

2. The DMA engine continuously fills a double/ping-pong RAM buffer.

3. As soon as one half of the buffer fills, an interrupt fires and streams that block over UART to the host PC while the hardware fills the second half.

4. The **Edge Impulse Data Forwarder** ingests the UART stream and automatically uploads labeled samples to Edge Impulse Studio.

#### Phase B: On-Device Neural Network Inference

1. The microcontroller runs locally with the exported C++ neural network library embedded in Flash memory.

2. The microphone continuously feeds audio into tiny memory slices (e.g., 100 ms to 250 ms chunks).

3. These slices update a rolling 1-second sliding audio frame buffer without duplicating raw sample storage.

4. An **MFCC processing block** extracts spectral features from the 1-second frame.

5. The quantized INT8 model evaluates the features, predicts the spoken command, and outputs confidence scores via UART or controls on-board GPIOs (e.g., toggling LEDs).

## ⚙️ Key Implementation Details

### 1. Phase A: Ping-Pong Double-Buffering Strategy

To prevent dropped audio frames during serial transmission, Phase A utilizes a **Ping-Pong (Circular) Buffer** driven by DMA:

* **Non-Blocking Transfer:** `HAL_ADC_Start_DMA()` fills a global array in the background without clogging CPU cycles.

* **Interrupt Halves:**

  * `HAL_ADC_ConvHalfCpltCallback()` signals that **Buffer A** (first half) is ready. The CPU sends Buffer A over UART while the DMA fills **Buffer B**.

  * `HAL_ADC_ConvCpltCallback()` signals that **Buffer B** (second half) is ready. The CPU sends Buffer B while DMA wraps back to fill **Buffer A**.

* **Zero Audio Gaps:** This guarantees seamless 16 kHz audio capture without losing a single sample during transmission.

### 2. Phase B: Slice-Based Audio Feeding (RAM Overflow Prevention)

Storing multiple seconds of raw audio in SRAM alongside the neural network tensor arena would exceed the NUCLEO-F401RE’s 96 KB RAM limit. To solve this:

* **Incremental Chunk Slicing:** Instead of holding full multi-second recordings in RAM, the system captures small audio slices (e.g., 100 ms \~ 1600 samples).

* **Sliding Window Shift:** Each new slice overwrites only the oldest slice in a fixed-size 1-second ring buffer.

* **Low Tensor Arena Footprint:** By computing MFCC features and running inference strictly on the compact 1-second slice-updated window, RAM consumption remains under \~20–30 KB, leaving ample memory for stack, heap, and peripheral drivers.

## 💻 How to Run

### 1. Hardware Connections

| NUCLEO-F401RE Pin | Microphone Module | Function | 
| ----- | ----- | ----- | 
| **3V3** | VCC | 3.3V Power Supply | 
| **GND** | GND | Ground | 
| **PA0** (ADC1_IN0) | OUT / AO | Analog Audio Signal Output | 

### 2. Execution Steps

#### Phase A: Dataset Acquisition & Model Training

1. Open **STM32CubeIDE** and import the project located in `/Capture Send-Voice-ToTrain-AI`.

2. Compile and flash the firmware onto the NUCLEO-F401RE.

3. Connect your board via USB and run the Edge Impulse CLI forwarder:

   ```
   edge-impulse-data-forwarder
   
   ```

4. Configure the stream to **16000 Hz** and name the axis `audio`.

5. In Edge Impulse Studio, go to **Data Acquisition** and record spoken command keywords (*ON*, *OFF*, *Noise*, *Unknown*).

6. Design your Impulse:

   * **Window Size:** 1000 ms (Window Increase: 200 ms \~ 500 ms)

   * **DSP Block:** Audio (MFCC)

   * **Learning Block:** Classifier (Keras / TensorFlow Lite)

7. Train your model and convert it to **INT8 Quantized**.

#### Phase B: Deploy & Run Inference

1. In Edge Impulse Studio, navigate to **Deployment** $\rightarrow$ select **C++ Library** and click **Build**.

2. Unzip the exported C++ SDK into your Phase B inference firmware folder in STM32CubeIDE.

3. Compile and flash the **Main Inference Firmware** to the board.

4. Open a serial monitor (e.g., Tera Term, PuTTY, or STM32CubeIDE Terminal) at **115200 baud**.

5. Speak into the microphone. The microcontroller will display live keyword classification probabilities and execution time in real time!