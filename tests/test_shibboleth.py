import functools
import os
import subprocess
from datetime import datetime
from pathlib import Path
from textwrap import dedent
from unittest import mock

import pytest

import shibboleth


def run_shib(shibby, *cmd, **kwargs):
    output = subprocess.run(["python", shibby, *cmd], capture_output=True, **kwargs)
    return output.stdout.decode(), output.stderr.decode()


@pytest.fixture(autouse=True)
def restore_task_lists():
    shibboleth.Task.lists = [
        "inbox",
        "1-now",
        "2-next",
        "3-soon",
        "4-later",
        "5-someday",
        "6-waiting",
        "done",
        None,
    ]


@pytest.fixture(autouse=True)
def to_tmp_path(tmp_path):
    curdir = os.getcwd()
    try:
        shibboleth.WORKDIR = tmp_path
        os.chdir(tmp_path)
        yield
    finally:
        os.chdir(curdir)


@pytest.fixture
def tmp_path_os_environ(tmp_path):
    with mock.patch.dict(os.environ, {"SHIBBOLETH_DIR": str(tmp_path)}):
        yield tmp_path


@pytest.fixture(
    params=[
        {"config": {}, "raw": b""},
        {
            "config": {
                "lists": ["1-cool", "2-old", "3-done"],
                "tag_colors": {
                    "rouge": "red",
                    "bleu": "rgb(0,0,255)",
                    "verdant": "#00ff00",
                },
            },
            "raw": dedent(
                """
                    lists = ["1-cool", "2-old", "3-done"]
                    [tag_colors]
                    rouge = "red"
                    bleu = "rgb(0,0,255)"
                    verdant = "#00ff00"
                    """
            ).encode(),
        },
    ]
)
def sample_config(tmp_path, request):
    print(request.param)
    (tmp_path / ".shibboleth").write_bytes(request.param["raw"])
    return request.param["config"]


@pytest.fixture(scope="session")
def standalone_shibby(tmp_path_factory):
    shibboleth_file = tmp_path_factory.mktemp("shib") / "shibboleth.py"
    shibboleth_file.write_bytes(Path(shibboleth.__file__).read_bytes())

    yield shibboleth_file


@pytest.fixture
def shibby_with_git(standalone_shibby, tmp_path):
    prev = os.getcwd()
    try:
        os.chdir(tmp_path)
        with open(".gitignore", "w") as f:
            f.write("*.sw[a-p]\n")
        subprocess.run(["git", "init"])
        subprocess.run(["git", "add", "."])
        subprocess.run(["git", "commit", "-m", "initial commit"])
        yield standalone_shibby
    finally:
        os.chdir(prev)


def test_shibboleth_returns_correct_version(standalone_shibby):
    output = subprocess.run(
        ["python", standalone_shibby, "version"], capture_output=True
    )
    stdout, stderr = run_shib(standalone_shibby, "version")
    assert stdout.strip() == shibboleth.__version__


def test_shibboleth_with_no_tasks_should_return_empty_pls(standalone_shibby):
    pytest.skip()


def test_shibboleth_with_SHIBBOLETH_DIR_should_use_the_files_in_that_dir(
    standalone_shibby,
):
    pytest.skip()


def test_shibboleth_should_read_dot_shibboleth_file_from_SHIBBOLETH_DIR(
    standalone_shibby,
):
    pytest.skip()


def test_shibboleth_with_updated_SHIBBOLETH_DIR_should_read_files_from_new_dir(
    standalone_shibby, tmp_path
):
    pytest.skip()


def test_shibboleth_with_SHIBBOLETH_DIR_should_use_list_names_from_dot_shibboleth_file():
    pytest.skip()


def test_when_shibboleth_file_is_selected_it_should_be_stuck_in_dot_last_dot_shib(
    standalone_shibby, tmp_path
):
    pytest.skip()


def test_task_should_use_md_extension_if_not_set(standalone_shibby, tmp_path):
    pytest.skip()


def test_tasks_should_sort_by_sort_tag_first_then_filename():
    pytest.skip()


def test_task_title_should_use_title_from_file_contents():
    pytest.skip()


def test_task_title_should_fallback_to_filename_if_no_title_header():
    pytest.skip()


def test_task_description_should_be_empty_if_only_whitespace_after_header():
    pytest.skip()


def test_task_description_should_have_between_header_and_replies():
    pytest.skip()


def test_task_replies_should_be_split_by_every_line_with_timestamp_and_line():
    pytest.skip()


def test_task_due_date_should_be_in_header():
    pytest.skip()


def test_task_checklist_in_reply_should_have_checklist():
    pytest.skip()


def test_task_checklist_in_details_should_have_checklist():
    pytest.skip()


def test_task_checklist_with_title_should_have_title():
    pytest.skip()


def test_task_checklist_with_no_title_should_have_None_title():
    pytest.skip()


def test_dot_template_files_should_be_available_as_task_new_from_template():
    pytest.skip()


def test_template_file_should_python_format_with_provided_args():
    pytest.skip()


def test_template_file_with_missing_fields_should_error_and_not_create():
    pytest.skip()


def test_shibboleth_flow(subtests, standalone_shibby, tmp_path):
    env = {"SHIBBOLETH_DIR": str(tmp_path)}

    with subtests.test(msg="empty dir should have no tasks"):
        pytest.skip("check pls")
        pytest.skip("check report")
        pytest.skip("assert no files in dir")

    with subtests.test(msg="creating a task should have it exist"):
        pytest.skip("assert new task should be in inbox")

    with subtests.test(msg="creating a task should have the timestamp in tags"):
        pytest.skip()

    with subtests.test(
        msg="shibboleth renames should order tags by timestamp list, then everything else"
    ):
        pytest.skip()

    with subtests.test(msg="by default shibboleth should remove None from taglist"):
        pytest.skip()

    with subtests.test(
        msg="if blocklist tags is overridden in .shibboleth then they should only be removed from tag list"
    ):
        pytest.skip()

    with subtests.test(msg="creating all of the tasks should have them exist"):
        pytest.skip("add task with p1")
        pytest.skip("add task with p2")
        pytest.skip("add task with p3")
        pytest.skip("add task with p4")
        pytest.skip("add task with p5")
        pytest.skip("add task with p6")
        pytest.skip("add task with done")
        pytest.skip("add task with inbox")

    with subtests.test(msg="marking task done should move it to done"):
        pytest.skip()

    with subtests.test(
        msg="moving a task should allow it to move through all priorities"
    ):
        pytest.skip()

    with subtests.test(
        msg="if .shibboleth contains different lists then they should be used"
    ):
        pytest.skip()

    with subtests.test(
        msg="default_list in .shibboleth should create new issues in that list"
    ):
        pytest.skip()

    with subtests.test(msg="done_list in .shibboleth should use that done list"):
        pytest.skip()

    with subtests.test(msg="in_progress should be tasks not in default or done lists"):
        pytest.skip()

    with subtests.test(msg="open tasks should be all tasks not in done_list"):
        pytest.skip()

    with subtests.test(mgs="closed tasks should only be tasks in done list"):
        pytest.skip()


def test_if_shibboleth_autocommit_shibboleth_should_identify_vcs():
    pytest.skip()


def test_if_shibboleth_autocommit_and_not_tracked_or_found_shibboleth_should_error():
    pytest.skip()


def test_shibboleth_autocommit(subtests, shibby_with_git):
    with open(".shibboleth", "w") as f:
        f.write("autocommit = true")

    faux_environment = {"EDITOR": "test"}

    run_shib(shibby_with_git, "new", "asdf", env=faux_environment)
    with subtests.test("new task should commit with expected message"):
        pytest.skip()

    resp = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True)
    prev_hash = resp.stdout.decode()
    with subtests.test("no changes made should not error or commit"):
        run_shib(shibby_with_git, "new", "asdf", env=faux_environment)

        resp = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True)
        post_hash = resp.stdout.decode()
        assert prev_hash == post_hash

    with subtests.test("changes in a dirty directory should warn"):
        pytest.skip()

    with subtests.test(
        "changes in a dirty directory with staged changes should reset and warn"
    ):
        pytest.skip()

    with subtests.test(
        "changes in a dirty directory with staged changes but no task changes should warn but leave index"
    ):
        pytest.skip()

    with subtests.test("updating a task should commit with expected message"):
        pytest.skip()

    with subtests.test(
        "updating a tag or filename with comment should commit changes first and rename second"
    ):
        pytest.skip()


def test_shibboleth_should_use_SHIBBOLETH_DIR_env_var_when_present(tmp_path):
    with mock.patch.dict(os.environ, {"SHIBBOLETH_DIR": str(tmp_path)}):
        shibby = shibboleth.Shibboleth()
        assert shibby.root_dir == tmp_path


def test_shibboleth_should_use_current_dir_if_SHIBBOLETH_DIR_not_in_environ(tmp_path):
    os.chdir(tmp_path)
    expected_path = Path(".").resolve()
    with mock.patch.dict(os.environ, {}, clear=True):
        assert os.environ == {}
        shibby = shibboleth.Shibboleth()
        assert shibby.root_dir == expected_path


def test_if_dot_shibboleth_is_found_in_SHIBBOLETH_DIR_then_shibboleth_should_load_settings(
    tmp_path_os_environ, sample_config
):
    expected_config = sample_config
    shibby = shibboleth.Shibboleth()
    assert shibby.config == expected_config


def test_shibboleth_tasks_by_list_should_use_defaults_if_not_set(tmp_path_os_environ):
    path = tmp_path_os_environ
    expected_lists = (
        "inbox",
        "1-now",
        "2-next",
        "3-soon",
        "4-later",
        "5-someday",
        "6-waiting",
        "done",
        None,
    )
    for expected in expected_lists:
        if expected is None:
            continue
        (path / f"somefile-name[{expected} cool beans].md").touch()
    (path / "another file[no priority found here].md").touch()
    shibby = shibboleth.Shibboleth()
    tasks = shibby.tasks_by_list
    for expected_list in expected_lists:
        if expected_list is None:
            continue
        assert (
            tasks[expected_list][0].filename
            == f"somefile-name[{expected_list} cool beans].md"
        )

    assert tasks[None][0].filename == "another file[no priority found here].md"


def test_shibboleth_tasks_by_list_should_use_lists_defined_in_dot_shibboleth_file(
    tmp_path_os_environ,
):
    path = tmp_path_os_environ

    first_lists = ("todo", "in-progress", "done")
    second_lists = ("roscivs", "bottia", "ipsum")

    (path / "one[todo roscivs].md").touch()
    (path / "two[todo roscivs].md").touch()
    (path / "three[todo roscivs].md").touch()

    (path / ".shibboleth").write_text('lists = ["todo", "in-progress", "done"]')
    shibby = shibboleth.Shibboleth()

    tasks = shibby.tasks_by_list
    actual_lists = tuple(tasks)
    assert actual_lists == first_lists

    (path / ".shibboleth").write_text('lists = ["roscivs", "bottia", "ipsum"]')
    shibby = shibboleth.Shibboleth()

    tasks = shibby.tasks_by_list
    actual_lists = tuple(tasks)
    assert actual_lists == second_lists


@pytest.mark.parametrize(
    "lists, tags",
    [
        ((), ("one", "two", "fnord", "any")),
        (
            ("one", "two", "three"),
            ("nothing", "to", "see", "here", "four", "3", "1", "2"),
        ),
        (("whatever", "is", "this", "banana"), ("fnord", "fnordy", "fnordzilla")),
    ],
)
def test_task_should_have_None_list_if_tags_not_in_any_Task_list(lists, tags, tmp_path):
    task_file = tmp_path / "fnord.md"
    task_file.touch()
    shibboleth.Task.lists = lists

    task = shibboleth.Task(path=task_file)
    task.tags.extend(tags)

    assert task.list is None


@pytest.mark.parametrize(
    "lists, tags",
    [
        (("good",), ("good",)),
        (("good"), ("one", "good", "two", "fnord", "any")),
        (
            ("one", "two", "three"),
            ("one", "nothing", "to", "see", "here", "four", "3", "1", "2"),
        ),
        (("whatever", "is", "this", "banana"), ("is", "fnord", "fnordy", "fnordzilla")),
    ],
)
def test_task_should_have_matching_list_if_tags_has_Task_list_in_tags(
    lists, tags, tmp_path
):
    task_file = tmp_path / "fnord.md"
    task_file.touch()
    shibboleth.Task.lists = lists

    task = shibboleth.Task(path=task_file)
    task.tags.extend(tags)

    print(task.tags)
    assert any(t in shibboleth.Task.lists for t in task.tags)
    assert task.list in lists


def test_task_from_content_should_have_md_extension():
    task = shibboleth.Task.create_from_content("Title: something silly")
    assert task.filename == "something-silly[inbox].md"


@pytest.mark.parametrize(
    "raw,expected_description,expected_comments",
    [
        [
            dedent(
                """
                Title: something silly
                """
            ).lstrip(),
            "",
            [],
        ],
        [
            dedent(
                """
            Title: something silly

            This is a description




            2025-11-02 10:27:05
            -------------------

            This is the first *comment*.

            Let's go!

            2025-11-02 10:28:56
            -------------------

            This one only has one line

        """
            ).lstrip(),
            "This is a description\n\n\n\n\n",
            [
                shibboleth.Comment(
                    date=datetime(2025, 11, 2, 10, 27, 5),
                    content="This is the first *comment*.\n\nLet's go!\n\n",
                ),
                shibboleth.Comment(
                    date=datetime(2025, 11, 2, 10, 28, 56),
                    content="This one only has one line\n\n",
                ),
            ],
        ],
    ],
)
def test_task_description_and_comments_should_be_correctly_set(
    raw, expected_description, expected_comments
):
    task = shibboleth.Task.create_from_content(raw)
    assert task.description == expected_description
    assert list(task.comments) == expected_comments


@pytest.mark.parametrize(
    "raw",
    [
        dedent("""
            """),
        dedent("""
            Nothing to see here.

            Nothing at all.

            Who cares at all? Bleep bloop whatever.
            """),
    ],
)
def test_Comment_parse_should_return_None_when_no_header(raw):
    comment, rest = shibboleth.Comment.parse(raw)
    assert comment == None
    assert rest == raw


@pytest.mark.parametrize(
    "raw",
    [
        dedent(
            """
            Ignore me

            2021-01-02 03:04:05
            -------------------

            Fnord
            Fnord

            """
        ),
        dedent(
            """
            2021-01-02 03:04:05
            -------------------

            Fnord
            Fnord

            """
        ),
        dedent(
            """
            Hello beans

            2021-01-02 03:04:05
            -------------------

            Fnord
            Fnord

            2021-01-02 03:04:05
            -------------------

            ignore me, too
            """
        ),
    ],
)
def test_Comment_parse_should_return_first_segment(raw):
    comment, rest = shibboleth.Comment.parse(raw)
    assert comment.date == datetime(2021, 1, 2, 3, 4, 5)
    assert comment.content == "Fnord\nFnord\n\n"
