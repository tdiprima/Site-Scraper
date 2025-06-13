To watch process `627030` on RHEL (Red Hat Enterprise Linux):

### 🔁 Continuously Refresh a Snapshot

```bash
watch -n 1 "ps -p 627030 -o pid,ppid,cmd,%mem,%cpu"
```

To monitor memory usage while embedding:

```bash
htop
```

or, if GPU is involved:

```bash
watch -n 1 nvidia-smi
```
