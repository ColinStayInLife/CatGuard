# CatGuard - 猫咪卫士

基于边缘 AI 的猫咪乱尿预防系统，在猫咪排尿前识别蹲姿并触发警报。

## 功能

- 🎯 实时检测猫咪蹲姿（排尿前兆）
- 🔔 音频警报打断猫咪行为
- 📊 双阈值日志记录系统
- 💻 边缘部署，隐私不上云

## 技术栈

- **模型**: YOLOv8n-cls (图像分类)
- **推理**: Ultralytics + OpenCV
- **部署**: Windows 计划任务 / Linux Systemd
- **硬件**: J1900 CPU (2.7 FPS)

## 项目结构

```
CatGuard/
├── catguard_headless.py    # 主程序
├── best.pt                 # YOLOv8 模型
├── diagnosis/              # 诊断日志目录
│   └── YYYYMMDD/
│       ├── diagnosis.log   # 检测日志
│       └── *.jpg           # 检测图片
└── catguard.log            # 运行日志
```

## 快速开始

### 1. 安装依赖

```bash
pip install ultralytics opencv-python
```

### 2. 准备模型

将训练好的 YOLOv8 分类模型放到 `C:\CatGuard\best.pt`

### 3. 运行

```bash
python catguard_headless.py
```

## 配置参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| LOG_THRESHOLD | 0.50 | 日志记录阈值 |
| ALERT_THRESHOLD | 0.70 | 警报触发阈值 |
| ALERT_COOLDOWN | 3 | 警报冷却时间（秒） |
| SAMPLE_INTERVAL | 3 | 采样间隔（帧） |

## 模型性能

| 指标 | 数值 |
|------|------|
| 准确率 | 87.3% |
| 正例召回率 | 100% |
| 推理速度 | ~1s (J1900 CPU) |
| FPS | 2.7 |

## 训练数据

- 数据量: 600 张图片
- 类别: positive (蹲姿) / negative (正常)
- 来源: AI 生成 (Z-Image Turbo)

## License

MIT