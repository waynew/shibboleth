import cmd
import glob
import logging
import os
import re
import readline
import sys
import pkg_resources

from datetime import datetime
from textwrap import dedent
from pathlib import Path

logger = logging.getLogger(__name__)

__version__ = '0.2.0'

DEFAULT_COLORS = {
    '1-now': 31, #red
    '2-next': 34, #blue
    '3-soon': 92, #light green
    '4-later': 32, #green
    '5-someday': 90, #dark gray
    '6-waiting': 95, # light pink?
}
PRIORITIES = {
    '1':'1-now',
    '2':'2-next',
    '3':'3-soon',
    '4':'4-later',
    '5':'5-someday',
    '6':'6-waiting',
}

TAG_PATTERN = re.compile(r'(?P<title>.*?)\[(?P<tags>.*?)\](\.(?P<ext>.*))?')
NO_TAG_PATTERN = re.compile(r'(?P<title>[^.]*)(?:\.(?P<ext>.*))?')


class Tags(list):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.listeners = []

    def _broadcast(self):
        for listener in self.listeners:
            listener()

    def append(self, item):
        super().append(item)
        self._broadcast()

    def extend(self, items):
        super().extend(items)
        self._broadcast()

    def sort(self):
        super().sort()
        self._broadcast()

    def remove(self, value):
        super().remove(value)
        self._broadcast()


class Task:
    def __init__(self, filename):
        m = re.search(TAG_PATTERN, filename)
        if m is None:
            self._missing_tags = True
            self.tags = Tags()
            m = re.search(NO_TAG_PATTERN, filename)
        else:
            self._missing_tags = False
            self.tags = Tags(m.group('tags').split())
        self._title = m.group('title')
        self.ext = m.group('ext')

        self.tags.listeners.append(self._on_tag_update)
        self._old_fname = Path(self.filename)

        if '1-now' in self.tags:
            self._priority = '1-now'
        elif '2-next' in self.tags:
            self._priority = '2-next'
        elif '3-soon' in self.tags:
            self._priority = '3-soon'
        elif '4-later' in self.tags:
            self._priority = '4-later'
        elif '5-someday' in self.tags:
            self._priority = '5-someday'
        elif '6-waiting' in self.tags:
            self._priority = '6-waiting'
        else:
            self._priority = None

    def _rename(self):
        self._old_fname.rename(self.filename)
        self._old_fname = Path(self.filename)

    def _on_tag_update(self):
        self._rename()

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, new_title):
        self._title = new_title
        self._rename()

    @property
    def priority(self):
        return self._priority

    @priority.setter
    def priority(self, value):
        if self._priority is not None:
            self.tags.remove(self._priority)

        if value is not None:
            self.tags.append(value)

        self._priority = value

    @property
    def filename(self):
        if self._missing_tags and not self.tags:
            tags = ''
        else:
            tags = f"[{' '.join(self.tags)}]"
        ext = '.'+self.ext if self.ext else ''
        return f'{self._title}{tags}{ext}'

    @property
    def colorized_filename(self):
        filename = self.filename
        for tag in self.tags or []:
            color = DEFAULT_COLORS.get(tag, '32')
            colorized = f'\x1b[{color}m{tag}\x1b[0m'
            filename = filename.replace(tag, colorized)
        return filename

    def complete(self):
        completed_dir = Path('completed').absolute()
        completed_dir.mkdir(parents=True, exist_ok=True)
        self.priority = None
        self.tags.append('done')
        new_path = completed_dir / Path(self.filename).name
        Path(self.filename).rename(new_path)

    def read(self):
        return self._old_fname.read_text()


class Shibboleth(cmd.Cmd):
    def __init__(self):
        super().__init__()
        self.prompt = f'\N{RIGHTWARDS HARPOON WITH BARB UPWARDS}\x1b[34mshibboleth\x1b[0m:{os.getcwd()}\n>'
        self.selected = None
        readline.set_completion_display_matches_hook(self.display_completion)
        readline.set_completer_delims(
            readline.get_completer_delims().replace('-', '')
        )
        self.editor = os.environ.get('EDITOR', 'vim')
        self.intro = dedent(f'''
        Welcome to Shibboleth {__version__}, the tool designed to be *your*
        secret weapon.

        Your editor is currently {self.editor}. If you don't like that, you
        should change or set your EDITOR environment variable.
        ''')

    def display_completion(self, substitution, matches, longest_match_length):
        logger.debug('>>display_completion')
        print()
        print('  '.join(matches))
        print(self.prompt, end='')
        print(readline.get_line_buffer(), end='')
        sys.stdout.flush()

    def complete(self, *args, **kwargs):
        logger.debug('>>complete')
        logger.debug('%r %r', args, kwargs)
        cmd = readline.get_line_buffer().split(None, maxsplit=1)[0]
        if cmd in ('sel', 'select', 'e', 'edit'):
            pass
        #else:
        res = super().complete(*args, **kwargs)
        logger.debug('Result: %r', res)
        return res

    def cmdloop(self):
        logger.debug('>>cmdloop')
        while True:
            try:
                super().cmdloop()
                break
            except KeyboardInterrupt:
                print()
                print('^C caught - use `q` to quit')

    def postcmd(self, stop, line):
        logger.debug('>>postcmd')
        self.prompt = f'\N{RIGHTWARDS HARPOON WITH BARB UPWARDS}\x1b[34mshibboleth\x1b[0m:{os.getcwd()}\n>'
        if self.selected:
            self.prompt = f'\N{RIGHTWARDS HARPOON WITH BARB UPWARDS}\x1b[34mshibboleth\x1b[0m:{self.selected.colorized_filename}\n>'
        return stop

    def do_cd(self, line):
        '''
        Change to a new directory

        e.g. > cd /tmp/
        '''
        logger.debug('>>do_cd')
        try:
            os.chdir(line)
        except Exception as e:
            print(e)

    def complete_cd(self, text, line, begidx, endidx):
        logger.debug('>>complete_cd')
        paths = glob.glob(text+'*')
        return paths

    def do_pls(self, line):
        '''
        Priority list - list files in the folder that have the
        specified priority.
        '''
        logger.debug('>>do_pls')
        files = [Task(name) for name in os.listdir(os.path.curdir)]
        targets = {
            '1': '1-now',
            '2': '2-next',
            '3': '3-soon',
            '4': '4-later',
            '5': '5-someday',
            '6': '6-waiting',
        }
        if line:
            try:
                target = targets[line]
            except KeyError:
                print(f'Unknown priority {line!r}')
                target = None

        for file_ in files:
            if not line or line == '1':
                if '1-now' in file_.tags:
                    print(file_.colorized_filename)
            elif target:
                if target in file_.tags:
                    print(file_.colorized_filename)

    def do_now(self, line):
        '''
        Show tasks with a priority of 1-now
        '''
        logger.debug('>>do_now')
        self.do_pls(line='1')

    def do_next(self, line):
        '''
        Show tasks with a priority of 2-next
        '''
        logger.debug('>>do_next')
        self.do_pls(line='2')

    def do_soon(self, line):
        '''
        Show tasks with a priority of 3-soon
        '''
        logger.debug('>>do_soon')
        self.do_pls(line='3')

    def do_later(self, line):
        '''
        Show tasks with a priority of 4-later
        '''
        logger.debug('>>do_later')
        self.do_pls(line='4')

    def do_someday(self, line):
        '''
        Show tasks with a priority of 5-someday
        '''
        logger.debug('>>do_someday')
        self.do_pls(line='5')

    def do_waiting(self, line):
        '''
        Show tasks with a priority of 6-waiting
        '''
        logger.debug('>>do_waiting')
        self.do_pls(line='6')

    def do_deselect(self, line):
        '''
        De-select the active task
        '''
        logger.debug('>>do_deselect')
        self.selected = None

    def do_select(self, line):
        '''
        Select the provided task.
        '''
        logger.debug('>>do_select')
        if not line:
            self.do_deselect()
        else:
            if not os.path.isfile(line):
                print(f'Unknown file {line!r}')
            else:
                self.selected = Task(os.path.abspath(line))

    def complete_select(self, text, line, begidx, endidx):
        logger.debug('>>complete_select')
        paths = glob.glob(text+'*')
        logger.debug('Possible paths: %r', paths)
        return paths

    def complete_edit(self, text, line, begidx, endidx):
        logger.debug('>>complete_edit')
        return complete_select

    def do_priority(self, line):
        '''
        Set the priority of the active task
        '''
        logger.debug('>>do_priority')
        if not self.selected:
            print('Select a file first and try again')
        else:
            try:
                self.selected.priority = PRIORITIES[line]
            except KeyError:
                print(f'Unknown priority {line!r}')

    def do_report(self, line):
        '''
        Show a breakdown of tasks by priority.
        '''
        files = [file for file in Path(line).iterdir() if file.is_file()]
        by_priority = {
            None: [],
            'done': [],
            '1-now': [],
            '2-next': [],
            '3-soon': [],
            '4-later': [],
            '5-someday': [],
            '6-waiting': [],
        }
        for file in files:
            task = Task(file.name)
            if 'done' in task.tags:
                by_priority['done'].append(task)
            else:
                by_priority[task.priority].append(task)

        for priority in list(PRIORITIES.values()) + ['done', None]:
            these_ones = by_priority[priority]
            print(priority, f'({len(these_ones)}/{len(files)})')
            for task in these_ones:
                print(f'\t{task.colorized_filename}')

    def do_ls(self, line):
        '''
        Show tasks/files in the current (or provided) directory.
        '''
        logger.debug('>>do_ls')
        line = os.path.expanduser(line)
        if not line:
            files = os.listdir(os.path.curdir)
        elif os.path.isdir(line):
            files = os.listdir(line)
        else:
            files = glob.glob(line)
        for filename in files:
            print(Task(filename).colorized_filename)

    def do_show(self, line):
        '''
        Show the body of the current task.
        '''
        logger.debug('>>do_show')
        if not self.selected or line:
            print('Select a file and try again')
        else:
            filename = self.selected.filename if self.selected else line
            print('*'*80)
            with open(filename) as f:
                print(self.selected.read())
            print('*'*80)

    def do_edit(self, line, flags=''):
        '''
        Open the current task in the configured editor.
        '''
        logger.debug('>>do_edit')
        if not (self.selected or line):
            print('Select a file and try again')
        else:
            filename = self.selected.filename if self.selected else line

        if self.editor in ('vi', 'vim'):
            flags = "-n " + flags
        os.system(f'{self.editor} {flags} "{filename}"')

    def do_complete(self, line):
        '''
        Mark the current task as complete.

        Changes the priority to "done" and moves it to the "completed" folder.
        '''
        logger.debug('>>do_complete')
        if not self.selected or line:
            print('Select a file and try again')
        else:
            task = self.selected if self.selected else Task(line)
            task.complete()
        self.selected = None

    def do_new(self, line):
        '''
        Create a new task with the provided title, or ask for one, and
        set it as the active task.
        '''
        logger.debug('>>do_new')
        if line:
            title = line.replace(' ', '-')
        else:
            title = input('Title: ').strip().replace(' ', '-')
        filename = f'{title}[{datetime.now():%Y%m%d~%H%M%S}].md'
        self.selected = None
        self.do_edit(filename)
        self.do_select(filename)

    def do_did(self, line):
        '''
        Add date/time entry to the end of your file

        See https://theptrk.com/2018/07/11/did-txt-file/ for more info.
        '''
        logger.debug('>>do_did')
        if not self.selected or line:
            print('Select a file and try again')
        else:
            task = self.selected if self.selected else Task(line)
            with open(task.filename, 'a') as f:
                print(f'\n{datetime.now():%Y-%m-%d %H:%M:%S %Z}', file=f)
            self.do_edit(task.filename, flags="+'normal Go' -c 'startinsert'")

    def do_tag(self, line):
        '''
        Add the space-delimited tag(s) to the current task.
        '''
        if not self.selected:
            print('Select a file and try again')
            return
        else:
            tags = line.split()
        self.selected.tags.extend(tags)

    def do_untag(self, line):
        '''
        Remove the space-delimited tag(s) from the current task.
        '''
        if not self.selected:
            print('Select a file and try again')
            return
        else:
            tags = line.split()
        for tag in tags:
            try:
                self.selected.tags.remove(tag)
            except ValueError:
                logger.debug(f'Tag {tag} not in {self.selected.tags}')

    def do_exit(self, line):
        '''
        Quit
        '''
        logger.debug('>>do_exit')
        print('Goodbye!')
        return True

    def do_EOF(self, line):
        '''
        Quit
        '''
        logger.debug('>>do_EOF')
        print()
        return self.do_exit(line)

    def do__debug(self, line):
        '''
        Enter the python debugger.
        '''
        logger.debug('>>do__debug')
        breakpoint()

    def do_log(self, line):
        '''
        log on <level> -> start writing debug logs to 'shibboleth.log'
        log off -> stop logging
        '''
        logger.debug('>>do_log')
        action, *rest = line.split(None, maxsplit=1)
        if action == 'off':
            logger.info('Turning logging off')
            logger.handlers.clear()
        elif action == 'on':
            level = getattr(logging, ''.join(rest).upper() or 'DEBUG')
            logger.handlers.clear()
            h = logging.FileHandler(
                'shibboleth.log'
            )
            h.setLevel(level)
            logger.setLevel(level)
            logger.addHandler(h)
            logger.info('Logging turned on, level - %r', level)

    # Aliases
    do_p = do_priority
    do_e = do_edit
    do_sel = do_select
    do_quit = do_exit
    do_q = do_exit
    do_done = do_complete
    do_stop = do_deselect
    complete_sel = complete_select
    complete_e = complete_edit


def run():
    # I'll never ever write a song about the shibby
    shibby = Shibboleth()
    if sys.argv[1:]:
        shibby.onecmd(' '.join(sys.argv[1:]))
    else:
        shibby.cmdloop()

if __name__ == '__main__':
    run()
