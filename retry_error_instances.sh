#!/bin/bash

# 设置基础目录
BASE_DIR=${1:-"/root/SWE-bench/remain_repos"}
RUN_ID=${2:-"0329"}
MAX_WORKERS=${3:-16}
TIMEOUT=${4:-1200}

# 遍历目录下的所有.jsonl文件
for file in ${BASE_DIR}/*.jsonl; do
    if [ -f "$file" ]; then
        echo "Processing file: $file"
        echo "=================================================="
        
        # 执行验证命令
        python -m swebench.harness.run_validation \
            --dataset_name "$file" \
            --split train \
            --max_workers $MAX_WORKERS \
            --timeout $TIMEOUT \
            --cache_level instance \
            --run_id $RUN_ID
        
        echo "Finished processing: $file"
        echo "=================================================="
    fi
done

echo "All files have been processed."