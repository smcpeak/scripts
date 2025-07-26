import winreg
import struct
import datetime
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

def main() -> None:
  filetime: Optional[int] = read_scheduled_reboot_time()
  if filetime is not None:
    dt: datetime.datetime = filetime_to_datetime(filetime)
    # Value is already in local time
    print("Scheduled restart time:", dt.strftime("%Y-%m-%d %H:%M"))

if __name__ == "__main__":
  main()
