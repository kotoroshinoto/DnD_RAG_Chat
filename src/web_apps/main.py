import atexit
import multiprocessing
import os
from pathlib import Path
import signal
import subprocess
import time
from typing import List

import click

# from web_apps.backend.flask_backend_app import FlaskBackEndApp
# from web_apps.frontend.flask_frontend_app import FlaskFrontEndApp
# from web_apps.backend.main import main_cli as backend_main_cli
# from web_apps.frontend.main import main_cli as frontend_main_cli
from log.logger import logger

def start_subprocess(command: List[str], cwd: Path):
    """Start a subprocess."""
    return subprocess.Popen(command, cwd=str(cwd.resolve()))

def monitor_subprocess(subp_command: List[str], subp_cwd: Path, subp_name: str, stop_event: multiprocessing.Event, polling_interval=1):
    """Monitor the frontend process and restart if it stops."""
    while not stop_event.is_set():
        try:
            logger.info(f"Starting {subp_name}...")
            process = start_subprocess(subp_command, subp_cwd)
            while process.poll() is None:  # If frontend process has stopped
                if stop_event.is_set():
                    process.terminate()
                    logger.info(f"{subp_name} terminated due to stop_event.")
                    return
                time.sleep(polling_interval)  # Check every second
        except Exception as e:
            logger.error(f"Exception detected in {subp_name}: {e}. Restarting..")
        logger.warning(f"{subp_name} exited. Restarting...")


def cleanup(monitors, stop_event):
    logger.info("Cleanup: stop_event set for subprocess monitors...")
    stop_event.set()
    for monitor in monitors:
        if monitor.is_alive():
            monitor.terminate()
            logger.info(f"Terminated monitor process {monitor.name}")


def create_signal_handler(stop_event, monitors):
    """Create a signal handler with access to the stop_event and monitors."""
    def signal_handler(signum, frame):
        logger.info(f"Signal {signum} received. Stopping subprocess monitors...")
        stop_event.set()
        for monitor in monitors:
            if monitor.is_alive():
                monitor.terminate()
                logger.info(f"Terminated monitor process {monitor.name}")
    return signal_handler


@click.command()
@click.option('--llm_host', default='localhost', help='LLM endpoint host')
@click.option('--llm_port', default=1234, help='LLM endpoint port')
@click.option('--llm_version_str', default='v1', help='LLM endpoint version str')
@click.option('--frontend_host', default='0.0.0.0', help='webapp hostname or ip to listen on')
@click.option('--frontend_port', default=3456, help='Port for webapp to listen on')
@click.option('--backend_host', default='0.0.0.0', help='webapp hostname or ip to listen on')
@click.option('--backend_port', default=5000, help='Port for webapp to listen on')
@click.option('--polling_interval', default=1, type=click.IntRange(min=1), help='polling interval in seconds')
def main_cli(llm_host, llm_port, llm_version_str, frontend_host, frontend_port, backend_host, backend_port, polling_interval):
    # Define the commands and working directories for each subprocess
    frontend_command = [
        'python', '-m', 'web_apps.frontend.main',
        '--host', frontend_host, '--port', frontend_port
    ]
    backend_command = [
        'python', '-m', 'web_apps.backend.main',
        '--host', backend_host, '--port', backend_port,
        '--llm_host', llm_host, '--llm_port', llm_port, '--llm_version_str', llm_version_str
    ]
    cwd = os.getcwd()
    
    stop_event = multiprocessing.Event()
    
    # Create separate monitor processes for frontend and backend using the generic monitor function
    frontend_monitor = multiprocessing.Process(target=monitor_subprocess, args=(frontend_command, cwd, "Frontend", stop_event, polling_interval), daemon=False)
    backend_monitor = multiprocessing.Process(target=monitor_subprocess, args=(backend_command, cwd, "Backend", stop_event, polling_interval), daemon=False)
    
    monitors = [frontend_monitor, backend_monitor]
    signal_handler = create_signal_handler(stop_event, monitors)
    
    atexit.register(cleanup, monitors, stop_event)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Start monitors
    for monitor in monitors:
        monitor.start()
    # Wait for monitors to finish
    for monitor in monitors:
        monitor.join()


if __name__ == "__main__":
    main_cli()
