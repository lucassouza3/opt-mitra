from queue import Queue
from threading import Thread, Lock
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path
from nist_manager import add_nist
from config_app import *

class MyHandler(FileSystemEventHandler):
    """
    Custom file system event handler that puts file creation events onto a queue.
    """
    def __init__(self, event_queue):
        """
        Initialize the handler with an event queue.
        
        :param event_queue: Queue object where events will be put.
        """
        super().__init__()
        self.event_queue = event_queue

    def on_created(self, event):
        """
        Action to perform when a file is created. Puts the event onto the queue if it's not a directory.
        
        :param event: Event object representing the file creation event.
        """
        if not event.is_directory:
            self.event_queue.put(event)

def event_processor(event_queue, file_lock):
    """
    Processes events from the event queue, uploading files with a '.nst' extension.
    
    :param event_queue: Queue from which to process events.
    :param file_lock: Threading lock to ensure thread-safe operations.
    """
    while True:
        event = event_queue.get()
        if event is None:  # Check for sentinel value to break the loop
            break
        with file_lock:
            arquivo_capturado = Path(event.src_path)
            print(f'[watchdog] Capturou o arquivo {str(arquivo_capturado)}')
            if arquivo_capturado.suffix == '.nst':
                add_nist(str(arquivo_capturado))

def monitor_directory(path, event_queue):
    """
    Sets up a watchdog observer to monitor a directory for changes.
    
    :param path: The path to the directory to monitor.
    :param event_queue: The event queue to which the observer will put events.
    :return: The observer object.
    """
    observer = Observer()
    handler = MyHandler(event_queue)
    observer.schedule(handler, path=str(path), recursive=True)
    observer.start()
    return observer

def setup_directory_monitors(base_path, event_queue):
    """
    Sets up monitors for a directory and its subdirectories, including resolving and monitoring symbolic links.
    
    :param base_path: The base directory path to monitor.
    :param event_queue: The event queue for the observers to use.
    :return: A list of observer objects.
    """
    observers = []
    for item in base_path.iterdir():
        if item.is_dir():
            observers.append(monitor_directory(item, event_queue))
            if item.is_symlink():
                resolved_path = item.resolve()
                if resolved_path.is_dir():
                    observers.append(monitor_directory(resolved_path, event_queue))
    return observers


if __name__ == '__main__':
    # root_dir = Path('./nists').resolve()

    NIST_DIR = Path(NIST_DIR).resolve()

    event_queue = Queue()
    file_lock = Lock()

    # Initialize monitoring on the specified directory and its subdirectories, including symbolic links
    observers = setup_directory_monitors(NIST_DIR, event_queue)

    print('[watchdog] Aguardando novos arquivos...')

    processor_thread = Thread(target=event_processor, args=(event_queue, file_lock))
    processor_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print('[watchdog] Shutting down...')
        for observer in observers:
            observer.stop()
            observer.join()

        event_queue.put(None)  # Signal the processor thread to stop
        processor_thread.join()
        print('[watchdog] Finished.')
