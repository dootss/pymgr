import ctypes
import os
import time
import sys
os.system('') # actually enables ansi escape codes on my system
sys.stdout.write('\033[?25l')
sys.stdout.flush()


class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength",                 ctypes.c_ulong),         # size of struct in bytes
        ("dwMemoryLoad",             ctypes.c_ulong),         # percent of memory in use
        ("ullTotalPhys",             ctypes.c_ulonglong),     # total physical memory in bytes
        ("ullAvailPhys",             ctypes.c_ulonglong),     # available physical memory in bytes
        ("ullTotalPageFile",         ctypes.c_ulonglong),     # total page file size in bytes
        ("ullAvailPageFile",         ctypes.c_ulonglong),     # available page file size in bytes
        ("ullTotalVirtual",          ctypes.c_ulonglong),     # total virtual memory in bytes
        ("ullAvailVirtual",          ctypes.c_ulonglong),     # available virtual memory in bytes
        ("sullAvailExtendedVirtual", ctypes.c_ulonglong),     # reserved for windows, always 0
    ]



class FILETIME(ctypes.Structure):
    _fields_ = [
        ("dwLowDateTime",  ctypes.c_ulong), # low-order part of file time
        ("dwHighDateTime", ctypes.c_ulong), # high-order part of the file time
    ]

kernel32 = ctypes.WinDLL('kernel32')
GetSystemTimes = kernel32.GetSystemTimes
GlobalMemoryStatusEx = kernel32.GlobalMemoryStatusEx

GlobalMemoryStatusEx.argtypes = [ctypes.POINTER(MEMORYSTATUSEX)]
GlobalMemoryStatusEx.restype = ctypes.c_bool
GetSystemTimes.argtypes = [ctypes.POINTER(FILETIME), ctypes.POINTER(FILETIME), ctypes.POINTER(FILETIME)]
GetSystemTimes.restype = ctypes.c_bool

def get_colored_bar(percentage, length=40):
    filled_length = int(length * percentage // 100)

    if percentage < 50:
        color = '\033[92m'  # green
    elif percentage < 75:
        color = '\033[93m'  # yellow
    else:
        color = '\033[91m'  # red

    bar = color + '█' * filled_length + '\033[0m' + '-' * (length - filled_length)
    return bar

def format_memory_size(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f}{unit}"
        size /= 1024
    return f"{size:.2f}PB"


def get_ram_usage():
    memory_status = MEMORYSTATUSEX()
    memory_status.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
    if GlobalMemoryStatusEx(ctypes.byref(memory_status)):
        ram_percent = memory_status.dwMemoryLoad
        ram_used = memory_status.ullTotalPhys - memory_status.ullAvailPhys
        ram_total = memory_status.ullTotalPhys
        return ram_percent, ram_used, ram_total
    else:
        raise Exception("couldn't get RAM status")


def get_cpu_usage():
    def filetime_to_large_integer(ft):
        return (ft.dwHighDateTime << 32) + ft.dwLowDateTime

    idle_time = FILETIME()
    kernel_time = FILETIME()
    user_time = FILETIME()

    if not GetSystemTimes(ctypes.byref(idle_time), ctypes.byref(kernel_time), ctypes.byref(user_time)):
        raise Exception("couldn't get system times")

    first_idle_time = filetime_to_large_integer(idle_time)
    first_total_time = filetime_to_large_integer(kernel_time) + filetime_to_large_integer(user_time)

    # creating a sample window to calculate cpu usage
    # so we need to wait a little
    # shorter time = less accurate :(
    time.sleep(0.75)

    # Get new system times
    idle_time_new = FILETIME()
    kernel_time_new = FILETIME()
    user_time_new = FILETIME()

    if not GetSystemTimes(ctypes.byref(idle_time_new), ctypes.byref(kernel_time_new), ctypes.byref(user_time_new)):
        raise Exception("couldn't get system times")

    second_idle_time = filetime_to_large_integer(idle_time_new)
    second_total_time = filetime_to_large_integer(kernel_time_new) + filetime_to_large_integer(user_time_new)

    idle_delta = second_idle_time - first_idle_time
    total_delta = second_total_time - first_total_time

    cpu_usage = (total_delta - idle_delta) / total_delta if total_delta > 0 else 0
    cpu_percent = max(0.0, cpu_usage * 100)
    return f"{cpu_percent:.2f}"

def print_stats():
    cpu_percent = get_cpu_usage()
    ram_percent, ram_used, ram_total = get_ram_usage()

    cpu_bar = get_colored_bar(float(cpu_percent))
    ram_bar = get_colored_bar(ram_percent)

    # only doing windows clear cause.. this is ctypes anyways lol
    os.system('cls')

    print(f"CPU Usage: [{cpu_bar}] {cpu_percent}%") 
    print(f"RAM Usage: [{ram_bar}] {ram_percent}% [{format_memory_size(ram_used)} / {format_memory_size(ram_total)}]")


try:
    while True:
        print_stats()
except KeyboardInterrupt:
    print("Exiting...")
