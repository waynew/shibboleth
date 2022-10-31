import os
import time
import shutil
import io
import shibboleth
import tempfile
import unittest
import unittest.mock as mock
import datetime

from pathlib import Path


class TestShibboleth(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.pwd = os.getcwd()
        os.chdir(self.tempdir)
        self.shib = shibboleth.Shibboleth()

    def tearDown(self):
        os.chdir(self.pwd)
        if hasattr(self._outcome, 'errors'):
            result = self.defaultTestResult()
            self._feedErrorsToResult(result, self._outcome.errors)
        else:
            result = self._outcome.result
        ok = all(test != self for test, text in result.errors + result.failures)
        if ok:
            shutil.rmtree(self.tempdir)
        else:
            print(f'{chr(10)}Leaving temp dir {self.tempdir} around on test failures')

    def test_shibboleth(self):
        # On creation, no tasks should be there.
        tasks = self.shib.ls()
        self.assertEqual(tasks, [])

        # After creating a new task, it should be list-able
        expected_title = "this_is_my_first_task"
        create_time = datetime.datetime(year=2010, month=8, day=14)
        self.shib.new(title="this is my first task", create_time=create_time)
        tasks = self.shib.ls()
        self.assertEqual(tasks[0].title, expected_title)

        # also it should automatically be in the inbox
        tasks = self.shib.ls(priority='inbox')
        self.assertEqual(tasks[0].title, expected_title)

        # also it should be selected/current, and have the correct contents
        self.assertEqual(self.shib.selected.read(), "Title: this is my first task\n\n")

        # and it should have correct filename 
        self.assertEqual(self.shib.selected.filename, 'this_is_my_first_task[20100814~000000 inbox].md')

        # Creating a task with no provided create_time should create one with some time after now
        before = datetime.datetime.now() - datetime.timedelta(seconds=2)
        self.shib.new(title='delete me')
        after = datetime.datetime.now() + datetime.timedelta(seconds=2)
        self.assertLess(before, self.shib.selected.timestamp)
        self.assertLess(self.shib.selected.timestamp, after)
        
        # rm should delete the task
        self.shib.rm()
        titles = [task.title for task in self.shib.ls()]
        self.assertNotIn('delete_me', titles)

        # Creating a bunch of tasks should all have correct filenames/titles/priorities

        # Making a new task will put it in the inbox
        self.shib.new(title="this is my now task", create_time=create_time)
        tasks = self.shib.ls()
        self.assertEqual([task.filename for task in tasks],
            [
                'this_is_my_now_task[20100814~000000 inbox].md',
                'this_is_my_first_task[20100814~000000 inbox].md',
            ]
        )

        # Now set to 1-now priority
        self.shib.selected.priority = '1-now'
        tasks = self.shib.ls()
        self.assertEqual([task.filename for task in tasks],
            [
                'this_is_my_now_task[20100814~000000 1-now].md',
                'this_is_my_first_task[20100814~000000 inbox].md',
            ]
        )

        # Again, the new one should be in the inbox
        self.shib.new(title="this is my next task", create_time=create_time)
        tasks = self.shib.ls()
        self.assertEqual([task.filename for task in tasks],
            [
                'this_is_my_next_task[20100814~000000 inbox].md',
                'this_is_my_now_task[20100814~000000 1-now].md',
                'this_is_my_first_task[20100814~000000 inbox].md',
            ]
        )

        # until we change it
        self.shib.selected.priority = '2-next'
        tasks = self.shib.ls()
        self.assertEqual([task.filename for task in tasks],
            [
                'this_is_my_next_task[20100814~000000 2-next].md',
                'this_is_my_now_task[20100814~000000 1-now].md',
                'this_is_my_first_task[20100814~000000 inbox].md',
            ]
        )

        # That's probably good enough to just create the rest of them
        for title in ("this is my soon task", "this is my later task", "this is my someday task", "this is my waiting task"):
            self.shib.new(title=title, create_time=create_time)

        tasks = self.shib.ls()
        self.assertEqual([task.filename for task in tasks],
            [
                'this_is_my_next_task[20100814~000000 2-next].md',
                'this_is_my_someday_task[20100814~000000 inbox].md',
                'this_is_my_waiting_task[20100814~000000 inbox].md',
                'this_is_my_soon_task[20100814~000000 inbox].md',
                'this_is_my_now_task[20100814~000000 1-now].md',
                'this_is_my_later_task[20100814~000000 inbox].md',
                'this_is_my_first_task[20100814~000000 inbox].md',
            ]
        )

        # Let's set their titles
        self.shib.select('soon').priority = '3-soon'
        self.shib.select('later').priority = '4-later'
        self.shib.select('someday').priority = '5-someday'
        self.shib.select('waiting').priority = '6-waiting'

        tasks = self.shib.ls()
        self.assertEqual([task.filename for task in tasks],
            [
                'this_is_my_next_task[20100814~000000 2-next].md',
                'this_is_my_soon_task[20100814~000000 3-soon].md',
                'this_is_my_waiting_task[20100814~000000 6-waiting].md',
                'this_is_my_later_task[20100814~000000 4-later].md',
                'this_is_my_someday_task[20100814~000000 5-someday].md',
                'this_is_my_now_task[20100814~000000 1-now].md',
                'this_is_my_first_task[20100814~000000 inbox].md',
            ]
        )

        # ls with priority should only return those with that priority
        self.assertEqual([task.filename for task in self.shib.ls(priority='inbox')],
                ['this_is_my_first_task[20100814~000000 inbox].md'])

        self.assertEqual([task.filename for task in self.shib.ls(priority='1-now')],
                ['this_is_my_now_task[20100814~000000 1-now].md'])

        self.assertEqual([task.filename for task in self.shib.ls(priority='2-next')],
                ['this_is_my_next_task[20100814~000000 2-next].md'])

        self.assertEqual([task.filename for task in self.shib.ls(priority='3-soon')],
                ['this_is_my_soon_task[20100814~000000 3-soon].md'])

        self.assertEqual([task.filename for task in self.shib.ls(priority='4-later')],
                ['this_is_my_later_task[20100814~000000 4-later].md'])

        self.assertEqual([task.filename for task in self.shib.ls(priority='5-someday')],
                ['this_is_my_someday_task[20100814~000000 5-someday].md'])

        self.assertEqual([task.filename for task in self.shib.ls(priority='6-waiting')],
                ['this_is_my_waiting_task[20100814~000000 6-waiting].md'])

        # if None or '' is passed to select, selected should be None
        self.shib.select(None)
        self.assertEqual(self.shib.selected, None)

        self.shib.select('someday')
        self.assertNotEqual(self.shib.selected, None)

        self.shib.select('')
        self.assertEqual(self.shib.selected, None)


        # Tagging a task should add the tag but only once
        self.shib.select('first')
        self.shib.tag('boop')
        self.shib.tag('boop')
        self.assertIn('boop', self.shib.selected.tags)

        # Untag should remove the tag if it's there but do nothing otherwise
        self.shib.untag('boop')
        self.assertNotIn('boop', self.shib.selected.tags)
        self.shib.untag('boop')

        # ls should ignore done
        count = len(self.shib.ls())
        fname = self.shib.selected.filename
        self.shib.complete()
        self.assertEqual(len(self.shib.ls()), count-1)
        self.assertTrue(Path('completed', fname.replace('inbox', 'done')).exists())



class TestShibbolethTask(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.pwd = os.getcwd()
        os.chdir(self.tempdir.name)

    def tearDown(self):
        os.chdir(self.pwd)
        self.tempdir.cleanup()

    def test_should_parse_title_from_filename(self):
        test_titles = [
            ('This is a cool title', ''),
            ('This a', '[title with tags]'),
        ]

        for expected_title, tags in test_titles:
            with self.subTest():
                fname = f'{expected_title}{tags}.md'

                task = shibboleth.Task(fname)

                self.assertEqual(task.title, expected_title)

    def test_filename_with_no_extension_or_tags_should_all_be_title(self):
        expected_title = 'This is some thing'

        task = shibboleth.Task(expected_title)

        assert task.title == expected_title
        assert task.ext is None, f'{task.ext}'

    def test_should_parse_tags_from_filename(self):
        test_names = [
            ('This is a cool title', None),
            ('This is a title with no tags', []),
            ('This has some tags', ['one']),
            ('This has more tags', ['more', 'tags', 'are', 'here']),
        ]
        for title, tags in test_names:
            if tags is None:
                fname = f'{title}.fnord'
            else:
                fname = f'{title}[{" ".join(tags)}].fnord'

            with self.subTest():
                task = shibboleth.Task(fname)

                self.assertEqual(task.tags, tags or [])

    def test_should_parse_extension_from_filename(self):
        test_exts = [None, '', 'foo', 'bar']
        for expected_ext in test_exts:
            if expected_ext is None:
                fname = 'title'
            else:
                fname = f'title.{expected_ext}'

            with self.subTest():
                task = shibboleth.Task(fname)

                assert task.ext == expected_ext, f'{task.ext!r} != {expected_ext!r}'

    def test_filename_after_parsing_should_be_same_as_original(self):
        expected_fnames = [
            'foo bar [bang quux].md',
            'zippy',
            'doo dah [whoop de doo].quux',
        ]
        for expected_fname in expected_fnames:

            with self.subTest():
                task = shibboleth.Task(expected_fname)

                self.assertEqual(task.filename, expected_fname)

    def test_filename_after_sorting_tags_should_have_tags_in_ascii_sort_order(self):
        old_filename = Path('foo bar [zoo bar apple].quux')
        old_filename.touch()
        expected_fname = 'foo bar [apple bar zoo].quux'

        task = shibboleth.Task(old_filename.name)
        task.tags.sort()

        self.assertEqual(task.filename, expected_fname)

    def test_changing_the_task_title_should_rename_the_file(self):
        new_title = "This is a task full of awesome"
        old_filename = Path(self.tempdir.name) / f'something old.txt'
        expected_filename = Path(self.tempdir.name) / f'{new_title}.txt'
        old_filename.touch()
        task = shibboleth.Task(old_filename.name)

        task.title = new_title

        self.assertTrue(expected_filename.exists())

    def test_when_tag_is_appended_it_should_rename_the_file(self):
        old_filename = Path(self.tempdir.name) / f'something old[boring].txt'
        expected_filename = (
            Path(self.tempdir.name) / f'something old[boring and new].txt'
        )
        old_filename.touch()
        task = shibboleth.Task(old_filename.name)

        task.tags.append('and')
        task.tags.append('new')

        self.assertTrue(expected_filename.exists(), str(os.listdir()))

    def test_when_tags_are_extended_it_should_rename_the_file(self):
        old_filename = Path(self.tempdir.name) / f'something old[boring].txt'
        expected_filename = (
            Path(self.tempdir.name) / f'something old[boring and new].txt'
        )
        old_filename.touch()
        task = shibboleth.Task(old_filename.name)

        task.tags.extend(['and', 'new'])

        self.assertTrue(expected_filename.exists(), str(os.listdir()))

    def test_when_tags_are_sorted_it_should_rename_the_file(self):
        old_filename = Path('foo bar [zoo bar apple].quux')
        old_filename.touch()
        expected_filename = Path('foo bar [apple bar zoo].quux')
        task = shibboleth.Task(old_filename.name)

        task.tags.sort()

        self.assertTrue(expected_filename.exists(), str(os.listdir()))

    def test_when_tag_is_removed_it_should_rename_the_file(self):
        old_filename = Path('foo bar [here gone].quux')
        old_filename.touch()
        expected_filename = Path('foo bar [gone].quux')
        task = shibboleth.Task(old_filename.name)

        task.tags.remove('here')

        self.assertTrue(expected_filename.exists(), str(os.listdir()))

    def test_when_no_priority_is_in_tag_it_should_be_None(self):
        filename = f'priority testing[No priority here].test'

        task = shibboleth.Task(filename)

        self.assertTrue(task.priority is None, 'priority was not None!')

    def test_when_priority_is_in_tag_it_should_be_set(self):
        for priority in shibboleth.PRIORITIES.values():
            filename = f'priority testing[{priority}].test'

            task = shibboleth.Task(filename)

            with self.subTest():
                self.assertEqual(
                    task.priority,
                    priority,
                    f'Tags: {task.tags!r} - priority: {task.priority}',
                )

    def test_when_priority_is_changed_it_should_modify_priority_tags(self):
        old_filename = Path('foo bar [here gone].quux')
        old_filename.touch()
        expected_filename = Path('foo bar [here gone 1-now].quux')
        task = shibboleth.Task(old_filename.name)

        task.priority = '1-now'

        self.assertTrue(expected_filename.exists(), str(os.listdir()))

    def test_when_priority_is_set_to_None_it_should_remove_tag(self):
        old_filename = Path('foo bar [here gone 1-now].quux')
        old_filename.touch()
        expected_filename = Path('foo bar [here gone].quux')
        task = shibboleth.Task(old_filename.name)

        task.priority = None

        self.assertTrue(expected_filename.exists(), str(os.listdir()))

    def test_colorized_should_set_expected_colors_on_filename(self):
        filename_template = 'this is [some {}]'
        for priority in shibboleth.PRIORITIES.values():
            filename = filename_template.format(priority)
            expected_filename = filename
            for tag in ['some', priority]:
                color = shibboleth.DEFAULT_COLORS.get(tag, '32')
                colorized = f'\x1b[{color}m{tag}\x1b[0m'
                expected_filename = expected_filename.replace(tag, colorized)
            task = shibboleth.Task(filename)

            with self.subTest():
                self.assertEqual(task.colorized_filename, expected_filename)

    def test_complete_should_remove_priority_and_tag_and_move_to_completed(self):
        old_filename = Path('foo bar [here gone 1-now].quux')
        old_filename.touch()
        expected_filename = Path('completed', 'foo bar [here gone done].quux')
        task = shibboleth.Task(old_filename.name)

        task.complete()

        self.assertTrue(expected_filename.exists(), str(os.listdir('completed')))

    def test_task_read_should_return_contents_of_the_file(self):
        expected_text = 'The quick brown fox\njumps\n\nover the\tlazy dogs'
        old_filename = Path('foo bar [here gone 1-now].quux')
        old_filename.touch()
        old_filename.write_text(expected_text)

        task = shibboleth.Task(old_filename.name)

        self.assertEqual(task.read(), expected_text)

    ###############################################################
    ###############################################################
    ## TODO: These need their own test class? Or move to pytest? ##
    ###############################################################
    ###############################################################
    def test_log_command(self):
        expected_log = "Logging turned on, level - 'INFO'\nTurning logging off\n"
        expected_stdout = 'Logging is OFF\nLogging is ON - writing to shibboleth.log\nLogging is OFF\n'
        with mock.patch('sys.stdout', io.StringIO()) as fake_out:
            shib = shibboleth.ShibbolethLoop()
            shib.onecmd('log')
            shib.onecmd('log on info')
            shib.onecmd('log off')
            fake_out.seek(0)
            self.assertEqual(fake_out.read(), expected_stdout)
        os.system('cp shibboleth.log /tmp/shib.log')
        with open('shibboleth.log') as f:
            log = f.read()
            self.assertEqual(log, expected_log)


if __name__ == '__main__':
    # unittest.main((TestShibbolethTask(), TestShibboleth()))
    unittest.main()
