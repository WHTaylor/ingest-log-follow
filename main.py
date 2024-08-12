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

    def __init__(self, filename):
        super().__init__()
        f = open(filename, "r")
        fsize = f.tell()
        f.seek(max(fsize - 2048, 0), 0) # Seek back a couple KB (hopefully enough)
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
                log.write(self.lines[i - 1], shrink=True)
            self.lines_read = len(self.lines)

    def compose(self) -> ComposeResult:
        yield RichLog(wrap=True, max_lines=2000)


class LogFollowApp(App):
    CSS_PATH="styles/main.tcss"
    BINDINGS= [
        ("q", "quit", "Quit")
    ]

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield FollowedLog("//icatliveingest/c$/FBS/Logs/FileWatcher.log")
            yield FollowedLog("//icatliveingest/c$/FBS/Logs/LiveIngest.log")
            yield FollowedLog("//icatliveingest/c$/FBS/Logs/XMLtoICAT.log")
        yield Footer()

if __name__ == "__main__":
    app = LogFollowApp()
    app.run()
