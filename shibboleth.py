import cmd
import glob
import os
import re
import sys


DEFAULT_COLORS = {
    '1-now': 31, #red
    '2-next': 34, #blue
    '3-soon': 92, #light green
    '4-later': 32, #green
    '5-someday': 90, #dark gray
    '6-waiting': 95, # light pink?
}
TAG_PATTERN = r'\[(.*)\]'


class Filename:
    def __init__(self, filename):
        tags_found = re.search(TAG_PATTERN, filename)
        if tags_found:
            self.tags = tags_found.groups()[0].split()
        else:
            self.tags = None
        self.filename = filename

    @property
    def colorized(self):
        filename = self.filename
        for tag in self.tags or []:
            color = DEFAULT_COLORS.get(tag, '32')
            colorized = f'\x1b[{color}m{tag}\x1b[0m'
            filename = filename.replace(tag, colorized)
        return filename


class Shibboleth(cmd.Cmd):
    def __init__(self):
        super().__init__()
        self.prompt = 'shibboleth\n>'

    def do_pls(self, line):
        files = os.listdir(os.path.curdir)

        if not line:
            ordered = {
                '1-now': [],
                '2-next': [],
                '3-soon': [],
                '4-later': [],
                '5-someday': [],
                '6-waiting': [],
            }
            for filename in files:
                filename = Filename(filename)
                if '1-now' in filename.tags:
                    ordered['1-now'].append(filename)
                elif '2-next' in filename.tags:
                    ordered['2-next'].append(filename)
                elif '3-soon' in filename.tags:
                    ordered['3-soon'].append(filename)
                elif '4-later' in filename.tags:
                    ordered['4-later'].append(filename)
                elif '5-someday' in filename.tags:
                    ordered['5-someday'].append(filename)
                elif '6-waiting' in filename.tags:
                    ordered['6-waiting'].append(filename)



    def do_ls(self, line):
        line = os.path.expanduser(line)
        if not line:
            files = os.listdir(os.path.curdir)
        elif os.path.isdir(line):
            files = os.listdir(line)
        else:
            files = glob.glob(line)
        for filename in files:
            print(Filename(filename).colorized)

    def do_exit(self, line):
        print('Goodbye!')
        return True

    def do_EOF(self, line):
        print()
        return self.do_exit(line)


def colorfy(filename):
    tags_found = re.search(tag_pattern, filename)
    tags = None
    if tags_found:
        tags = tags_found.groups()[0].split()
        for tag in tags:
            color = DEFAULT_COLORS.get(tag, '32')
            colorized = f'\x1b[{color}m{tag}\x1b[0m'
            filename = filename.replace(tag, colorized)
    return filename, tags


def run():
    # TODO: REMOVEME -W. Werner, 2017-04-05
    os.chdir(os.path.expanduser('~/notes/secret-weapon'))
    # I'll never ever write a song about the shibby
    shibby = Shibboleth()
    if sys.argv[1:]:
        shibby.onecmd(' '.join(sys.argv[1:]))
    else:
        shibby.cmdloop()

if __name__ == '__main__':
    run()
