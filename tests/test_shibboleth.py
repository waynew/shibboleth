import os
import functools
import subprocess
from pathlib import Path

import pytest

import shibboleth


def run_shib(shibby, *cmd):
    output = subprocess.run(
        ["python", shibby, *cmd], capture_output=True
    )
    return output.stdout.decode(), output.stderr.decode()


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
        with open('.gitignore', 'w') as f:
            f.write('*.sw[a-p]\n')
        subprocess.run(['git', 'init'])
        subprocess.run(['git', 'add', '.'])
        subprocess.run(['git', 'commit', '-m', 'initial commit'])
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

def test_shibboleth_with_SHIBBOLETH_DIR_should_use_the_files_in_that_dir(standalone_shibby):
    pytest.skip()

def test_shibboleth_should_read_dot_shibboleth_file_from_SHIBBOLETH_DIR(standalone_shibby):
    pytest.skip()

def test_shibboleth_with_updated_SHIBBOLETH_DIR_should_read_files_from_new_dir(standalone_shibby, tmp_path):
    pytest.skip()

def test_shibboleth_with_SHIBBOLETH_DIR_should_use_list_names_from_dot_shibboleth_file():
    pytest.skip()

def test_when_shibboleth_file_is_selected_it_should_be_stuck_in_dot_last_dot_shib(standalone_shibby, tmp_path):
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
    env = {'SHIBBOLETH_DIR': str(tmp_path)}

    with subtests.test(msg="empty dir should have no tasks"):
        pytest.skip('check pls')
        pytest.skip('check report')
        pytest.skip('assert no files in dir')

    with subtests.test(msg="creating a task should have it exist"):
        pytest.skip('assert new task should be in inbox')

    with subtests.test(msg='creating a task should have the timestamp in tags'):
        pytest.skip()

    with subtests.test(msg='shibboleth renames should order tags by timestamp list, then everything else'):
        pytest.skip()

    with subtests.test(msg="by default shibboleth should remove None from taglist"):
        pytest.skip()

    with subtests.test(msg="if blocklist tags is overridden in .shibboleth then they should only be removed from tag list"):
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

    with subtests.test(msg="moving a task should allow it to move through all priorities"):
        pytest.skip()

    with subtests.test(msg="if .shibboleth contains different lists then they should be used"):
        pytest.skip()

    with subtests.test(msg="default_list in .shibboleth should create new issues in that list"):
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
    with open('.shibboleth', 'w') as f:
        f.write('autocommit = true')

    
    resp = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True)
    prev_hash = resp.stdout.decode()
    with subtests.test("no changes made should not error or commit"):


        resp = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True)
        post_hash = resp.stdout.decode()
        assert prev_hash == post_hash

    with subtests.test("changes in a dirty directory should warn"):
        pytest.skip()

    with subtests.test("changes in a dirty directory with staged changes should reset and warn"):
        pytest.skip()

    with subtests.test("changes in a dirty directory with staged changes but no task changes should warn but leave index"):
        pytest.skip()

    with subtests.test("new task should commit with expected message"):
        pytest.skip()

    with subtests.test("updating a task should commit with expected message"):
        pytest.skip()

    with subtests.test("updating a tag or filename with comment should commit changes first and rename second"):
        pytest.skip()
