from typing import Any, Callable

class EventIt:
    def __init__(self):
        self.events = {}
    
    def call_event(self, name: str, *args, **kwargs):
        for func in self.events[name]:
            func(*args, **kwargs)

    def register_event(self, name: str):
        print("Registered event: {}".format(name))
        self.events[name] = []

    def on_event(self, func: Callable[[], Any]):
        self.events[func.__name__].append(func)
        print("Registered event listener for: {}".format(func.__name__))

        # def wrapper_func():
        #     # print("Do something before the function.")
        #     func()
        return func
