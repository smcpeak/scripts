import winreg
import struct
import datetime

def filetime_to_datetime(filetime):
  # FILETIME is number of 100-nanosecond intervals since Jan 1, 1601
  windows_epoch = datetime.datetime(1601, 1, 1)
  microseconds = filetime / 10
  return windows_epoch + datetime.timedelta(microseconds=microseconds)

def main():
  key_path = r"SOFTWARE\Microsoft\WindowsUpdate\UX\StateVariables"
  value_name = "ScheduledRebootTime"

  try:
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ) as key:
      value, regtype = winreg.QueryValueEx(key, value_name)
      if regtype != winreg.REG_QWORD:
        print("Unexpected registry value type.")
        return
      if value == 0:
        print("Scheduled restart time is not set.")
        return
  except FileNotFoundError:
    print("No scheduled restart time.")
    return
  except PermissionError:
    print("Access denied: please run this script with administrator privileges.")
    return

  dt = filetime_to_datetime(value)
  # Do not convert from UTC — value is already local time
  print("Scheduled restart time:", dt.strftime("%Y-%m-%d %H:%M"))

if __name__ == "__main__":
  main()
