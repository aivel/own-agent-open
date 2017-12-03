import threading

import logging
import traceback

import agent_impl.websocks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


if __name__ == '__main__':
    ws_thread = None

    while True:
        if ws_thread is None or not ws_thread.is_alive():
            try:
                ws_thread = threading.Thread(target=agent_impl.websocks.run)
                ws_thread.start()
            except:
                traceback.print_exc()
