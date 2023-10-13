import os
import io
import shibboleth
import tempfile
import unittest
import unittest.mock as mock

from pathlib import Path


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
        expected_filename = Path(self.tempdir.name) / f'something old[boring and new].txt'
        old_filename.touch()
        task = shibboleth.Task(old_filename.name)

        task.tags.append('and')
        task.tags.append('new')

        self.assertTrue(expected_filename.exists(), str(os.listdir()))

    def test_when_tags_are_extended_it_should_rename_the_file(self):
        old_filename = Path(self.tempdir.name) / f'something old[boring].txt'
        expected_filename = Path(self.tempdir.name) / f'something old[boring and new].txt'
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

    def test_complete_should_remove_priority_and_tag_and_set_done_tag(self):
        old_filename = Path('foo bar [here gone 1-now].quux')
        old_filename.touch()
        expected_filename = Path('foo bar [here gone done].quux')
        task = shibboleth.Task(old_filename.name)

        task.complete()

        self.assertTrue(expected_filename.exists())

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
            shib = shibboleth.Shibboleth()
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
    unittest.main(TestShibbolethTask())
