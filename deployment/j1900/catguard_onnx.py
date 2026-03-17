# CatGuard ONNX - 15 FPS 带日志版本
import cv2
import time
import numpy as np
import onnxruntime as ort
from datetime import datetime
import sys

# 配置
ONNX_MODEL = r'C:\CatGuard\best.onnx'
CONFIDENCE_THRESHOLD = 0.7
COOLDOWN_SECONDS = 3
LOG_FILE = r'C:\CatGuard\catguard_onnx.log'

def log(msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

log("=" * 50)
log("CatGuard ONNX Starting...")
log(f"Model: {ONNX_MODEL}")
log(f"Threshold: {CONFIDENCE_THRESHOLD}")

# 加载模型
session = ort.InferenceSession(ONNX_MODEL, providers=['CPUExecutionProvider'])
input_name = session.get_inputs()[0].name
log(f"Model loaded: {input_name}")

# 打开摄像头
cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

if not cap.isOpened():
    log("ERROR: Camera not available!")
    sys.exit(1)

log("Camera opened, starting monitoring...")

# 状态
last_alert_time = 0
frame_count = 0
fps_times = []

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            log("Frame error")
            time.sleep(0.1)
            continue

        frame_count += 1
        t0 = time.time()

        # 预处理
        img = cv2.resize(frame, (224, 224))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        img = np.transpose(img, (2, 0, 1))[None]

        # ONNX 推理
        outputs = session.run(None, {input_name: img})[0]
        probs = np.exp(outputs[0]) / np.sum(np.exp(outputs[0]))
        positive_prob = probs[1]

        elapsed = (time.time() - t0) * 1000
        fps_times.append(elapsed)
        if len(fps_times) > 30:
            fps_times.pop(0)

        # 检测
        now = time.time()
        if positive_prob > CONFIDENCE_THRESHOLD and (now - last_alert_time) > COOLDOWN_SECONDS:
            last_alert_time = now
            log(f"ALERT! Frame={frame_count} pos={positive_prob:.2f}")

        # 每 100 帧输出状态
        if frame_count % 100 == 0:
            avg_ms = sum(fps_times) / len(fps_times)
            fps = 1000 / avg_ms
            log(f"Frame {frame_count}: {avg_ms:.1f}ms ({fps:.1f} FPS)")

except KeyboardInterrupt:
    log("Stopped by user")
except Exception as e:
    log(f"Error: {e}")
finally:
    cap.release()
    log("Camera released")