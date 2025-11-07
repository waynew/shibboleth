import os
import subprocess
from datetime import datetime
from textwrap import dedent

import rich.markdown as rm
from textual import events, getters, log
from textual.app import App, ComposeResult
from textual.containers import (
    Container,
    Grid,
    Horizontal,
    HorizontalGroup,
    HorizontalScroll,
    Vertical,
    VerticalGroup,
    VerticalScroll,
)
from textual.events import Click
from textual.message import Message
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, Input, Label, Rule, Static, TextArea
from textual.css.query import NoMatches

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
        ("f4", "external_edit", "Edit Raw"),
    ]
    task = reactive(None, recompose=True)
    comment_area = getters.query_one("#new_comment", TextArea)
    comment_list = getters.query_one("#comments")

    def __init__(self, task):
        super().__init__()
        self.task = task

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="cardback-scroll"):
            with VerticalGroup(id="cardback-grid"):
                yield Label(
                    rm.Markdown("# " + self.task.fancy_title.lstrip("#")),
                    classes="title",
                )
                b = Button("X", id="close", compact=True)
                b.can_focus = False
                yield b

                with VerticalGroup(id="cardback-info") as v:
                    v.border_title = "Honk"
                    yield Static(
                        rm.Markdown(f"In list `{self.task.list}`"), classes="subheader"
                    )
                    yield Static(
                        rm.Markdown(f"Due Date: `{self.task.due_date or 'none'}` ")
                    )
                    with HorizontalGroup(id="tag-list"):
                        yield Label("Tags:")
                        any_tags = False
                        for tag in self.task.tags:
                            if tag == self.task.list:
                                continue
                            yield Label(tag, classes="tag")
                            any_tags = True
                        if not any_tags:
                            yield Label("None", classes="no-tags")
                    desc = Static(
                        rm.Markdown(self.task.description), classes="description"
                    )
                    desc.border_title = "Description"
                    yield desc

                    with VerticalGroup(id="comments") as v:
                        v.border_title = "Comments"
                        for comment in self.task.comments:
                            comment_widget = Static(
                                rm.Markdown(comment.content.strip()), classes="comment"
                            )
                            comment_widget.border_title = str(comment.date)
                            yield comment_widget

                    yield TextArea(placeholder="Add a comment", id="new_comment")

                    with Horizontal():
                        yield Button("Save", id="card_save")

                with VerticalGroup(id="side-controls"):
                    yield Label("Add to Card")
                    yield Button("Tags", disabled=True)
                    yield Button("Checklist", disabled=True)
                    yield Button("Due Date", disabled=True)
                    yield Label("Actions")
                    yield Button("Move", disabled=True)
                    yield Button("Copy", disabled=True)
                    yield Button("Archive", disabled=True)

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "close":
            self.action_clean_dismiss()
        elif event.button.id == "card_save":
            self.action_add_comment()

    def action_external_edit(self) -> None:
        with self.app.suspend():
            subprocess.run(["vim", self.task.path])
        self.mutate_reactive(CardBack.task)

    def action_add_comment(self) -> None:
        with self.task.path.open("a") as f:
            now = datetime.now().replace(microsecond=0)
            f.write(
                dedent(f"""

            {now:%Y-%m-%d %H:%M:%S}
            {"-" * 19}

            """)
                + self.comment_area.text
            )
            # self.mutate_reactive(CardBack.task)
        # self.call_later(lambda: self.query_one("#card_save").scroll_visible())
        comment_widget = Static(rm.Markdown(self.comment_area.text), classes="comment")
        comment_widget.border_title = str(now)
        self.comment_area.clear()
        self.comment_list.mount(comment_widget)

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
        ("f4", "external_edit", "Edit Raw"),
    ]

    task = reactive(None)

    class CardMessage(Message):
        def __init__(self, task, card):
            super().__init__()
            self.task = task
            self.card = card

    class Flipped(CardMessage): ...

    class MoveLeft(CardMessage): ...

    class MoveRight(CardMessage): ...

    class MouseMoving(CardMessage): ...

    def __init__(self, task, *args, **kwargs):
        super().__init__(rm.Markdown(task.fancy_title), *args, **kwargs)
        self.task = task

    def action_external_edit(self) -> None:
        with self.app.suspend():
            subprocess.run(["vim", self.task.path])

    def action_go_zoom(self) -> None:
        self.post_message(self.Flipped(task=self.task, card=self))

    def action_move_left(self) -> None:
        self.post_message(self.MoveLeft(task=self.task, card=self))

    def action_move_right(self) -> None:
        self.post_message(self.MoveRight(task=self.task, card=self))

    def on_click(self, event: Click):
        if event.chain > 1:
            self.post_message(self.Flipped(task=self.task, card=self))

    def on_mouse_move(self, event: events.MouseEvent):
        if event.button == 1:
            self.post_message(self.MouseMoving(task=self.task, card=self))


class Column(Static):
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
        with VerticalScroll(can_focus=False) as v:
            v.BINDINGS.clear()
            v.refresh_bindings()
            for task in self.tasks:
                yield Card(task=task)  # rm.Markdown(task.fancy_title), name=task.path)
            yield Input(placeholder="New card...")

    def on_key(self, event: events.Key) -> None:
        if event.key == 'down':
            if not self.app.focused == self.query(Card).last():
                self.screen.focus_next(Card)
        elif event.key == 'up':
            if not self.app.focused == self.query(Card).first():
                self.screen.focus_previous(Card)
        elif event.key == 'right':
            self.post_message(self.NextColumn(self))
        elif event.key == 'left':
            self.post_message(self.PreviousColumn(self))


class Shibboleth(App):
    CSS_PATH = "shibboleth.tcss"
    BINDINGS = [("q", "quit", "Quit")]

    dragged_card = None

    def __init__(self, *args, shibboleth, **kwargs):
        super().__init__(*args, **kwargs)
        self.shibboleth = shibboleth

    def compose(self) -> ComposeResult:
        yield Header()
        with HorizontalScroll():
            # for priority, tasks in shibboleth.tasks_by_priority():
            for list_, tasks in self.shibboleth.tasks_by_list.items():
                col = Column(id=f"col-{list_}")
                col.tasks = tasks
                yield col
        with Horizontal():
            yield Button("Quit", id="quit")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "quit":
            self.exit()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        log("wonk", event.input, event.value, event.input.parent.parent)
        priority = event.input.parent.parent.id[4:]
        if priority == "None":
            priority = None
        task = shibboleth.Task.create_from_content(f"Title: {event.value}")
        task.priority = priority
        log("new task?", task)
        self.update_tasks()

    def on_mount(self) -> None:
        self.screen.focus_next(Card)

    def on_card_flipped(self, event: Card.Flipped) -> None:
        log.debug("Flippin' task:", event.task)
        self.push_screen(CardBack(event.task), self.update_task)

    def on_card_move_left(self, event: Card.MoveLeft) -> None:
        task = event.task
        list_ = task.list
        log.debug(f"Current priority {repr(list_)} {list_}")
        prev_col = None
        columns = list(self.query("Column"))
        for column in columns:
            if column.id == f"col-{list_}":
                if prev_col:
                    event.card.remove()
                    prev_list = prev_col.id[4:]
                    task.list = prev_list
                    card = Card(
                        task=task
                    )  # rm.Markdown(task.fancy_title), name=task.path)
                    prev_col.mount(card, before="Input")
                    card.focus()
                    card.scroll_visible()
            prev_col = column

    def on_card_move_right(self, event: Card.MoveRight) -> None:
        # TODO: make the rest of this like move left -W. Werner, 2025-10-30
        task = event.task
        list_ = task.list
        next_col = None
        columns = list(self.query("Column"))
        for column in reversed(columns):
            if column.id == f"col-{list_}":
                if next_col:
                    event.card.remove()
                    next_list = next_col.id[4:]
                    task.list = next_list
                    card = Card(
                        task=task
                    )  # rm.Markdown(task.fancy_title), name=task.path)
                    next_col.mount(card, before="Input")
                    card.focus()
                    card.scroll_visible()
            next_col = column

    def on_card_mouse_moving(self, event: Card.MouseMoving) -> None:
        if self.dragged_card is None:
            self.dragged_card = Card(task=event.task, classes="moving")
            self.screen.mount(self.dragged_card)
            event.card.parent.focus()
            event.card.remove()

    def on_mouse_move(self, event: events.MouseMove) -> None:
        if event.button == 1:
            if self.dragged_card:
                self.dragged_card.offset = event.screen_offset - (3, 2)
                for widget, region in self.screen.get_widgets_at(*self.mouse_position):
                    if widget.id and widget.id.startswith("col-"):
                        widget.focus()
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
                    list_ = widget.id[4:]
                    if list_ == "None":
                        list_ = None
                    log.debug("new list:", list_)
                    task.list = list_
                    widget.mount(column_card, before="Input")

    def on_column_next_column(self, message: Column.NextColumn):
        list = message.current.id[4:]
        try:
            index = shibboleth.Task.lists.index(list)+1
            while True:
                try:
                    next = shibboleth.Task.lists[index]
                    f = self.query(f"#col-{next} Card").first()
                    f.focus()
                    return
                except NoMatches:
                    index += 1
        except ValueError:
            return

    def on_column_previous_column(self, message: Column.PreviousColumn):
        list = message.current.id[4:]
        try:
            index = shibboleth.Task.lists.index(list)-1
            while True:
                try:
                    next = shibboleth.Task.lists[index]
                    f = self.query(f"#col-{next} Card").first()
                    f.focus()
                    return
                except NoMatches:
                    index -= 1
        except ValueError:
            return

    def update_tasks(self):
        for list_, tasks in self.shibboleth.tasks_by_list.items():
            col = self.query_one(f"#col-{list_}", Column)
            col.tasks = tasks

    def update_task(self, response):
        if response is None:
            pass


def app():
    shibby = shibboleth.Shibboleth()
    shibboleth.WORKDIR = shibboleth.Path(
        os.environ.get("SHIBBOLETH_DIR", ".")
    ).resolve()
    app = Shibboleth(shibboleth=shibby)
    return app


def run():
    return app().run()


if __name__ == "__main__":
    run()
