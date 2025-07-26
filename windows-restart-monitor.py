import winreg
import struct
import datetime
import sys
import ctypes
from typing import Optional

def filetime_to_datetime(filetime: int) -> datetime.datetime:
  # FILETIME is number of 100-nanosecond intervals since Jan 1, 1601
  windows_epoch = datetime.datetime(1601, 1, 1)
  microseconds = filetime / 10
  return windows_epoch + datetime.timedelta(microseconds=microseconds)

def read_scheduled_reboot_time() -> Optional[int]:
  key_path = r"SOFTWARE\Microsoft\WindowsUpdate\UX\StateVariables"
  value_name = "ScheduledRebootTime"

  try:
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ) as key:
      value, regtype = winreg.QueryValueEx(key, value_name)
      if regtype != winreg.REG_QWORD:
        print("Unexpected registry value type.")
        return None
      if not isinstance(value, int):
        print(f"Value is not an integer: {value}.")
        return None
      if value == 0:
        print("Scheduled restart time is not set.")
        return None
      return value
  except FileNotFoundError:
    print("No scheduled restart time.")
    return None
  except PermissionError:
    print("Access denied: please run this script with administrator privileges.")
    return None

def show_warning_dialog(message: str) -> None:
  MB_OK = 0x0
  MB_ICONWARNING = 0x30
  ctypes.windll.user32.MessageBoxW(0, message, "Scheduled Restart Warning", MB_OK | MB_ICONWARNING)

def main() -> None:
  warn_hours: Optional[int] = None
  args = sys.argv[1:]
  if len(args) == 2 and args[0] == "-warn":
    try:
      warn_hours = int(args[1])
    except ValueError:
      print("Invalid value for -warn argument. Must be an integer.")
      return

  filetime: Optional[int] = read_scheduled_reboot_time()
  if filetime is None:
    print("No scheduled restart time.")
  else:
    dt: datetime.datetime = filetime_to_datetime(filetime)
    # Value is already in local time
    print("Scheduled restart time:", dt.strftime("%Y-%m-%d %H:%M"))

    if warn_hours is not None:
      now = datetime.datetime.now()
      delta = dt - now
      hours_until_restart = delta.total_seconds() / 3600
      if hours_until_restart < warn_hours:
        msg = f"A system restart is scheduled for {dt.strftime('%Y-%m-%d %H:%M')}\n"
        msg += f"This is in approximately {hours_until_restart:.1f} hours."
        show_warning_dialog(msg)

if __name__ == "__main__":
  main()
