"""
tools/time_tool.py - Current date and time of the system

Light tool that reads the datetime with the local timezone.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from langchain_core.tools import tool

@tool
def get_current_time(timezone: str = "Europe/Rome") -> str:
    """
    Returns the current date and time in the specified time zone
    Use this tool everytime the user asks the date & time,
    Which day it its, the current day or every other time related info.

    Args:
        timezone: timezone IANA (default: Europe/Rome).
            Example: 'UTC', 'America/New_York', 'Asia/Tokyo'
    """
    try:
        tz = ZoneInfo(timezone)
        now = datetime.now(tz)
        return (
            f"Data e ora corrente ({timezone}):\n"
            f"  Data:    {now.strftime('%d/%m/%Y')}\n"
            f"  Ora:     {now.strftime('%H:%M:%S')}\n"
            f"  Giorno:  {now.strftime('%A')}\n"
            f"  UTC offset: {now.strftime('%z')}"
        )
    except Exception as e:
        return f"Error occured when retrieving the time from the timezone '{timezon}': {e}"
    # #endtry
# #enddef get_current_time
