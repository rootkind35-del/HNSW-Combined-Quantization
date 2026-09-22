import os
import sys

patterns = [
    'data_product_studio',
    'data_product.css',
    'quantization_benchmark',
    'speed_benchmark',
    'auto_search_evaluator',
    'three_engine',
    'three_hnsw_graph',
    'three_pipeline_3d',
    'three_vector_space',
    'dimension_reduction_3d',
    'init3DEngine'
]

targets = ['dashboard/public', 'dashboard/server.js', 'dashboard/scripts']
found = {}

for target in targets:
    if os.path.isfile(target):
        files = [target]
    else:
        files = [os.path.join(root, f) for root, _, fs in os.walk(target) for f in fs]
    
    for filepath in files:
        if filepath.endswith(('.html', '.js', '.css', '.py')):
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                for p in patterns:
                    if p in content:
                        found.setdefault(p, []).append(filepath)

print("--- Cleanup Pattern Search Results ---")
all_clean = True
for p in patterns:
    matches = found.get(p, [])
    if matches:
        all_clean = False
        print(f"FOUND {p}: {matches}")
    else:
        print(f"CLEAN {p}: None")

if all_clean:
    print("ALL CLEAN: Zero orphaned references found.")
else:
    print("WARNING: Orphaned references exist!")
