#!/usr/bin/env python3
"""
Query and print the Windows Update scheduled restart time.

If run with "-warn N", and the restart is within N hours, then also pop
up a message box saying so.

Warning: The specific registry key holds the restart time on my Windows
10 system.  I have no idea how general it is.

NOTE: This only works with Windows Python, not cygwin Python.
"""

import winreg
import struct
import datetime
import sys
import ctypes
from typing import Optional


# For `get_local_system_time`.
class SYSTEMTIME(ctypes.Structure):
  _fields_ = [
    ("wYear", ctypes.c_ushort),
    ("wMonth", ctypes.c_ushort),
    ("wDayOfWeek", ctypes.c_ushort),
    ("wDay", ctypes.c_ushort),
    ("wHour", ctypes.c_ushort),
    ("wMinute", ctypes.c_ushort),
    ("wSecond", ctypes.c_ushort),
    ("wMilliseconds", ctypes.c_ushort),
  ]

def get_local_system_time() -> datetime.datetime:
  """Get current date/time in local time zone using a direct Windows API
  call rather than relying on Python's confused library."""

  systime = SYSTEMTIME()
  ctypes.windll.kernel32.GetLocalTime(ctypes.byref(systime))
  return datetime.datetime(
    year=systime.wYear,
    month=systime.wMonth,
    day=systime.wDay,
    hour=systime.wHour,
    minute=systime.wMinute,
    second=systime.wSecond,
    microsecond=systime.wMilliseconds * 1000,
  )


def iso_8601_string(d: datetime.datetime) -> str:
  """Return `d` in the ISO 8601 format."""

  # Technically, ISO 8601 now requires the 'T' separator, but that looks
  # awful, and this is IMO close enough to keep using that label.
  return d.strftime("%Y-%m-%d %H:%M")


def filetime_to_datetime(filetime: int) -> datetime.datetime:
  """Convert a Windows FILETIME into a Python datetime."""

  # FILETIME is number of 100-nanosecond intervals since Jan 1, 1601
  windows_epoch = datetime.datetime(1601, 1, 1)
  microseconds = filetime / 10
  return windows_epoch + datetime.timedelta(microseconds=microseconds)


def read_scheduled_reboot_time() -> Optional[int]:
  """
  Read the registry value containing the currently scheduled Windows
  Update reboot time, as a FILETIME; or None if nothing is scheduled.

  Based on experimentation, this value is already in the local time
  zone, not UTC (as a sane implementation would be).
  """

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
  """Pop up a warning dialog box with `message`."""

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

  now: datetime.datetime = get_local_system_time()
  print(f"Current time: {iso_8601_string(now)}")

  filetime: Optional[int] = read_scheduled_reboot_time()
  if filetime is None:
    print("No scheduled restart time.")

  else:
    dt: datetime.datetime = filetime_to_datetime(filetime)

    delta = dt - now
    hours_until_restart = delta.total_seconds() / 3600

    print(f"Restart time: {iso_8601_string(dt)} " +
          f"(about {hours_until_restart:.1f} hours from now)")

    if warn_hours is not None:
      if hours_until_restart < warn_hours:
        msg = (
          f"A system restart is scheduled for {iso_8601_string(dt)}.\n" +
          f"This is in approximately {hours_until_restart:.1f} hours.")
        show_warning_dialog(msg)


if __name__ == "__main__":
  main()


# EOF
