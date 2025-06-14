#!/bin/bash
# Ubuntu 24.04 compatible

echo "===== System Information ====="

# CPU Cores
cores=$(nproc --all)
echo "CPU Cores: $cores"

# Total RAM
ram=$(free -h --si | awk '/^Mem:/ {print $2}')
echo "Total RAM: $ram"

# VRAM (NVIDIA GPUs)
if command -v nvidia-smi &> /dev/null; then
    vram=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1)
    echo "GPU VRAM (NVIDIA): ${vram} MiB"
else
    # Try lspci for other GPUs (just vendor/type, not VRAM)
    gpu_info=$(lspci | grep -Ei 'vga|3d|display')
    echo "GPU Info: $gpu_info"
    echo "VRAM: (Unable to detect - non-NVIDIA GPU or driver missing)"
fi

# Disk Space (root partition)
disk_total=$(df -h / | awk 'NR==2 {print $2}')
disk_avail=$(df -h / | awk 'NR==2 {print $4}')
echo "Root Filesystem Total: $disk_total"
echo "Root Filesystem Available: $disk_avail"

echo "============================="

# Optional: Exit with success
exit 0
