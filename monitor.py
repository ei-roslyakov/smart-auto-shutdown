from datetime import datetime, time as dt_time, timedelta
import os
import sys
import time
import shutil
import subprocess
import psutil
from loguru import logger


POSTPONE_FILE = "/tmp/cpu_monitor_postpone_until"
LOG_SYSTEM_FILE = "/var/log/cpu_monitor.log"

logger.remove()
logger.add(
    LOG_SYSTEM_FILE,
    rotation="10 MB",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
)
logger.add(
    sys.stdout, level="INFO", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
)


def str_to_bool(value):
    """
    Converts environment variable strings to boolean correctly.
    """
    return str(value).strip().lower() in ["true", "1", "yes"]


def load_config():
    """
    Loads environment variables, sets them globally, and logs the values.
    """
    global CPU_THRESHOLD, CHECK_INTERVAL, TIME_PERIOD, NOTIFY_PERIOD
    global ALLOWED_START_HOUR, ALLOWED_END_HOUR, ALLOWED_START, ALLOWED_END
    global RESTRICTED_HOURS, DENY_TURN_OFF_WHEN_ACTIVE_SSH

    CPU_THRESHOLD = float(os.getenv("CPU_THRESHOLD", 10))
    CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 60))
    TIME_PERIOD = int(os.getenv("TIME_PERIOD", 3600))
    NOTIFY_PERIOD = int(os.getenv("NOTIFY_PERIOD", 300))

    ALLOWED_START_HOUR = int(os.getenv("ALLOWED_START_HOUR", 19))
    ALLOWED_END_HOUR = int(os.getenv("ALLOWED_END_HOUR", 8))
    ALLOWED_START = dt_time(ALLOWED_START_HOUR, 0)
    ALLOWED_END = dt_time(ALLOWED_END_HOUR, 0)
    RESTRICTED_HOURS = str_to_bool(os.getenv("RESTRICTED_HOURS", "true"))
    DENY_TURN_OFF_WHEN_ACTIVE_SSH = str_to_bool(
        os.getenv("DENY_TURN_OFF_WHEN_ACTIVE_SSH", "true")
    )

    # Log the configuration values
    logger.info("🚀 Loaded Configuration:")
    logger.info(f"  - CPU_THRESHOLD: {CPU_THRESHOLD}%")
    logger.info(f"  - CHECK_INTERVAL: {CHECK_INTERVAL} seconds")
    logger.info(f"  - TIME_PERIOD: {TIME_PERIOD} seconds")
    logger.info(f"  - NOTIFY_PERIOD: {NOTIFY_PERIOD} seconds")
    logger.info(f"  - ALLOWED_START_HOUR: {ALLOWED_START_HOUR} ({ALLOWED_START} UTC)")
    logger.info(f"  - ALLOWED_END_HOUR: {ALLOWED_END_HOUR} ({ALLOWED_END} UTC)")
    logger.info(f"  - RESTRICTED_HOURS: {RESTRICTED_HOURS}")
    logger.info(f"  - DENY_TURN_OFF_WHEN_ACTIVE_SSH: {DENY_TURN_OFF_WHEN_ACTIVE_SSH}")


load_config()


def get_cpu_usage():
    """Returns the current CPU utilization as a percentage."""
    return psutil.cpu_percent(interval=CHECK_INTERVAL)


def send_shutdown_notification():
    """Sends a warning message before shutdown, allowing user input to cancel shutdown."""
    if os.path.exists(POSTPONE_FILE):
        with open(POSTPONE_FILE, "r") as f:
            postpone_until = float(f.read().strip())

        current_time = time.time()
        remaining_time = int(postpone_until - current_time)

        if remaining_time > 0:
            logger.info(
                f"🛑 Shutdown postponed! Skipping warning. Remaining: {remaining_time // 60} minutes."
            )
            return

    message = f"⚠️ WARNING: System will shut down in {NOTIFY_PERIOD} seconds due to low CPU utilization!\n"
    message += "🚀 Press any key to cancel shutdown or run 'postpone_shutdown <duration>' to delay shutdown."

    logger.warning(message)
    shutil.which("wall") and os.system(f'echo "{message}" | wall')

    logger.info(
        "⌨️ Waiting for user input... Press any key within 60 seconds to cancel shutdown."
    )
    result = os.system(
        f"read -t {NOTIFY_PERIOD} -n 1 -p 'Press any key to cancel shutdown...' && echo 'CANCEL'"
    )

    if result == 0:
        postpone_until = time.time() + (10 * 60)
        with open(POSTPONE_FILE, "w") as f:
            f.write(str(postpone_until))

        logger.info("🛑 Shutdown canceled by user input. Postponed for 10 minutes.")
        shutil.which("wall") and os.system(
            'echo "🛑 Shutdown canceled! System will remain running." | wall'
        )
        return

    logger.warning("🚨 No input received. Proceeding with shutdown.")


def get_system_uptime():
    """Returns system uptime in seconds."""
    with open("/proc/uptime", "r") as f:
        return float(f.readline().split()[0])


def shutdown_system():
    """Ensures shutdown is postponed if requested, otherwise proceeds with shutdown."""
    logger.info("🔍 Checking if shutdown should be postponed...")

    if os.path.exists(POSTPONE_FILE):
        logger.info(f"📄 Found postpone file: {POSTPONE_FILE}")

        try:
            with open(POSTPONE_FILE, "r") as f:
                lines = f.readlines()
                postpone_until = float(lines[0].strip())
                saved_uptime = float(lines[1].strip())
        except (ValueError, IndexError):
            logger.error("⚠️ Invalid postpone file format, removing it.")
            os.remove(POSTPONE_FILE)
            return

        current_time = time.time()
        system_uptime = get_system_uptime()
        remaining_time = int(postpone_until - current_time)

        if system_uptime < saved_uptime:
            logger.warning("🔄 VM reboot detected. Clearing postponed shutdown.")
            os.remove(POSTPONE_FILE)
        elif remaining_time > 0:
            logger.info(
                f"🛑 Shutdown postponed! Remaining: {remaining_time // 60} minutes."
            )
            return

    logger.critical("🚨 No active postpone request. System shutting down now!")
    os.system("sudo shutdown -h now")


def is_within_allowed_time(start, end):
    """Check if the current time is within the allowed monitoring window."""
    now = datetime.now().time()

    if ALLOWED_START <= now or now < ALLOWED_END:
        return True
    return False


def is_ssh_active():
    """Checks if there are active SSH sessions."""
    try:
        result = subprocess.run(["who"], capture_output=True, text=True)
        users = result.stdout.splitlines()
        ssh_sessions = [user for user in users if "pts/" in user]

        if ssh_sessions:
            logger.info(f"🛑 Active SSH session detected:\n{ssh_sessions}")
            return True
    except Exception as e:
        logger.error(f"⚠️ Error checking SSH sessions: {e}")

    return False


def main():
    """Monitors CPU and shuts down if below threshold for TIME_PERIOD, unless postponed."""
    logger.info("----------------------------------------")
    logger.info("🚀 CPU Monitor Script Started")

    if RESTRICTED_HOURS:
        logger.info("⏳ Monitoring is restricted to allowed hours.")

    below_threshold_count = 0
    required_count = TIME_PERIOD // CHECK_INTERVAL

    while True:
        if RESTRICTED_HOURS and not is_within_allowed_time(ALLOWED_START, ALLOWED_END):
            next_start = datetime.combine(datetime.today(), ALLOWED_START)
            if datetime.now().time() >= ALLOWED_START:
                next_start += timedelta(days=1)

            sleep_time = (next_start - datetime.now()).total_seconds()
            logger.info(
                f"⏸️ Monitoring paused until {ALLOWED_START_HOUR}:00. Sleeping for {sleep_time / 3600:.2f} hours..."
            )
            time.sleep(sleep_time)
            continue

        if DENY_TURN_OFF_WHEN_ACTIVE_SSH and is_ssh_active():
            logger.info(
                "🛑 Active SSH session detected. Resetting below_threshold_count and skipping shutdown sequence."
            )
            below_threshold_count = 0
            time.sleep(CHECK_INTERVAL)
            continue

        cpu_usage = get_cpu_usage()
        logger.info(f"📊 CPU Usage: {cpu_usage:.2f}% (Threshold: {CPU_THRESHOLD}%)")

        if cpu_usage < CPU_THRESHOLD:
            below_threshold_count += 1
        else:
            below_threshold_count = 0

        logger.info(
            f"✅ {below_threshold_count}/{required_count} readings below threshold."
        )

        if os.path.exists(POSTPONE_FILE):
            logger.info(f"📄 Found postpone file: {POSTPONE_FILE}")

            try:
                with open(POSTPONE_FILE, "r") as f:
                    lines = [line.strip() for line in f.readlines() if line.strip()]

                if not lines:
                    raise ValueError("Empty postpone file")

                postpone_until = float(lines[-1])

            except (ValueError, IndexError) as e:
                logger.error(f"⚠️ Invalid postpone file format ({e}). Removing file.")
                os.remove(POSTPONE_FILE)
                continue

            current_time = time.time()
            remaining_time = int(postpone_until - current_time)

            if remaining_time > 0:
                logger.info(
                    f"🛑 Shutdown postponed! Remaining: {remaining_time // 60} minutes."
                )
                continue

        if below_threshold_count >= required_count:
            send_shutdown_notification()
            logger.info(f"🕒 Waiting {NOTIFY_PERIOD} seconds before final shutdown...")
            time.sleep(NOTIFY_PERIOD)
            shutdown_system()

        logger.info(f"⏳ Sleeping for {CHECK_INTERVAL} seconds before next check...")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
