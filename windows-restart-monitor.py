#!/usr/bin/env python3
"""
Query and print the Windows Update scheduled restart time.

If run with "-warn N", and the restart is within N hours, then also pop
up a message box saying so.

Warning: The specific registry key holds the restart time on my Windows
10 system.  I have no idea how general it is.

NOTE: This only works with Windows Python, not cygwin Python.
"""

import ctypes     #      byref, c_ushort, windll
from   datetime   import datetime, timedelta, timezone
import os         #      environ
from   pathlib    import Path
import subprocess #      run, DEVNULL
import sys        #      argv
import tempfile   #      NamedTemporaryFile
from   typing     import Optional
import winreg     #      OpenKey, HKEY_LOCAL_MACHINE, etc.

import xml.etree.ElementTree as ET


DEBUG: bool = False


def dprint(msg: str) -> None:
  if DEBUG:
    print("%%% " + msg)


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

def get_local_system_time() -> datetime:
  """
  Get current date/time in local time zone using a direct Windows API
  call rather than relying on Python's confused library.

  Although, we *also* use the expedient of unsetting TZ, which might
  make this procedure unnecessary.
  """

  systime = SYSTEMTIME()
  ctypes.windll.kernel32.GetLocalTime(ctypes.byref(systime))
  return datetime(
    year=systime.wYear,
    month=systime.wMonth,
    day=systime.wDay,
    hour=systime.wHour,
    minute=systime.wMinute,
    second=systime.wSecond,
    microsecond=systime.wMilliseconds * 1000,
  ).astimezone()


def iso_8601_string(d: datetime) -> str:
  """Return `d` in the ISO 8601 format."""

  # Technically, ISO 8601 now requires the 'T' separator, but that looks
  # awful, and this is IMO close enough to keep using that label.
  return d.strftime("%Y-%m-%d %H:%M")


def filetime_to_datetime(filetime: int) -> datetime:
  """Convert a Windows FILETIME into a Python datetime."""

  # FILETIME is number of 100-nanosecond intervals since Jan 1, 1601
  #
  # Based on experimentation, this value is already in the local time
  # zone, not UTC (as a sane implementation would be).
  windows_epoch = datetime(1601, 1, 1)
  microseconds = filetime / 10
  return windows_epoch + timedelta(microseconds=microseconds)


def read_scheduled_reboot_time_from_registry() -> Optional[datetime]:
  """
  Read the registry value containing the currently scheduled Windows
  Update reboot time, as a datetime; or None if nothing is scheduled.

  This method only works on Windows 10.
  """

  key_path = r"SOFTWARE\Microsoft\WindowsUpdate\UX\StateVariables"
  value_name = "ScheduledRebootTime"

  try:
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ) as key:
      value, regtype = winreg.QueryValueEx(key, value_name)
      if regtype != winreg.REG_QWORD:
        raise ValueError(f"Unexpected registry value type: {regtype}")
      if not isinstance(value, int):
        raise ValueError(f"Value is not an integer: {value}.")
      if value == 0:
        print("Scheduled restart time is not set.")
        return None

      dt: datetime = filetime_to_datetime(value)
      return dt

  except FileNotFoundError:
    return None

  except PermissionError:
    raise ValueError("Access denied: please run this script with administrator privileges.")


def parse_datetime(value: str) -> datetime:
  """Parse an ISO 8601 date/time."""
  result = datetime.fromisoformat(value)

  if result.tzinfo is None:
    # Assume local time unless zone is specified.
    result = result.astimezone()

  return result


LOG_DIR = Path(
  "C:/ProgramData/USOShared/Logs/User"
)
EVENT_TASK = "MusUpdateRebootScheduledByUser"
EVENT_NS = "http://schemas.microsoft.com/win/2004/08/events/event"


# Tuple of (scheduled_time, reboot_time).
ScheduledAndRebootTime = tuple[datetime, datetime]


def get_events(
  etl_path: Path,
) -> list[ScheduledAndRebootTime]:
  """
  Return reboot-scheduled events from one ETL file.

  After conversion to XML, the events we are looking for look like this:

    <Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
      <System>
        <Provider Name="Microsoft.Windows.Update.Ux.MoUpdateSettings" Guid="{e9c21a1a-70d6-5ffa-4b58-ad7ae78bd3e7}" />
        <EventID>0</EventID>
        <Version>0</Version>
        <Level>5</Level>
        <Task>0</Task>
        <Opcode>0</Opcode>
        <Keywords>0x400000000000</Keywords>
        <TimeCreated SystemTime="2026-09-23T20:42:24.059248500-07:00" />
        <Correlation ActivityID="{00000000-0000-0000-0000-000000000000}" />
        <Execution ProcessID="20296" ThreadID="20712" ProcessorID="0" KernelTime="187727530167642" />
        <Channel />
        <Computer />
      </System>
      <EventData>
        <Data Name="ScheduledUtcTime">2026-09-30T13:30:00.000Z</Data>
        <Data Name="ScheduledLocalTime">2026-09-30T06:30:00.000Z</Data>
        <Data Name="SchedulePickerOption">       1</Data>
        <Data Name="UtcTime">2026-09-24T03:42:24.058Z</Data>
        <Data Name="DeviceLocalTime">2026-09-23T20:42:24.058Z</Data>
        <Data Name="__TlgCV__">c6P4n9P9oEa4IjEH.0</Data>
        <Data Name="PartA_PrivTags">33554432</Data>
      </EventData>
      <RenderingInfo Culture="en-US">
        <Task>MusUpdateRebootScheduledByUser</Task>
      </RenderingInfo>
    </Event>

  We identify them by RenderingInfo.Task ==
  "MusUpdateRebootScheduledByUser" and return their System.TimeCreated
  and EventData.ScheduledLocalTime.

  This format is "documented" (loosely speaking) at:

    https://learn.microsoft.com/en-us/windows/privacy/basic-level-windows-diagnostic-events-and-fields-1809
  """

  xml_path: Path
  with tempfile.NamedTemporaryFile(
    mode="w",
    suffix=".xml",
    delete=False,
  ) as temp:
    xml_path = Path(temp.name)

  dprint(f"xml_path={xml_path}")

  try:
    subprocess.run(
      [
        # MS-provided program (should be in Windows/system32, and
        # assumed to be on the PATH) that can read ETL and write XML.
        #
        # https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/tracerpt
        "tracerpt",

        # Input file.
        str(etl_path),

        # Output file.
        "-o", str(xml_path),

        # Output format.
        "-of", "XML",

        # "Specifies to be less restrictive."  ChatGPT thought this
        # would be a good idea.
        "-lr",

        # We create the XML file above, and that causes tracerpt to ask
        # whether to overwrite it.  Say yes.
        "-y",
      ],
      check=True,
      stdin=subprocess.DEVNULL,
      stdout=subprocess.DEVNULL,
    )

    root = ET.parse(xml_path).getroot()
    events: list[ScheduledAndRebootTime] = []

    for event in root.iter(f"{{{EVENT_NS}}}Event"):
      rendering_info = event.find(
        f"{{{EVENT_NS}}}RenderingInfo"
      )
      if rendering_info is None:
        continue

      task = rendering_info.find(
        f"{{{EVENT_NS}}}Task"
      )
      if task is None or task.text != EVENT_TASK:
        continue

      system = event.find(f"{{{EVENT_NS}}}System")
      if system is None:
        continue

      time_created = system.find(
        f"{{{EVENT_NS}}}TimeCreated"
      )
      if time_created is None:
        continue

      time_text = time_created.get("SystemTime")
      if time_text is None:
        continue

      event_data = event.find(
        f"{{{EVENT_NS}}}EventData"
      )
      if event_data is None:
        continue

      reboot_time: Optional[datetime] = None

      for data in event_data.findall(
        f"{{{EVENT_NS}}}Data"
      ):
        if (data.get("Name") == "ScheduledLocalTime" and
            data.text is not None):

          # For some reason, the "local time" string has a "Z" at the
          # end that is incorrect.  Strip it.
          local_time_str: str = data.text.removesuffix("Z")
          reboot_time = parse_datetime(local_time_str)

          break

      if reboot_time is None:
        continue

      events.append((
        parse_datetime(time_text),
        reboot_time,
      ))

    return events

  finally:
    xml_path.unlink(missing_ok=True)


def read_scheduled_reboot_time_from_logs(
  since: datetime,
) -> Optional[datetime]:
  """
  Find the most recent reboot-scheduled event after `since`.

  We have to resort to the bizarre method of crawling the logs to find
  out when the reboot is scheduled for because Microsoft doesn't provide
  any query API, and they removed the registry key in Windows 11.
  """

  latest: Optional[ScheduledAndRebootTime] = None

  dprint(f"since: {since}")

  etl_path: Path
  for etl_path in LOG_DIR.glob("UpdateUx.*.etl"):
    dprint(f"etl_path={etl_path}")

    # If the file hasn't been modified since `since`, then none of the
    # events inside of it can (should) satisfy the time condition.
    mtime: datetime = datetime.fromtimestamp(
      etl_path.stat().st_mtime).astimezone()
    dprint(f"mtime: {mtime}")
    if mtime <= since:
      continue

    for event_time, scheduled_time in get_events(etl_path):
      if event_time <= since:
        continue

      if latest is None or event_time > latest[0]:
        latest = (event_time, scheduled_time)

  return latest[1] if latest is not None else None


def get_default_since() -> datetime:
  return datetime.now(timezone.utc) - timedelta(days=10)


def read_scheduled_reboot_time() -> Optional[datetime]:
  ret: Optional[datetime] = read_scheduled_reboot_time_from_registry()
  if ret is not None:
    return ret

  # TODO: Add a command line option to allow the user to specify this.
  since: datetime = get_default_since()

  # If the registry method does not find it, look in the logs.

  return read_scheduled_reboot_time_from_logs(since)


def show_warning_dialog(message: str) -> None:
  """Pop up a warning dialog box with `message`."""

  MB_OK = 0x0
  MB_ICONWARNING = 0x30
  ctypes.windll.user32.MessageBoxW(0, message, "Scheduled Restart Warning", MB_OK | MB_ICONWARNING)


def main() -> None:
  # Unsetting TZ is the key to allowing Windows Python to get the
  # right time zone.
  os.environ.pop("TZ", None)

  warn_hours: Optional[int] = None
  args = sys.argv[1:]
  if len(args) == 2 and args[0] == "-warn":
    try:
      warn_hours = int(args[1])
    except ValueError:
      print("Invalid value for -warn argument. Must be an integer.")
      return

  now: datetime = get_local_system_time()
  print(f"Current time: {iso_8601_string(now)}")

  reboot_time: Optional[datetime] = read_scheduled_reboot_time()
  if reboot_time is None:
    print("No scheduled restart time.")

  else:
    reboot_time_str = iso_8601_string(reboot_time)
    delta = reboot_time - now
    hours_until_restart = delta.total_seconds() / 3600

    print(f"Restart time: {reboot_time_str} " +
          f"(about {hours_until_restart:.1f} hours from now)")

    if warn_hours is not None:
      if hours_until_restart < warn_hours:
        msg = (
          f"A system restart is scheduled for {reboot_time_str}.\n" +
          f"This is in approximately {hours_until_restart:.1f} hours.")
        show_warning_dialog(msg)


if __name__ == "__main__":
  main()


# EOF
