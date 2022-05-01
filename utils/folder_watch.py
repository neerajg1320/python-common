from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from utils.file_utils import get_extn
import os


class FolderWatch:
    def __init__(self, folder, file_event_handler, extensions=None, filename=None):
        self.observer = Observer()
        self.folder = folder
        self.file_event_handler = file_event_handler
        self.extensions = extensions
        self.filename = filename

    def run(self):
        event_handler = Handler(self.file_event_handler,
                                extensions=self.extensions,
                                filename=self.filename)
        self.observer.schedule(event_handler, self.folder, recursive = True)
        try:
            self.observer.start()
        except FileNotFoundError as e:
            print("Folder {} not found".format(self.folder))
            return

        # The following was not being executed when we had queue receive message used
        self.observer.join()


class Handler(FileSystemEventHandler):
    def __init__(self, file_event_handler, extensions=None, filename=None):
        super().__init__()
        self.file_event_handler = file_event_handler
        self.extensions = extensions
        self.filename = filename

    def on_any_event(self, event):
        # print("%s: Watchdog directory event - % s." % (event.event_type, event.src_path))

        if event.is_directory:
            return

        if self.filename is not None:
            filename = os.path.basename(event.src_path)
            if filename != self.filename:
                return

        if self.extensions is not None:
            extn = get_extn(event.src_path)
            if not extn in self.extensions:
                return

        if event.event_type == 'created':
            pass
        elif event.event_type == 'closed':
            self.file_event_handler(event.src_path)
        elif event.event_type == 'modified':
            pass
        elif event.event_type == 'deleted':
            pass
        elif event.event_type == 'moved':
            pass
        else:
            print("Watchdog received event not handled - % s." % event.event_type, ", ", event.src_path)
