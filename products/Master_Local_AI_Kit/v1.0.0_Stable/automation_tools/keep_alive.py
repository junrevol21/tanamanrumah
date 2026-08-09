import ctypes, time
# Menggunakan API Windows untuk menonaktifkan sleep sementara skrip jalan
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002

print("Anti-Sleep Daemon aktif...")
while True:
    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED)
    time.sleep(300) # 5 menit
