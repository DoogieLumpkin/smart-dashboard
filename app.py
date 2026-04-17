from flask import Flask, render_template_string
import psutil
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime, timedelta
import os

app = Flask(__name__)

HISTORY_FILE = 'history.txt'
MAX_HISTORY = 30

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, 'r') as f:
        lines = f.readlines()
    data = []
    for line in lines[-MAX_HISTORY:]:
        try:
            t, c, r, d = line.strip().split(',')
            data.append((float(t), float(c), float(r), float(d)))
        except:
            continue
    return data

def save_history(cpu, ram, disk):
    data = load_history()
    data.append((datetime.now().timestamp(), cpu, ram, disk))
    if len(data) > MAX_HISTORY:
        data = data[-MAX_HISTORY:]
    with open(HISTORY_FILE, 'w') as f:
        for ts, c, r, d in data:
            f.write(f"{ts},{c},{r},{d}\n")

def get_forecast():
    data = load_history()
    if len(data) < 5:
        return None, None, None
    # Берём последние 10 точек
    last_data = data[-10:]
    # Средний прирост за замер (между точками)
    cpu_changes = []
    ram_changes = []
    disk_changes = []
    for i in range(1, len(last_data)):
        cpu_changes.append(last_data[i][1] - last_data[i-1][1])
        ram_changes.append(last_data[i][2] - last_data[i-1][2])
        disk_changes.append(last_data[i][3] - last_data[i-1][3])
    avg_cpu_change = sum(cpu_changes) / len(cpu_changes)
    avg_ram_change = sum(ram_changes) / len(ram_changes)
    avg_disk_change = sum(disk_changes) / len(disk_changes)
    # Прогноз на 6 шагов вперёд (примерно 30-60 секунд)
    last_cpu = last_data[-1][1]
    last_ram = last_data[-1][2]
    last_disk = last_data[-1][3]
    forecast_cpu = max(0, min(100, last_cpu + avg_cpu_change * 6))
    forecast_ram = max(0, min(100, last_ram + avg_ram_change * 6))
    forecast_disk = max(0, min(100, last_disk + avg_disk_change * 6))
    return round(forecast_cpu), round(forecast_ram), round(forecast_disk)

def get_graph():
    data = load_history()
    if len(data) < 2:
        return None
    times = [datetime.fromtimestamp(ts).strftime('%H:%M:%S') for ts, _, _, _ in data]
    cpu_vals = [c for _, c, _, _ in data]
    ram_vals = [r for _, _, r, _ in data]
    disk_vals = [d for _, _, _, d in data]
    
    plt.figure(figsize=(10, 5))
    plt.plot(times, cpu_vals, label='CPU %', color='#4caf50', marker='o')
    plt.plot(times, ram_vals, label='RAM %', color='#ff9800', marker='s')
    plt.plot(times, disk_vals, label='HDD %', color='#f44336', marker='^')
    plt.xticks(rotation=45, ha='right', fontsize=8)
    plt.yticks(range(0, 101, 20))
    plt.ylim(0, 100)
    plt.legend()
    plt.tight_layout()
    
    img = io.BytesIO()
    plt.savefig(img, format='png', dpi=80)
    img.seek(0)
    plt.close()
    return base64.b64encode(img.getvalue()).decode()

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Smart Dashboard</title>
    <meta http-equiv="refresh" content="5">
    <style>
        body { font-family: sans-serif; background: #1e1e2f; color: white; text-align: center; padding: 20px; }
        .stat { font-size: 48px; margin: 10px; padding: 20px; background: #2d2d44; border-radius: 20px; display: inline-block; width: 180px; }
        .stat span { font-size: 20px; display: block; color: #aaa; }
        .forecast { font-size: 24px; margin-top: 10px; padding: 5px; border-radius: 12px; background: #1e1e2f; }
        .cpu { color: #4caf50; }
        .ram { color: #ff9800; }
        .disk { color: #f44336; }
        .advice { margin-top: 20px; padding: 15px; background: #2d2d44; border-radius: 20px; max-width: 500px; margin-left: auto; margin-right: auto; }
        .good { color: #4caf50; }
        .warning { color: #ff9800; }
        .danger { color: #f44336; }
        .graph { margin-top: 30px; background: #2d2d44; border-radius: 20px; padding: 20px; }
        img { max-width: 100%; border-radius: 10px; }
        .forecast-block { margin-top: 20px; padding: 15px; background: #2d2d44; border-radius: 20px; max-width: 600px; margin-left: auto; margin-right: auto; }
        .trend-up { color: #f44336; }
        .trend-down { color: #4caf50; }
        .trend-stable { color: #ff9800; }
    </style>
</head>
<body>
    <h1>📊 Smart Server Dashboard</h1>
    <div class="stat cpu">
        <span>CPU</span>
        {{ cpu }}%
    </div>
    <div class="stat ram">
        <span>RAM</span>
        {{ ram }}%
    </div>
    <div class="stat disk">
        <span>HDD</span>
        {{ disk }}%
    </div>
    
    {% if forecast_cpu is not none %}
    <div class="forecast-block">
        <h3>🔮 Прогноз на ближайшее время</h3>
        <div class="forecast">CPU: {{ forecast_cpu }}% &nbsp;| RAM: {{ forecast_ram }}% &nbsp;| HDD: {{ forecast_disk }}%</div>
        <p style="font-size: 12px; margin-top: 10px;">*Прогноз основан на изменении нагрузки за последние замеры</p>
    </div>
    {% endif %}
    
    <div class="advice">
        <h3>💡 Совет</h3>
        <p class="{{ advice_class }}">{{ advice_text }}</p>
    </div>
    
    {% if graph %}
    <div class="graph">
        <h3>📈 История нагрузки (последние {{ history_count }} замеров)</h3>
        <img src="data:image/png;base64,{{ graph }}" alt="График">
    </div>
    {% endif %}
    <p>Автообновление каждые 5 секунд | Данные сохраняются в history.txt</p>
</body>
</html>
'''

def get_advice(cpu, ram, disk):
    if cpu > 80:
        return "⚠️ Высокая нагрузка на CPU! Проверь процессы (htop)", "warning"
    if ram > 80:
        return "⚠️ Мало оперативной памяти! Добавь swap или закрой программы", "warning"
    if disk > 90:
        return "🔥 Диск почти заполнен! Почисти логи или удали лишнее", "danger"
    if cpu < 20 and ram < 50 and disk < 70:
        return "✅ Всё отлично! Сервер стабилен. Можно добавлять новые сервисы", "good"
    return "🟢 Сервер в норме. Нагрузка умеренная", "good"

@app.route('/')
def index():
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    
    save_history(cpu, ram, disk)
    advice_text, advice_class = get_advice(cpu, ram, disk)
    graph = get_graph()
    data = load_history()
    forecast_cpu, forecast_ram, forecast_disk = get_forecast()
    
    return render_template_string(HTML_TEMPLATE, 
                                  cpu=cpu, ram=ram, disk=disk,
                                  advice_text=advice_text, advice_class=advice_class,
                                  graph=graph, history_count=len(data),
                                  forecast_cpu=forecast_cpu, forecast_ram=forecast_ram, forecast_disk=forecast_disk)

if __name__ == '__main__':
    print("🚀 Smart Dashboard запущен! Открой в браузере: http://192.168.178.25:5000")
    app.run(host='0.0.0.0', port=5000)
