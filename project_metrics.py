import numpy as np

# Data points from previous benchmark (Two-Tier HNSW)
N = np.array([5000, 10000, 30000])
RAM = np.array([2.44, 4.89, 14.65]) # MB
BuildTime = np.array([0.47, 1.86, 13.41]) # seconds
QPS = np.array([104.3, 56.75, 45.59])
Latency50 = np.array([8.99, 15.70, 18.40])

# Fit RAM (O(N) -> Linear)
# RAM = a * N
a_ram = np.mean(RAM / N)

# Fit Build Time (O(N log N))
# BuildTime = a * N * log(N)
N_log_N = N * np.log(N)
a_build = np.mean(BuildTime / N_log_N)

# Fit Latency (O(log N))
# Latency = a * log(N)
log_N = np.log(N)
a_latency = np.mean(Latency50 / log_N)

# Project to Big Data scales
scales = [10_000_000, 10_500_000, 11_000_000, 11_500_000, 12_000_000, 12_500_000]

print("| Quy mô (N) | Ước tính RAM (GB) | Build Time (Giờ) | Ước tính Latency p50 (ms) |")
print("| :--- | :--- | :--- | :--- |")
for n in scales:
    proj_ram = (a_ram * n) / 1024 # GB
    proj_build = (a_build * n * np.log(n)) / 3600 # Hours
    proj_lat = a_latency * np.log(n)
    
    print(f"| {n:,} | {proj_ram:.2f} GB | {proj_build:.2f} giờ | {proj_lat:.2f} ms |")
