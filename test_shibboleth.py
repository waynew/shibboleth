import os
import shibboleth
import tempfile
import unittest

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

                assert task.title == expected_title, f'{task.title!r} != {expected_title!r}'

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

                assert task.tags == tags, f'{task.tags!r} != {tags!r}'

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

    def test_when_tag_is_added_it_should_rename_the_file(self):
        old_filename = Path(self.tempdir.name) / f'something old[boring].txt'
        expected_filename = Path(self.tempdir.name) / f'something old[boring and new].txt'
        old_filename.touch()
        task = shibboleth.Task(old_filename.name)

        task.tags.append('and')
        task.tags.append('new')

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


if __name__ == '__main__':
    unittest.main(TestShibbolethTask())
