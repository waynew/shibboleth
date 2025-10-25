import os
from datetime import datetime
from textwrap import dedent

import rich.markdown as rm
from textual import events, getters, log
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, HorizontalScroll, VerticalScroll
from textual.events import Click
from textual.message import Message
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, Input, Label, Static, TextArea

import shibboleth

PRIORITIES = {
    None: {"prev": "done", "next": None},
    "inbox": {"prev": None, "next": "1-now"},
    "1-now": {"prev": "inbox", "next": "2-next"},
    "2-next": {"prev": "1-now", "next": "3-soon"},
    "3-soon": {"prev": "2-next", "next": "4-later"},
    "4-later": {"prev": "3-soon", "next": "5-someday"},
    "5-someday": {"prev": "4-later", "next": "6-waiting"},
    "6-waiting": {"prev": "5-someday", "next": "done"},
    "done": {"prev": "6-waiting", "next": None},
}


class CardBack(ModalScreen):
    BINDINGS = [
        ("ctrl+enter", "add_comment", "Add Comment"),
        ("escape", "clean_dismiss", "Back"),
    ]
    task = reactive(None, recompose=True)
    comment_area = getters.query_one("#new_comment", TextArea)

    def __init__(self, task):
        super().__init__()
        self.task = task

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Button("X", id="close")
        with VerticalScroll():
            yield Label(rm.Markdown("# " + self.task.fancy_title.lstrip("#")))
            yield Static(rm.Markdown(self.task.content))
            ta = TextArea(placeholder="Add a comment...", id="new_comment")
            ta.focus()
            yield ta
            yield Button("Save", id="card_save")

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "close":
            self.action_clean_dismiss()
        elif event.button.id == "card_save":
            self.action_add_comment()

    def action_add_comment(self) -> None:
        with self.task.path.open("a") as f:
            f.write(
                dedent(f"""

            {datetime.now():%Y-%m-%d %H:%M:%S}
            {"-" * 19}

            {self.comment_area.text}
            """)
            )
            self.mutate_reactive(CardBack.task)
        self.comment_area.clear()
        self.call_later(lambda: self.query_one("#card_save").scroll_visible())

    def action_clean_dismiss(self) -> None:
        if self.comment_area.text:
            self.app.notify("Comment area has text", severity="warning")
        else:
            self.dismiss()

    def on_mouse_up(self, event: events.MouseUp):
        widget, region = self.get_widget_at(event.screen_x, event.screen_y)
        if widget is self:
            self.action_clean_dismiss()


class Card(Static, can_focus=True):
    BINDINGS = [
        ("enter", "go_zoom", "Zoom"),
        ("<", "move_left", "Move Card Left"),
        (">", "move_right", "Move Card Right"),
    ]

    task = reactive(None)

    class Flipped(Message):
        def __init__(self, task):
            super().__init__()
            self.task = task

    class MoveLeft(Message):
        def __init__(self, filename, card):
            super().__init__()
            self.filename = filename
            self.card = card

    class MoveRight(Message):
        def __init__(self, filename, card):
            super().__init__()
            self.filename = filename
            self.card = card

    class MouseMoving(Message):
        def __init__(self, task, card):
            super().__init__()
            self.task = task
            self.card = card

    def __init__(self, task, *args, **kwargs):
        super().__init__(rm.Markdown(task.fancy_title), *args, **kwargs)
        self.task = task

    def action_go_zoom(self) -> None:
        self.post_message(
            self.Flipped(self.content, filename=self.task.filename)
        )  # self.name))

    def action_move_left(self) -> None:
        self.post_message(self.MoveLeft(filename=self.name, card=self))

    def action_move_right(self) -> None:
        self.post_message(self.MoveRight(filename=self.name, card=self))

    def on_click(self, event: Click):
        if event.chain > 1:
            self.post_message(self.Flipped(task=self.task))

    def on_mouse_move(self, event: events.MouseEvent):
        if event.button == 1:
            self.post_message(self.MouseMoving(task=self.task, card=self))


class Column(Static):
    BINDINGS = [
        ("down", "next_card", "Next Card"),
        ("up", "prev_card", "Previous Card"),
        ("right", "next_column", "Next Column"),
        ("left", "previous_column", "Previous Column"),
    ]
    tasks = reactive([], recompose=True)
    DEFAULT_CSS = """
        Column {
            border: solid;
        }

        Column Container.header {
            content-align: center top;
        }

    """

    class NextColumn(Message):
        def __init__(self, current):
            super().__init__()
            self.current = current

    class PreviousColumn(Message):
        def __init__(self, current):
            super().__init__()
            self.current = current

    def compose(self) -> ComposeResult:
        yield Static(self.id[4:])
        with VerticalScroll(can_focus=False):
            for task in self.tasks:
                yield Card(task=task)  # rm.Markdown(task.fancy_title), name=task.path)
            yield Input(placeholder="New card...")

    def action_next_card(self) -> None:
        if not self.app.focused == self.query(Card).last():
            self.screen.focus_next(Card)

    def action_prev_card(self) -> None:
        if not self.app.focused == self.query(Card).first():
            self.screen.focus_previous(Card)

    def action_next_column(self) -> None:
        self.post_message(self.NextColumn(self))

    def action_previous_column(self) -> None:
        self.post_message(self.PreviousColumn(self))


class Shibboleth(App):
    CSS_PATH = "shibboleth.tcss"
    BINDINGS = [("q", "quit", "Quit")]

    dragged_card = None

    def compose(self) -> ComposeResult:
        yield Header()
        with HorizontalScroll():
            for priority, tasks in shibboleth.tasks_by_priority():
                col = Column(id=f"col-{priority}")
                col.tasks = tasks
                yield col
        with Horizontal():
            yield Button("Quit", id="quit")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "quit":
            self.exit()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        log("wonk", event.input, event.value)
        task = shibboleth.Task.create_from_content(f"Title: {event.value}")
        log("new task?", task)
        self.update_tasks()

    def on_mount(self) -> None:
        self.screen.focus_next(Card)

    def on_card_flipped(self, event: Card.Flipped) -> None:
        log.debug("Flippin' task:", event.task)
        self.push_screen(CardBack(event.task), self.update_task)

    def on_card_move_left(self, event: Card.MoveLeft) -> None:
        task = shibboleth.Task(event.filename)
        priority = task.priority
        log.debug(f"Current priority {priority}")
        prev_priority = PRIORITIES[priority]["prev"]
        if prev_priority is not None:
            log.debug(f"Moving card to {prev_priority}")
            event.card.remove()
            task.priority = prev_priority
            prev_col = self.query_one(
                f"#col-{prev_priority} VerticalScroll", VerticalScroll
            )
            card = Card(task=task)  # rm.Markdown(task.fancy_title), name=task.path)
            prev_col.mount(card, before="Input")
            card.focus()
            card.scroll_visible()

    def on_card_move_right(self, event: Card.MoveRight) -> None:
        task = shibboleth.Task(event.filename)
        priority = task.priority
        next_priority = PRIORITIES[priority]["next"]
        if next_priority is not None:
            event.card.remove()
            task.priority = next_priority
            next_col = self.query_one(
                f"#col-{next_priority} VerticalScroll", VerticalScroll
            )
            card = Card(task=task)  # rm.Markdown(task.fancy_title), name=task.path)
            next_col.mount(card, before="Input")
            card.focus()
            card.scroll_visible()

    def on_card_mouse_moving(self, event: Card.MouseMoving) -> None:
        if self.dragged_card is None:
            self.dragged_card = Card(task=event.task, classes="moving")
            self.screen.mount(self.dragged_card)
            event.card.remove()

    def on_mouse_move(self, event: events.MouseMove) -> None:
        if event.button == 1:
            if self.dragged_card:
                self.dragged_card.offset = event.screen_offset - (3, 2)
            else:
                log("moving")

    def on_mouse_up(self, event: events.MouseUp) -> None:
        if self.dragged_card:
            task = self.dragged_card.task
            column_card = Card(task=task)
            self.dragged_card.remove()
            self.dragged_card = None
            for widget, region in self.screen.get_widgets_at(*self.mouse_position):
                if widget.id and widget.id.startswith("col-"):
                    priority = widget.id[4:]
                    log.debug("new priority:", priority)
                    task.priority = priority
                    widget.mount(column_card, before="Input")

    def on_column_next_column(self, message: Column.NextColumn):
        self.screen.focus_next(Card)
        return

        col_id = message.current.id
        priority = col_id[4:]
        if priority in PRIORITIES:
            next_priority = PRIORITIES[priority]["next"]
            if next_priority is not None:
                next_col = self.query_one(f"#col-{next_priority}", Column)
                next_col.focus(Card)

    def on_column_previous_column(self, message: Column.PreviousColumn):
        self.screen.focus_previous(Card)
        return
        col_id = message.current.id
        priority = col_id[4:]
        if priority in PRIORITIES:
            prev_priority = PRIORITIES[priority]["prev"]
            if prev_priority is not None:
                prev_col = self.query(f"#col-{prev_priority}", Column)
                prev_col.query(Card).first().focus()
                prev_col.focus(Card)
            self.screen.focus_next(Card)

    def update_tasks(self):
        for priority, tasks in shibboleth.tasks_by_priority():
            col = self.query_one(f"#col-{priority}", Column)
            col.tasks = tasks

    def update_task(self, response):
        if response is None:
            pass


def app():
    shibboleth.WORKDIR = shibboleth.Path(
        os.environ.get("SHIBBOLETH_DIR", ".")
    ).resolve()
    app = Shibboleth()
    return app


def run():
    return app().run()


if __name__ == "__main__":
    app = Shibboleth()
