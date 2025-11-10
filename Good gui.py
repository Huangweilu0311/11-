import pymysql
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# ---------- MySQL 設定 ----------
DB_HOST = "localhost"
DB_USER = "mqttuser"
DB_PASSWORD = "gs5g4432"
DB_NAME = "adc_db"
TABLE_NAME = "adc_data"

# ---------- 參數設定 ----------
MAX_DT = 4            # ms，超過此值視為異常
MAX_POINTS = 2000      # 從資料庫最多讀幾筆
WINDOW_POINTS = 50    # 一個畫面顯示幾筆
POINT_INTERVAL = 2     # 每筆資料之間間隔 (ms)，用來設定 X 軸寬度

# ---------- 連線並抓資料 ----------
conn = pymysql.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME
)
cursor = conn.cursor()

# 取最新 MAX_POINTS 筆，依時間排序
sql = f"""
SELECT timestamp, value, dt_ms
FROM (
    SELECT timestamp, value, dt_ms FROM {TABLE_NAME}
    ORDER BY id DESC LIMIT {MAX_POINTS}
) AS sub
ORDER BY timestamp ASC
"""
cursor.execute(sql)
rows = cursor.fetchall()
conn.close()

# ---------- 解析資料 ----------
values = []
x_rel = []
acc_time = 0.0
frame_count = 0

for ts, value, dt in rows:
    # 跳過異常資料
    if dt is None or dt <= 0 or dt > MAX_DT:
        continue

    acc_time += dt
    x_rel.append(acc_time)
    values.append(value)

# ---------- 畫圖 ----------
fig, ax = plt.subplots(figsize=(20, 6))
line, = ax.plot([], [], marker='o', linestyle='-')

ax.set_xlabel("Time (ms)")
ax.set_ylabel("ADC Value (mV)")
ax.set_title("ADC Animation (reset every window)")
ax.grid(True)

# X 軸範圍 = 一個畫面顯示幾筆 * 2ms
x_range_ms = WINDOW_POINTS * POINT_INTERVAL
ax.set_xlim(0, x_range_ms)
ax.set_ylim(min(values) - 0.1, max(values) + 0.1)

def init():
    line.set_data([], [])
    return line,

def update(frame):
    global acc_time
    # 計算當前畫面要顯示的範圍
    start_idx = frame * WINDOW_POINTS
    end_idx = start_idx + WINDOW_POINTS
    if start_idx >= len(values):
        return line,  # 超過資料總長度就停止

    x_window = x_rel[start_idx:end_idx]
    y_window = values[start_idx:end_idx]

    if not x_window:
        return line,

    # 新畫面累積時間從0開始
    x0 = x_window[0]
    x_window = [x - x0 for x in x_window]

    line.set_data(x_window, y_window)
    return line,

# ---------- 動畫 ----------
# 幀數 = len(values)//WINDOW_POINTS，每幀顯示一個畫面
total_frames = (len(values) + WINDOW_POINTS - 1) // WINDOW_POINTS

ani = FuncAnimation(
    fig,
    update,
    frames=total_frames,
    init_func=init,
    blit=False,
    interval=2,  # 每個畫面停留時間(ms)，可調整
    repeat=False
)

plt.show()
