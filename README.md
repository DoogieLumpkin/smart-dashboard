# 📊 Smart Server Dashboard

A lightweight web dashboard for monitoring your home server (CPU, RAM, disk usage) with live graphs and simple load forecasting.

## 🚀 Features

- Real-time **CPU**, **RAM**, and **HDD** usage
- History of last 30 measurements
- Live graphs using `matplotlib`
- Simple load forecast based on recent trends
- Auto-refresh every 5 seconds
- Smart advice (green/yellow/red)

## 🛠️ Installation & Usage

```bash
git clone https://github.com/DoogieLumpkin/smart-dashboard.git
cd smart-dashboard
python3 -m venv venv
source venv/bin/activate
pip install flask psutil matplotlib
python app.py

## 🐳 Run with Docker (optional)

```bash
docker build -t smart-dashboard .
docker run -p 5000:5000 smart-dashboard
