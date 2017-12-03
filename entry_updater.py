import threading

import logging
import traceback

import agent_impl.updater

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


if __name__ == '__main__':
    updater_thread = None

    while True:
        if updater_thread is None or not updater_thread.is_alive():
            try:
                updater_thread = threading.Thread(target=agent_impl.updater.run)
                updater_thread.start()
            except:
                traceback.print_exc()
