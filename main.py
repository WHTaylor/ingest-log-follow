#!/usr/bin/env python
import re
from datetime import datetime as dt

from rich.syntax import Syntax
from rich.table import Table

from textual import events
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import RichLog, Footer, Static


date_patt = r"(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})"
time_patt = r"(?P<time>\d{2}:\d{2}:\d{2}),\d{3}"
thread_patt = r"\[(\d+|\.NET TP Worker)\]"
level_patt = "(?P<level>[A-Z]+)"
logging_class_patt = r"([a-zA-Z0-9]+\.)+(?P<logging_class>[a-zA-Z0-9]+)"
pattern = f"{date_patt} {time_patt} {thread_patt} {level_patt} {logging_class_patt} - (?P<message>.+)"
def strip_crap(line):
    m = re.match(pattern, line)
    if not m:
        return line
    def v(group_name): return m.group(group_name)
    return f"{v('day')}/{v('month')} {v('time')} {v('logging_class')}.{v('level')} - {v('message')}".strip("\\n")


class FollowedLog(Static):
    lines = reactive([])
    lines_read = 0

    def __init__(self, title, filename):
        super().__init__()
        self.title = title
        f = open(filename, "r")
        self.tail = f

    def on_mount(self) -> None:
        # Catch up on previous lines
        self.lines = self.get_new_lines()
        self.update_timer = self.set_interval(1 / 60, self.poll_lines)

    def on_unmount(self) -> None:
        if self.tail:
            self.tail.close()

    def poll_lines(self) -> None:
        if (new_lines := self.get_new_lines()):
            self.lines = self.lines + new_lines

    def get_new_lines(self) -> [str]:
        new_lines = []
        while (l := self.tail.readline()):
            new_lines.append(strip_crap(l))
        return new_lines

    def watch_lines(self, lines: list[str]) ->  None:
        log = self.query_one(RichLog)
        if self.lines and self.lines_read < len(self.lines):
            for i in range(self.lines_read + 1, len(self.lines) + 1):
                log.write(self.lines[i - 1])
            self.lines_read = len(self.lines)

    def on_resize(self, event) -> None:
        """ Rewrite log lines so that wrapping is recalculated for new width """
        rl = self.query_one(RichLog)
        rl.clear()
        for l in self.lines:
            rl.write(l)

    def compose(self) -> ComposeResult:
        yield Static(self.title, classes="title")
        yield RichLog(wrap=True, max_lines=2000)


class LogFollowApp(App):
    CSS_PATH="styles/main.tcss"
    BINDINGS= [
        ("q", "quit", "Quit")
    ]

    def __init__(self, logs):
        super().__init__()
        self.logs = logs

    def compose(self) -> ComposeResult:
        with Horizontal():
            for title, file in self.logs:
                yield FollowedLog(title, file)

        yield Footer()

    def on_key(self, event: events.Key) -> None:
        if event.key.isdigit():
            i = int(event.key)

            children = list(self.query(FollowedLog))
            if i == 0:
                for c in children:
                    c.display = True
            elif i <= len(children):
                for j, c in enumerate(children):
                    if i - 1 == j:
                        c.display = True
                    else:
                        c.display = False


dev_files = [
    ("FileWatcher", "//icatdevingest/c$/FBS/Logs/FileWatcher.log"),
    ("LiveIngest", "//icatdevingest/c$/FBS/Logs/LiveIngest.log"),
    ("XMLtoICAT", "//icatdevingest/c$/FBS/Logs/XMLtoICAT.log")
]
prod_files = [
    ("FileWatcher", "//icatliveingest/c$/FBS/Logs/FileWatcher.log"),
    ("LiveIngest", "//icatliveingest/c$/FBS/Logs/LiveIngest.log"),
    ("XMLtoICAT", "//icatliveingest/c$/FBS/Logs/XMLtoICAT.log")
]
test_files = [
    ("test1", "C:/Users/rop61488/test/test1.log"),
    ("test2", "C:/Users/rop61488/test/test2.log"),
    ("test3", "C:/Users/rop61488/test/test3.log"),
    ("test4", "C:/Users/rop61488/test/test4.log"),
]

if __name__ == "__main__":
    app = LogFollowApp(prod_files)
    app.run()
