from dataclasses import dataclass
from threading import Thread, Event
from time import sleep

from jsons import load as jload, dump as jdump, KEY_TRANSFORMER_SNAKECASE, KEY_TRANSFORMER_PASCALCASE
from yaml import load, dump, CDumper, CSafeLoader


@dataclass
class Settings:
    theme: str = "dark"
    invert_value: int = 85


class SavingThread(Thread):
    def __init__(self):
        super().__init__()
        self.name = "SavingThread"
        self.daemon = True
        self._skip = Event()
        self._waiting = Event()
        self._terminate = False

    def run(self):
        while True:
            self._skip.wait()
            if self._terminate:
                break
            force_stop = self._waiting.wait(0.7)
            if force_stop:
                self._waiting.clear()
                continue
            _save_to_yaml()
            self._skip.clear()

    def call(self):
        if not self._skip.is_set():
            self._skip.set()
        else:
            self._waiting.set()

    def join(self, timeout=0.5):
        self._terminate = True
        self.call()
        sleep(max(timeout, 0.5))


class Config:
    title = "Image Inverter"
    icon_file = "icon.ico"
    config_name = "_image_inversion_config.yml"
    config: Settings = Settings()
    config_saving_thread: SavingThread = SavingThread()


def save_to_yaml(instant_save=False):
    if instant_save:
        _save_to_yaml()
    else:
        Config.config_saving_thread.call()


def _save_to_yaml():
    with open(Config.config_name, "w", encoding="utf8") as f:
        dump(jdump(Config.config, key_transformer=KEY_TRANSFORMER_PASCALCASE), f, Dumper=CDumper)


def read_from_yaml():
    with open(Config.config_name, "r", encoding="utf8") as f:
        Config.config = jload(load(f, Loader=CSafeLoader), Settings, key_transformer=KEY_TRANSFORMER_SNAKECASE)


"""
class Error_file_handler:
    def __init__(self):
        self.stderr = sys.stderr
        sys.stderr = self

    def __del__(self):
        sys.stderr = self.stderr

    def write(self, data, **kwargs):
        print_console(data)
        if kwargs.pop('flush', False):
            self.stderr.flush()

    def flush(self):
        self.stderr.flush()


def print_console(message):
    # TODO: Throw error window!
    Config.scrollbar_dict["console"].configure(state='normal')  # enable insert
    Config.scrollbar_dict["console"].insert(END, message)
    # Config.console.insert(END, "-------\n")
    Config.scrollbar_dict["console"].yview(END)  # autoscroll
    Config.scrollbar_dict["console"].configure(state='disabled')  # disable editing
"""
