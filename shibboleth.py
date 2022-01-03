import cmd
import functools
import glob
import itertools
import logging
import os
import pkg_resources
import re
import readline
import subprocess
import sys
import types
import webbrowser

from collections import defaultdict
from datetime import datetime
from pathlib import Path
from textwrap import dedent

logger = logging.getLogger(__name__)

__version__ = '0.7.0'

DEFAULT_COLORS = {
    '1-now': 31,  # red
    '2-next': 34,  # blue
    '3-soon': 92,  # light green
    '4-later': 32,  # green
    '5-someday': 90,  # dark gray
    '6-waiting': 95,  # light pink?
}
PRIORITIES = {
    '1': '1-now',
    '2': '2-next',
    '3': '3-soon',
    '4': '4-later',
    '5': '5-someday',
    '6': '6-waiting',
}

TAG_PATTERN = re.compile(r'(?P<title>.*?)\[(?P<tags>.*?)\](\.(?P<ext>.*))?')
NO_TAG_PATTERN = re.compile(r'(?P<title>[^.]*)(?:\.(?P<ext>.*))?')


def edit(editor, flags, filename):
    if editor.lower() in ('vi', 'vim'):
        flags = "-n " + flags
    else:
        flags = ''
    os.system(f'{editor} {flags} "{filename}"')


def is_git_tracked():
    '''
    Determine if the current directory is tracked via git.
    '''
    logger.debug('>>is_git_tracked')
    DEVNULL = subprocess.DEVNULL
    retcode = subprocess.call(
        ['git', 'rev-parse'], stdout=DEVNULL, stderr=DEVNULL,
    )
    return retcode == 0


def git_postcmd(comment='shibboleth++'):
    '''
    Determine if any changes need to be committed after a command, and do so.
    '''
    logger.debug('>>git_postcmd')
    DEVNULL = subprocess.DEVNULL
    result = subprocess.run(['git', 'status', '--porcelain=v2'], capture_output=True)
    if result.stdout.strip():
        logger.debug('Staging git files')
        result = subprocess.run(['git', 'add', '.'], capture_output=True)
        if result.returncode:
            logger.debug('Oops %r', result)
        logger.debug('Committing git with message %r', comment)
        result = subprocess.run(['git', 'commit', '-m', comment], capture_output=True)
        if result.returncode:
            print('ERROR from git: ', result.stderr)


def load_plugins(plugin_dir='~/.shibboleth/plugins'):
    logger.debug('>>load_plugins')
    plugins = {}
    plugin_dir = os.path.expanduser(plugin_dir)
    if not os.path.exists(plugin_dir):
        logger.info('No plugin dir %r exists', plugin_dir)
        return plugins
    for fname in (f for f in os.listdir(plugin_dir) if f.endswith('.py')):
        plugname = os.path.basename(fname).rsplit('.', maxsplit=1)[0]
        modname = 'shibboleth.ext.' + plugname
        if modname in sys.modules:
            plugins[plugname] = sys.modules[modname]
        else:
            with open(os.path.join(plugin_dir, fname), 'r') as f:
                sourcecode = f.read()
            mod = types.ModuleType(modname)
            mod.__file__ = fname
            code = compile(sourcecode, fname, 'exec')
            exec(code, mod.__dict__)
            plugins[plugname] = sys.modules[modname] = mod
    return plugins


def register_plugin(name):
    def wrapper(func):
        print(id(Shibboleth))

        @functools.wraps(func)
        def f(*args, **kwargs):
            return func(*args, **kwargs)

    return wrapper


class Tags(list):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.listeners = []

    def _broadcast(self):
        for listener in self.listeners:
            listener()

    def append(self, item):
        if item not in self:
            super().append(item)
        self._broadcast()

    def extend(self, items):
        super().extend(i for i in items if i not in self)
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
        self._old_fname = Path(self.filename).expanduser().resolve()

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
        self._old_fname = Path(self.filename).expanduser().resolve()

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
        ext = '.' + self.ext if self.ext else ''
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
        # TODO: Could we do a better job at renaming here? -W. Werner, 2019-10-15
        # There's the _rename function, but it seems like it's
        # a bit different than what we're doing here. I bet we
        # could properly unify this thing.
        self._old_fname = new_path

    def read(self):
        return self._old_fname.read_text()


def tasks_by_priority():
    files = [file for file in Path().iterdir() if file.is_file()]
    priorities = tuple(PRIORITIES.values()) + ('done', None)
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
    for priority in priorities:
        yield priority, by_priority[priority]


class Reviewer(cmd.Cmd):
    def __init__(self, editor):
        super().__init__()
        self.editor = editor
        self.tasks = tuple(tasks_by_priority())
        self.priorities = reversed(list(t[0] for t in self.tasks if t[1]))
        self.tasks = dict(self.tasks)
        self._priority_iter = iter(self.priorities)
        self._cur_priority = next(self._priority_iter)
        self._index = 0

    def next(self):
        if self._index+1 < len(self.tasks[self._cur_priority]):
            self._index += 1
        else:
            self._index = 0
            try:
                self._cur_priority = next(self._priority_iter)
            except StopIteration:
                return True

    @property
    def _cur(self):
        return self.tasks[self._cur_priority][self._index]

    @property
    def prompt(self):
        color = DEFAULT_COLORS.get(self._cur_priority, '32')
        colorized = f'\x1b[{color}m{self._cur_priority}\x1b[0m'
        return f'''\
{self._cur.colorized_filename}
Review ({self._index+1}/{len(self.tasks[self._cur_priority])}) {colorized} [?/1-6/d/e/s/n/q]> '''

    def do_help(self, line):
        '''
        Display help.
        '''
        print('''
Review Commands
===============
?   help
e   edit/view task
1-6 set task priority
s   skip/do not modify task
d   mark task as done
n   next priority
q   quit review
''')

    def do_e(self, line):
        '''
        Edit the task.
        '''
        edit(self.editor, '', self._cur.filename)

    def do_1(self, line):
        self._cur.priority = PRIORITIES['1']
        return self.next()

    def do_2(self, line):
        self._cur.priority = PRIORITIES['2']
        return self.next()

    def do_3(self, line):
        self._cur.priority = PRIORITIES['3']
        return self.next()

    def do_4(self, line):
        self._cur.priority = PRIORITIES['4']
        return self.next()

    def do_5(self, line):
        self._cur.priority = PRIORITIES['5']
        return self.next()

    def do_6(self, line):
        self._cur.priority = PRIORITIES['6']
        return self.next()

    def do_s(self, line):
        '''
        Skip/do not change/update task.
        '''
        return self.next()

    def do_d(self, line):
        '''
        Mark task as completed.
        '''
        self._cur.complete()
        return self.next()

    def do_n(self, line):
        '''
        Next priority.
        '''
        self._index = len(self.tasks[self._cur_priority])
        return self.next()

    def do_q(self, line):
        '''
        Quit review.
        '''
        print('Quitting review')
        return True


class Shibboleth(cmd.Cmd):
    plugins = load_plugins()

    def __init__(self):
        # Register plugins before calling super's init
        for plugin in self.plugins:
            setattr(
                Shibboleth,
                'do_' + plugin,
                types.MethodType(self.plugins[plugin].handle, self),
            )
        super().__init__()
        self.is_git_tracked = is_git_tracked()
        self.selected = None
        readline.set_completion_display_matches_hook(self.display_completion)
        readline.set_completer_delims(readline.get_completer_delims().replace('-', ''))
        self.editor = os.environ.get('EDITOR', 'vim')
        self.intro = dedent(
            f'''
        Welcome to Shibboleth {__version__}, the tool designed to be *your*
        secret weapon.

        Your editor is currently {self.editor}. If you don't like that, you
        should change or set your EDITOR environment variable.
        ''')

    @property
    def prompt(self):
        if self.selected:
            return f'\N{RIGHTWARDS HARPOON WITH BARB UPWARDS}\x1b[34mshibboleth\x1b[0m:{self.selected.colorized_filename}\n>'
        return f'\N{RIGHTWARDS HARPOON WITH BARB UPWARDS}\x1b[34mshibboleth\x1b[0m:{os.getcwd()}\n>'

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
        # else:
        res = super().complete(*args, **kwargs)
        logger.debug('Result: %r', res)
        return res

    def cmdloop(self, *args, **kwargs):
        logger.debug('>>cmdloop')
        while True:
            try:
                super().cmdloop(*args, **kwargs)
                break
            except KeyboardInterrupt:
                print()
                print('^C caught - use `q` to quit')

    def postcmd(self, stop, line):
        logger.debug('>>postcmd')
        if self.is_git_tracked:
            git_postcmd('shibboleth ' + line.partition(' ')[0])
        return stop

    def default(self, line):
        plugname, _, newline = line.partition(' ')
        newline = newline.strip()
        try:
            self.plugins[plugname].handle(newline)
        except (AttributeError, KeyError):
            super().default(line)

    def do_cd(self, line):
        '''
        Change to a new directory

        e.g. > cd /tmp/
        '''
        logger.debug('>>do_cd')
        try:
            os.chdir(line)
            self.is_git_tracked = is_git_tracked()
        except Exception as e:
            print(e)

    def complete_cd(self, text, line, begidx, endidx):
        logger.debug('>>complete_cd')
        paths = glob.glob(text + '*')
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

    def do_work(self, line):
        '''
        Work tasks of a given priority or tag, default of 1-now. Also supports
        multiple tags - if multiple tags are requested they all must be
        present. For instance, 'work 6-waiting email security' would work all
        the tasks that have 6-waiting, email, and security.
        '''
        tags = set(PRIORITIES.get(tag or '1', tag) for tag in line.split())
        all_tasks = (Task(name) for name in os.listdir(os.path.curdir))
        tasks_to_work = [task for task in all_tasks if tags.issubset(set(task.tags))]
        if not tasks_to_work:
            print(f"No tasks for tag {tag!r}")
        else:
            worker = Worker(tasks_to_work)
            worker.cmdloop()
            return worker.result


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
            print('No task provided.')
        else:
            if not os.path.isfile(line):
                print(f'Unknown file {line!r}')
            else:
                self.selected = Task(os.path.abspath(line))

    def complete_select(self, text, line, begidx, endidx):
        logger.debug('>>complete_select')
        paths = glob.glob(text + '*')
        logger.debug('Possible paths: %r', paths)
        return paths

    def complete_edit(self, text, line, begidx, endidx):
        logger.debug('>>complete_edit')
        return complete_select

    def complete_work(self, text, line, begidx, endidx):
        tag_names = set(itertools.chain(*[Task(name).tags for name in os.listdir(os.path.curdir)]))
        return sorted(name for name in tag_names if name.startswith(text))

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
                if line == 'clear':
                    self.selected.priority = None
                else:
                    print(f'Unknown priority {line!r}')

    def do_review(self, line):
        '''
        Review and quickly update the priority of your tasks.
        '''
        r = Reviewer(self.editor)
        r.cmdloop()

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
            print('*' * 80)
            with open(filename) as f:
                print(self.selected.read())
            print('*' * 80)

    def do_edit(self, line, flags=''):
        '''
        Open the current task in the configured editor.
        '''
        logger.debug('>>do_edit')
        if not (self.selected or line):
            print('Select a file and try again')
        else:
            filename = self.selected.filename if self.selected else line

        edit(self.editor, flags, filename)

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

    def do_new(self, line, content=''):
        '''
        Create a new task with the provided title, or ask for one, and
        set it as the active task.
        '''
        logger.debug('>>do_new')
        if line:
            title = line.strip()
        else:
            title = input('Title: ').strip()
        filename = f'{title.replace(" ", "-")}[{datetime.now():%Y%m%d~%H%M%S}].md'
        content = content or f'Title: {title}\n\n'
        Path(filename).write_text(content)
        self.selected = None
        self.do_edit(filename, flags="+'normal Go'")
        self.do_select(filename)
        self.do_priority('1')

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
                header = f'\n\n{datetime.now():%Y-%m-%d %H:%M:%S}\n{"-"*19}\n'
                print(header, file=f)
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
        action, _, level = line.partition(' ')
        level = level.strip()
        if action == 'off':
            logger.info('Turning logging off')
            for handler in logger.handlers[:]:
                handler.flush()
                handler.close()
                logger.removeHandler(handler)
        elif action == 'on':
            level = getattr(logging, level.upper() or 'DEBUG')
            logger.handlers.clear()
            h = logging.FileHandler('shibboleth.log')
            h.setLevel(level)
            logger.setLevel(level)
            logger.addHandler(h)
            logger.info('Logging turned on, level - %r', logging.getLevelName(level))
        if logger.handlers:
            print('Logging is ON - writing to shibboleth.log')
        else:
            print('Logging is OFF')

    def do_launch(self, line):
        """
        Look for URL headers in the current (or specified) task and open them in
        the web browser. If only one URL header is found, it will be launched
        automatically. Otherwise, you will be able to select any of them.
        """
        last = None
        headers = defaultdict(list)
        filename = self.selected.filename if self.selected else line
        with open(filename) as f:
            for line in f:
                if last == line == '\n':
                    break
                else:
                    key, _, val = line.strip().partition(':')
                    if val:
                        headers[key].append(val)
        urls = headers.get('URL')
        if not urls:
            print('No URL headers found')
        else:
            urlcount = len(urls)
            choices = [0]
            if urlcount > 1:
                for i, url in enumerate(urls, start=1):
                    print(f"{i}. {url}")
                done = False
                while not done:
                    choices = input(f'Select urls [1-{i}, empty launches all. Select many by spaces]: ').strip()
                    if not choices:
                        choices = list(range(urlcount))
                        done = True
                    else:
                        try:
                            choices = [int(c)-1 for c in choices.split()]
                            done = True
                        except ValueError:
                            logger.exception('Non-number in choices')
                            print('Non-number found')
            for choice in choices:
                webbrowser.open(urls[choice])

    def do_version(self, line):
        '''
        Display shibboleth version.
        '''
        print(__version__)

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


class Worker(Shibboleth):
    def __init__(self, tasks_to_work):
        super().__init__()
        self.tasks = tasks_to_work
        self.intro = dedent(f'''
        {len(tasks_to_work)} tasks to work.
        ''')
        self.index = -1
        self.do_next('')
        self.result = None
        self.postcmd(None, '')

    @property
    def prompt(self):
        return f'\N{RIGHTWARDS HARPOON WITH BARB UPWARDS}\x1b[34mshibboleth\x1b[0m:{self.selected.colorized_filename}\n{self.index+1}/{len(self.tasks)}>'

    def do_ls(self, line):
        '''
        List the tasks, indicating the current one.
        '''

        for i, task in enumerate(self.tasks):
            arrow = '\N{RIGHTWARDS HARPOON WITH BARB UPWARDS} ' if i == self.index else ''
            print(f"{arrow}{task.colorized_filename}")

    def do_next(self, line):
        '''
        Go to the next task to work. If all tasks have been
        worked, go back to the main shibboleth prompt.
        '''
        self.index += 1
        if self.index >= len(self.tasks):
            print('All done! Good job!')
            return True
        else:
            self.selected = self.tasks[self.index]

    def do_prev(self, line):
        '''
        Go to the previous task to work.
        '''
        self.index = max(self.index-1, 0)
        self.selected = self.tasks[self.index]

    def do_done(self, line):
        super().do_done(line)
        return self.do_next(line)

    def do_priority(self, line):
        super().do_priority(line)
        return self.do_next(line)

    def do_stop(self, line):
        '''
        Stop working this task list and return to Shibboleth.
        '''
        return True


    do_deselect = do_next
    do_skip = do_next
    do_p = do_priority
    do_q = do_quit = do_stop


def run():
    # I'll never ever write a song about the shibby
    shibby = Shibboleth()
    if sys.argv[1:]:
        shibby.onecmd(' '.join(sys.argv[1:]))
    else:
        try:
            shibby.cmdloop()
        except:
            h = logging.FileHandler(
                'shibboleth.log'
            )
            h.setLevel(logging.DEBUG)
            logger.setLevel(logging.DEBUG)
            logger.addHandler(h)
            logger.exception("Unhandled exception")
            logger.critical("Unable to recover, shutting down")
            print("Oh no! Shibboleth had a problem and had to close. Log written to shibboleth.log")
            exit(99)


if __name__ == '__main__':
    run()
