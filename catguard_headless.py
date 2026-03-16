# CatGuard 无头版 - 详细耗时日志（每帧打印）
import cv2
import time
import os
import winsound
from ultralytics import YOLO
from datetime import datetime
import sys

# ============ 配置 ============
MODEL_PATH = r'C:\CatGuard\best.pt'
ALERT_SOUND = r'C:\Windows\Media\Alarm01.wav'
CAMERA_INDEX = 0

# 阈值配置
LOG_THRESHOLD = 0.50        # 日志记录阈值
ALERT_THRESHOLD = 0.70      # 警报触发阈值
ALERT_COOLDOWN = 3          # 警报冷却时间（秒）
SAMPLE_INTERVAL = 3         # 采样间隔（每N帧检测一次）

# 日志路径
LOG_FILE = r'C:\CatGuard\catguard.log'
DIAGNOSIS_BASE_DIR = r'C:\CatGuard\diagnosis'

# ============ 获取当日诊断目录 ============
def get_today_dir():
    date_str = datetime.now().strftime('%Y%m%d')
    return os.path.join(DIAGNOSIS_BASE_DIR, date_str)

# ============ 初始化诊断目录 ============
def init_diagnosis_dir():
    today_dir = get_today_dir()
    if not os.path.exists(today_dir):
        os.makedirs(today_dir)

# ============ 保存诊断帧 ============
def save_diagnosis_frame(frame, label, confidence, is_alert=False):
    save_start = time.time()
    
    today_dir = get_today_dir()
    if not os.path.exists(today_dir):
        os.makedirs(today_dir)
    
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    filename = f'ALERT_{timestamp}.jpg' if is_alert else f'{timestamp}.jpg'
    filepath = os.path.join(today_dir, filename)
    
    cv2.imwrite(filepath, frame)
    
    diagnosis_log = os.path.join(today_dir, 'diagnosis.log')
    alert_flag = 'ALERT' if is_alert else 'LOG'
    log_line = f'{timestamp}|{filename}|{label}|{confidence:.4f}|{alert_flag}\n'
    with open(diagnosis_log, 'a', encoding='utf-8') as f:
        f.write(log_line)
    
    save_time = (time.time() - save_start) * 1000
    return filepath, save_time

# ============ 播放音频警报 ============
def play_alert():
    audio_start = time.time()
    try:
        winsound.PlaySound(ALERT_SOUND, winsound.SND_FILENAME | winsound.SND_ASYNC)
    except Exception as e:
        pass
    audio_time = (time.time() - audio_start) * 1000
    return audio_time

# ============ 日志函数 ============
def log(msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    line = f'[{timestamp}] {msg}'
    print(line, flush=True)
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except:
        pass

# ============ 主程序 ============
if __name__ == '__main__':
    init_diagnosis_dir()
    
    log('=' * 60)
    log('CatGuard 启动 (详细耗时日志 - 每帧打印)')
    log(f'模型: {MODEL_PATH}')
    log(f'摄像头索引: {CAMERA_INDEX}')
    log(f'日志记录阈值: {LOG_THRESHOLD}')
    log(f'警报触发阈值: {ALERT_THRESHOLD}')
    log(f'警报冷却: {ALERT_COOLDOWN}秒')
    log(f'采样间隔: 每 {SAMPLE_INTERVAL} 帧检测 1 次')
    log(f'音频播放: 仅 positive 时触发')
    
    # 加载模型
    log('加载模型...')
    model = YOLO(MODEL_PATH)
    log(f'模型加载完成! 类别: {model.names}')
    
    # 打开摄像头
    log('打开摄像头...')
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        log('错误: 无法打开摄像头!')
        sys.exit(1)
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    log('摄像头已就绪')
    
    # 状态变量
    last_alert_time = 0
    frame_count = 0
    fps_start = time.time()
    fps_count = 0
    alert_count = 0
    log_count = 0
    detection_count = 0
    
    log('开始监控...')
    log('─' * 60)
    
    try:
        while True:
            frame_start = time.time()
            
            # === 1. 摄像头读取 ===
            camera_start = time.time()
            ret, frame = cap.read()
            camera_time = (time.time() - camera_start) * 1000
            
            if not ret:
                log('警告: 无法读取帧')
                time.sleep(0.1)
                continue
            
            frame_count += 1
            fps_count += 1
            
            # FPS 计算（每秒打印一次）
            if time.time() - fps_start >= 1.0:
                fps = fps_count / (time.time() - fps_start)
                log(f'[FPS] {fps:.1f}')
                fps_start = time.time()
                fps_count = 0
            
            # 采样间隔
            if frame_count % SAMPLE_INTERVAL != 0:
                continue
            
            detection_count += 1
            
            # === 2. 图片预处理 ===
            preprocess_start = time.time()
            preprocess_time = (time.time() - preprocess_start) * 1000
            
            # === 3. 模型推理 ===
            inference_start = time.time()
            results = model(frame, verbose=False)
            inference_time = (time.time() - inference_start) * 1000
            
            # === 4. 结果后处理 ===
            postprocess_start = time.time()
            result = results[0]
            label = result.names[result.probs.top1]
            confidence = result.probs.top1conf.item()
            postprocess_time = (time.time() - postprocess_start) * 1000
            
            current_time = time.time()
            
            # 判断是否触发
            is_alert = (label == 'positive' and 
                       confidence >= ALERT_THRESHOLD and 
                       (current_time - last_alert_time >= ALERT_COOLDOWN))
            
            is_log = (label == 'positive' and confidence >= LOG_THRESHOLD)
            
            # === 5. 图片保存（如果需要） ===
            save_time = 0
            filepath = ''
            if is_log:
                filepath, save_time = save_diagnosis_frame(frame, label, confidence, is_alert)
                log_count += 1
            
            # === 6. 播放音频（仅 positive 时触发） ===
            audio_time = 0
            if label == 'positive':
                audio_time = play_alert()
            
            if is_alert:
                alert_count += 1
                last_alert_time = current_time
            
            # === 计算总耗时 ===
            total_time = (time.time() - frame_start) * 1000
            
            # === 打印每帧详细耗时 ===
            log(f'[帧#{detection_count}] 读取={camera_time:.0f}ms | 预处理={preprocess_time:.0f}ms | 推理={inference_time:.0f}ms | 后处理={postprocess_time:.0f}ms | 保存={save_time:.0f}ms | 音频={audio_time:.0f}ms | 总计={total_time:.0f}ms')
            log(f'         结果: {label} ({confidence:.2f}) {"⚠️ ALERT" if is_alert else "📝 LOG" if is_log else "➖ 跳过"}')
            
            if is_alert:
                log(f'         警报#{alert_count}! 保存: {filepath}')
    
    except KeyboardInterrupt:
        log('收到停止信号')
    except Exception as e:
        log(f'错误: {e}')
        import traceback
        traceback.print_exc()
    
    cap.release()
    log('─' * 60)
    log(f'CatGuard 已停止 | 检测={detection_count} | 记录={log_count} | 警报={alert_count}')
    log('=' * 60)