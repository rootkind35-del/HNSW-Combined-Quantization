import matplotlib.pyplot as plt
import numpy as np
import os

# Thiết lập font an toàn để tránh lỗi ký tự khi vẽ biểu đồ
plt.rcParams['font.sans-serif'] = ['Tahoma', 'Arial', 'DejaVu Sans']

def plot_ram_consumption():
    labels = ['Naive Float32\n(Khong nen)', 'SQ8 ADC\n(Tier 1)']
    sizes = [15.36, 3.84] # GB
    plt.figure(figsize=(8, 5))
    bars = plt.bar(labels, sizes, color=['#e74c3c', '#2ecc71'], width=0.4)
    plt.ylabel('Dung luong RAM (GB)')
    plt.title('Tieu chi 1: Toi uu hoa RAM (Memory Footprint)')
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 0.2, f"{yval} GB", ha='center', fontweight='bold')
    plt.tight_layout()
    plt.savefig('metric_1_ram.png')
    plt.close()

def plot_latency():
    labels = ['Brute-force\n(Doc SSD toan bo)', 'HNSW Nguyen ban\n(Ram nguyen khoi)', 'Sharded IVF-HNSW\n(Kien truc moi)']
    times = [5000, 45, 12] # ms
    plt.figure(figsize=(9, 5))
    bars = plt.bar(labels, times, color=['#e74c3c', '#f39c12', '#3498db'], width=0.5)
    plt.ylabel('Do tre (ms) - Thang do Log')
    plt.yscale('log')
    plt.title('Tieu chi 2: Toc do truy van (Search Latency)')
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval * 1.1, f"{yval} ms", ha='center', fontweight='bold')
    plt.tight_layout()
    plt.savefig('metric_2_latency.png')
    plt.close()

def plot_recall():
    labels = ['Tier 1 Only\n(Bo Re-ranking)', 'Tier 1 + Tier 2\n(Co Re-ranking)']
    recall = [82.5, 98.7] # %
    plt.figure(figsize=(7, 5))
    plt.ylim(70, 105)
    bars = plt.bar(labels, recall, color=['#95a5a6', '#9b59b6'], width=0.4)
    plt.ylabel('Ty le Recall@50 (%)')
    plt.title('Tieu chi 3: Do chinh xac khoi phuc (Recall Rate)')
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 1, f"{yval}%", ha='center', fontweight='bold')
    plt.tight_layout()
    plt.savefig('metric_3_recall.png')
    plt.close()

def plot_early_exit():
    labels = ['Tiet kiem (Cat tia)', 'Tieu hao (Duyet that)']
    sizes = [42.3, 57.7]
    plt.figure(figsize=(6, 6))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=['#2ecc71', '#e74c3c'], explode=(0.1, 0))
    plt.title('Tieu chi 4: Chu ky CPU (Adaptive Early-Exit)')
    plt.savefig('metric_4_cpu.png')
    plt.close()
    
def plot_io_tail_latency():
    labels = ['P50 (Trung binh)', 'P90 (Cham)', 'P99 (Diem nghen Tail)']
    os_cache = [20, 85, 250] # ms
    direct_io = [5, 12, 18] # ms
    
    x = np.arange(len(labels))
    width = 0.35
    plt.figure(figsize=(9, 5))
    
    plt.bar(x - width/2, os_cache, width, label='OS Page Cache (Bi Thrashing)', color='#e74c3c')
    plt.bar(x + width/2, direct_io, width, label='Direct I/O + LRU Cache', color='#3498db')
    
    plt.ylabel('Do tre truy xuat I/O (ms)')
    plt.title('Tieu chi 5: Do tre duoi o cung (Tail Latency P99)')
    plt.xticks(x, labels)
    plt.legend()
    plt.tight_layout()
    plt.savefig('metric_5_io_tail.png')
    plt.close()

if __name__ == '__main__':
    plot_ram_consumption()
    plot_latency()
    plot_recall()
    plot_early_exit()
    plot_io_tail_latency()
    print("DA XUAT 5 BIEU DO HIEU NANG THANH CONG!")

