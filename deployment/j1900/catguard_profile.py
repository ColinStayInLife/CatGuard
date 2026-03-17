# CatGuard ONNX - 详细性能分析版本
import cv2
import time
import numpy as np
import onnxruntime as ort
from datetime import datetime
import sys

# 配置
ONNX_MODEL = r'C:\CatGuard\best.onnx'
CONFIDENCE_THRESHOLD = 0.7
LOG_FILE = r'C:\CatGuard\catguard_profile.log'

def log(msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

log("=" * 60)
log("CatGuard ONNX Performance Profiler")
log(f"Model: {ONNX_MODEL}")

# 加载模型
t_load_start = time.time()
session = ort.InferenceSession(ONNX_MODEL, providers=['CPUExecutionProvider'])
input_name = session.get_inputs()[0].name
t_load = (time.time() - t_load_start) * 1000
log(f"Model load time: {t_load:.1f}ms")
log(f"Input: {input_name}, Shape: {session.get_inputs()[0].shape}")

# 打开摄像头
cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

if not cap.isOpened():
    log("ERROR: Camera not available!")
    sys.exit(1)

log("Camera opened (640x480)")
log("Running 100 frames for profiling...\n")

# 性能统计
times = {
    'read': [],
    'resize': [],
    'cvtColor': [],
    'transpose': [],
    'inference': [],
    'softmax': [],
    'total': []
}

frame_count = 0
warmup = 10
profile_frames = 100

try:
    while frame_count < warmup + profile_frames:
        # 读取帧
        t0 = time.time()
        ret, frame = cap.read()
        t1 = time.time()
        
        if not ret:
            time.sleep(0.1)
            continue
        
        frame_count += 1
        
        # 预处理
        t_resize_start = time.time()
        img = cv2.resize(frame, (224, 224))
        t_resize = time.time() - t_resize_start
        
        t_cvt_start = time.time()
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        t_cvt = time.time() - t_cvt_start
        
        t_trans_start = time.time()
        img = np.transpose(img, (2, 0, 1))[None]
        t_trans = time.time() - t_trans_start
        
        # 推理
        t_inf_start = time.time()
        outputs = session.run(None, {input_name: img})[0]
        t_inf = time.time() - t_inf_start
        
        # Softmax
        t_soft_start = time.time()
        probs = np.exp(outputs[0]) / np.sum(np.exp(outputs[0]))
        t_soft = time.time() - t_soft_start
        
        t_total = time.time() - t0
        
        # 跳过 warmup 帧
        if frame_count > warmup:
            times['read'].append((t1 - t0) * 1000)
            times['resize'].append(t_resize * 1000)
            times['cvtColor'].append(t_cvt * 1000)
            times['transpose'].append(t_trans * 1000)
            times['inference'].append(t_inf * 1000)
            times['softmax'].append(t_soft * 1000)
            times['total'].append(t_total * 1000)
        
        # 每 20 帧输出进度
        if frame_count % 20 == 0:
            log(f"Progress: {frame_count - warmup}/{profile_frames}")

except Exception as e:
    log(f"Error: {e}")
finally:
    cap.release()

# 计算统计
log("\n" + "=" * 60)
log("Performance Analysis Results")
log("=" * 60)

log(f"\nTest frames: {profile_frames} (warmup: {warmup})")
log(f"Original resolution: 640x480")
log(f"Model input: 224x224")
log("\n")

# 输出统计表
log(f"{'Step':<15} {'Avg(ms)':<10} {'Min(ms)':<10} {'Max(ms)':<10} {'%Total':<10}")
log("-" * 55)

total_avg = sum(times['total']) / len(times['total'])

for step in ['read', 'resize', 'cvtColor', 'transpose', 'inference', 'softmax', 'total']:
    avg = sum(times[step]) / len(times[step])
    min_t = min(times[step])
    max_t = max(times[step])
    pct = (avg / total_avg * 100) if step != 'total' else 100.0
    log(f"{step:<15} {avg:<10.2f} {min_t:<10.2f} {max_t:<10.2f} {pct:<10.1f}%")

log("-" * 55)
log(f"\nTotal average: {total_avg:.2f}ms ({1000/total_avg:.1f} FPS)")

# 瓶颈分析
log("\n" + "=" * 60)
log("Bottleneck Analysis")
log("=" * 60)

steps = ['read', 'resize', 'cvtColor', 'transpose', 'inference', 'softmax']
sorted_steps = sorted(steps, key=lambda s: sum(times[s])/len(times[s]), reverse=True)

for i, step in enumerate(sorted_steps, 1):
    avg = sum(times[step]) / len(times[step])
    pct = avg / total_avg * 100
    log(f"{i}. {step}: {avg:.2f}ms ({pct:.1f}%)")

log("\n" + "=" * 60)