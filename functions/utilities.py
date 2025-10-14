from datetime import datetime

def parse_datetime(dt_str):
    # try full format first
    try:
        return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        # Fallback to no-seconds format
        return datetime.strptime(dt_str, "%Y-%m-%d %H:%M")