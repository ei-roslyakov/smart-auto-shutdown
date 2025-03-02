import os
import sys
import time
import shutil

import psutil
from loguru import logger


CPU_THRESHOLD = float(os.getenv("CPU_THRESHOLD", 10))
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 30))
TIME_PERIOD = int(os.getenv("TIME_PERIOD", 180))
NOTIFY_PERIOD = int(os.getenv("NOTIFY_PERIOD", 60))
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

logger.info("🚀 CPU Monitor Script Starting")


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
            f'echo "🛑 Shutdown canceled! System will remain running." | wall'
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


def main():
    """Monitors CPU and shuts down if below threshold for TIME_PERIOD, unless postponed."""
    logger.info("🚀 CPU Monitor Script Started")

    below_threshold_count = 0
    required_count = TIME_PERIOD // CHECK_INTERVAL

    while True:
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
            with open(POSTPONE_FILE, "r") as f:
                postpone_until = float(f.read().strip())

            current_time = time.time()
            remaining_time = int(postpone_until - current_time)

            if remaining_time > 0:
                logger.info(
                    f"🛑 Shutdown postponed! Skipping shutdown sequence. Remaining: {remaining_time // 60} minutes."
                )
                time.sleep(CHECK_INTERVAL)
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
