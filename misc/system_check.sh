#!/bin/bash
# Ubuntu 24.04 compatible

# File output setup
date_str=$(date +"%Y-%m-%d")
outfile="system_check-$date_str.txt"

# Fun banner
echo "✨ SYSTEM CHECK INITIATED $(date '+%Y-%m-%d %H:%M') ✨" | tee "$outfile"
echo "-----------------------------------------------" | tee -a "$outfile"

# CPU Cores
cores=$(nproc --all)
echo "🧠 CPU Cores: $cores" | tee -a "$outfile"

# Total RAM
ram=$(free -h --si | awk '/^Mem:/ {print $2}')
echo "💾 Total RAM: $ram" | tee -a "$outfile"

# VRAM
if command -v nvidia-smi &> /dev/null; then
    vram=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1)
    echo "🎮 GPU VRAM (NVIDIA): ${vram} MiB" | tee -a "$outfile"
else
    gpu_info=$(lspci | grep -Ei 'vga|3d|display' | head -1)
    echo "🖥️ GPU Info: $gpu_info" | tee -a "$outfile"
    echo "❓ VRAM: Not detected (non-NVIDIA or no driver)" | tee -a "$outfile"
fi

# Disk space (root)
disk_total=$(df -h / | awk 'NR==2 {print $2}')
disk_avail=$(df -h / | awk 'NR==2 {print $4}')
echo "📦 Disk (Root) Total: $disk_total" | tee -a "$outfile"
echo "✅ Disk (Root) Free: $disk_avail" | tee -a "$outfile"

echo "-----------------------------------------------" | tee -a "$outfile"
echo "System check saved as $outfile 🚀" | tee -a "$outfile"

exit 0
