A cli [TagSpaces][1] client, especially geared towards [The Secret Weapon][2]
approach to Getting Things Done.

# History

A few months into 2017 I read Joan Westenberg's  post about how [she uses
Evernote][3] to keep track of all the things that she needs to do. In the
article she has some pretty golden advice:

> Before I get into it though, I want to be clear. What I do might not work
> for you. There is no golden key to productivity, and this is pretty
> specifically designed to match my workflow and my personality.

Which is, of course, fantastic advice.

While I'm sure Evernote is a fantastic tool with all the bells and whistles
that one could desire, it's not exactly *my* bells and whistles. I have a
slightly different approach that I prefer. I'm much more into the command line,
mainly because it's the easiest way to eliminate distractions. Yeah, you can
turn off distractions in your browser and on your phone - but you actually have
to turn *on* distractions on the command line. So I try to spend most of my
time here.

About a year ago I also came across [TagSpaces][1], which has a philosophy I
love: just stick the information into the filename itself. Then it doesn't
matter what system you're using, the information is going to travel with the
file.

After I read Joan's article, I started trying to use the TagSpaces client. It
worked well enough, though it wasn't quite as keyboard-centric as I wanted.
Using Dropbox to sync my files worked great (though they still don't have a
client for the Raspberry Pi, grumble grumble).

I toyed around with using the command line, `ls *1-now*` or `find . -name
*3-soon*` worked pretty well, but it was still a bit clunky. Out of that need
came Shibboleth

# Guide

Shibboleth is pretty simple. At the moment it only supports Linux-y systems
(there's some weirdness on Mac OSX, with readline), but I'm always open to
[pull requests][4]!

All you have to do is install shibboleth:

    python3 -m pip install shibboleth

Or even better, use [pipx][pipx]:

    pipx install shibboleth


(Come join me in the glorious future that is Python3 ~~.6~~! Or, if you think it's
awesome and you live in some horrible reality that requires something ancient,
did I mention that I'm totally accepting [pull requests][4]?)

Once it's installed, just start it up in whatever directory you want to stick
your stuff. Maybe you do something like this:


    $ mkdir secret-weapon
    $ cd secret-weapon
    $ mkdir completed
    $ shibboleth
    Welcome to Shibboleth, the tool designed to be *your* secret weapon.

    Your editor is currently vim. If you don't like that, you
    should change or set your EDITOR environment variable.

    ⇀shibboleth:/home/wayne/secret-weapon
    >new
    Title: Try out shibboleth

That will launch your editor - whatever your `EDITOR` environment variable is
set to. Or `vim`, if nothing is set. `:q` is how you get out of Vim, if
that's not your thing. I added the text 

> Trying out shibboleth, how does it work for me?

Save and quit and you should come back to shibboleth:

    ⇀shibboleth:/tmp/fnord/Try-out-shibboleth[20170406~011315 inbox].md
    >show
    ********************************************************************************
    Title: Try out shibboleth

    Trying out shibboleth, how does it work for me?

    ********************************************************************************
    ⇀shibboleth:/tmp/fnord/Try-out-shibboleth[20170406~011315 inbox].md
    >

It will automatically select the new file. You may notice that it changed the
spaces for `-`. That's because readline is confusing and hard and doesn't
like autocompleteing spaces. But if you can make it do the right thing, did I
mention I'm accepting [pull requests][4]?

Recently (in January 2022) I was reminded of the "inbox" functionality, so I
added that as the default "priority" that will show up in the report.

Of course, you can change the priority of your selected file/task with
`priority`, or the shortcut `p`.

    >p 6
    ⇀shibboleth:/tmp/fnord/Try-out-shibboleth[20170406~011315 6-waiting].md
    >

You can `deselect` to drop that, or `select` a different file. Or create
another `new` one:

    >new something completely different
    ⇀shibboleth:/tmp/fnord/something-completely-different[20170406~013345 inbox].md
    >show
    ********************************************************************************
    A man with three legs!

    > 'e ran off!

    ********************************************************************************
    ⇀shibboleth:/tmp/fnord/something-completely-different[20170406~013345 inbox].md
    p 4
    ⇀shibboleth:/tmp/fnord/something-completely-different[20170406~013345 4-later].md
    >

You can use `ls` to list all the files in the directory, `cd` to change
directory. Or if you just want to see what you're supposed to be doing now:

    >now
    trying-out-shibboleth[20170406~013326 1-now].md
    ⇀shibboleth:/tmp/fnord/trying-out-shibboleth[20170406~013326 1-now].md
    >later
    something-completely-different[20170406~013345 4-later].md
    ⇀shibboleth:/tmp/fnord/trying-out-shibboleth[20170406~013326 1-now].md
    >

Or if you want a high-level view, use `report`:

    >report
    inbox
    1-now (1/2)
            Trying-out-shibboleth[20220102~210020 1-now].md
    2-next (0/2)
    3-soon (0/2)
    4-later (1/2)
            something-completely-different[20220102~210043 4-later].md
    5-someday (0/2)
    6-waiting (0/2)
    done (0/2)
    None (0/2)

You can use the `work` command to process either a priority or any other label. 

Once you're done with a thing, you can `compelete` it, or be `done` with
it:

    >done
    ⇀shibboleth:/tmp/fnord
    >cd completed
    ⇀shibboleth:/tmp/fnord/completed
    >ls
    something-completely-different[20170406~013345 done].md


That's really about all there is to it. The way I use Shibboleth for my
day-to-day:

- Start up shibboleth.
- `select startup` which contains a bunch of URLs that I need to open.
- `launch` to open up all my startup URLs.
- `work 6` to work my waiting list, to see if there's anything I need to move
  out of waiting.
- Go through `someday`, `later`, `soon`, and `next` to see if anything needs to
  be bumped up.
- Decide which of `now` I need to work on the most, then `s` elect it. I may
  `ed` it to add some notes or just `show` to review what I'm supposed to be
  doing, and probably `launch` the relevant URLs. Then when I finish that I
  mark it `done` and move on to the next.

As new tasks come in via email, etc. I go ahead and add new ones. I've been
using shibboleth as the interface for my tasks for a while now and it works
*great* for shifting the priority, creating new tasks, and editing ones that
I've got.

If you've got any suggestions about what would make shibboleth (more) awesome,
I'm happy to work with you to get your [pull request][4] in. Or if I've got
some time or I think it's a killer feature, I'm sure I'll add it to my own
list. Using shibboleth, of course :)


<a id="philosophy"></a>

Philosophy
----------

I would prefer to keep this as 3rd-party-dependency-free as possible. ~~I'm not
opposed to adding some kind of plugin architecture, but~~ (Plugins were added!)
I *really* want shibboleth to stay one single file. That way you can just stick
it in a directory and you're good to go.


<a id="plugins"></a>

Plugins
-------

I've added a plugin architecture! Currently it requires plugins to be found in
`~/.shibboleth/plugins`. Plugins will be attached to Shibboleth's main loop as
if they were methods, using the filename as the name of the command. For
instance, if you wanted to add a really bad pomodoro timer, you could do that
by creating a `pom.py` in the plugin directory that contained the following:

    import time


    def handle(self, line):
        print('Pomodoro', line)
        time.sleep(60*20)  # sleep for 20 minutes
        print('Pomodoro done!')

If you wanted to make it drop straight into the editor you could add:

        self.edit('')

At the end of the function.


<a id="auto_git_tracking"></a>

Automatic Git Tracking
----------------------

When commands finish, any untracked/committed changes will be automatically
added and committed. This means that when doing `did` or `done`, or tagging
files will automatically be tracked.

Currently git is the only VCS backend that's supported, but it should be pretty
reasonable to extend the behavior to other backends, like mercurial or fossil.


TODOs
-----

- ~~Add BSD license~~ - Done 2018-10-01
- ~~Add other tag support~~ - Done 2018-10-01
- config. We want to be able to config shibboleth, right? Different colors and
  what-not.

<a id="changelog"></a>

CHANGELOG
---------

## [0.9.1] - [Unreleased]

### Fixed

- `pls inbox` now works.

### Changed

- Internal refactor - if Shibboleth is used programatically then replace
  Shibboleth with ShibbolethLoop. Should be completely transparent from a user
  perspective.

## [0.9.0] - [2022-10-29]

### Added

- Added launch and view/show functionality to review.
- Added tag autocomplete to tag/untag functions.

### Fixed

- If review changes a selected task, it'll be deselected.

## [0.8.0] - [2022-01-03]


### Added

- "inbox" as a priority.

### Changed

- "inbox" as the default priority.

### Fixed

- Restored `1-now` as the default work priority.

## [0.7.1] - [2022-01-02]

### Fixed

- Fixed bug when your shibboleth directory was a subfolder in a repo that had
  modified files in a different directory in the repo.

## [0.7.0] - [2022-01-02]

### Added

- [Automatic git tracking](#auto_git_tracking).
- `clear` priority to... well, clear the priority!
- Title is now inserted automatically into the file.

### Changed

- `did` now inserts timestamps with a header instead of relying on the
  blank-space-at-the-end-of-a-line for CommonMark rendering.
- `work` now supports arbitrary tag matching, with autocomplete. Allows for
  working priority labels or other labels.

### Fixed

- Mis-provided `log` command no longer crashes, improved logging.
- No longer pass vim flags to all editors.

---

## [0.6.0] - [2021-06-17]

## Fixed

- Unhandled exceptions are now caught and written to shibboleth.log instead of
  crashing.
- Added `launch` command, which will launch URLs found in headers in the task
  file.

## [0.5.0] - [2019-10-15]

### Added

- `work` subcommand, to allow you to quickly process a particular priority. By
  default, it will work `1-now`, but `work 2` will work the "next" tasks.
- `version` command, to display the current version of shibboleth.

### Changed

- Updated how prompt is generated. Shouldn't cause an issue, but something to
  be aware of, especially in plugins.
- Default priority is now `now` - this helps with tasks falling through the
  cracks.

## [0.4.1] - [2019-10-14]

### Changed

- `cmdloop` passes on `*args` and `**kwargs` - useful for running loops from
  plugins.

## [0.4.0] - [2019-07-31]

### Added

- Review command that lets you cycle through your tasks, updating priorities.

### Changed

- Duplicate tags are no longer allowed, though if added outside Shibboleth they
  will not be interfered with.

## [0.3.0]

### Added

- Plugin system. Add `.py` files to `~/.shibboleth/plugins` to extend the
  functionality of Shibboleth.
- Keep a changelog functionality for the changelog.


[1]: https://www.tagspaces.org/ "TagSpaces"
[2]: http://www.thesecretweapon.org/the-secret-weapon-manifesto/manifesto-part-1-the-issue "The Secret Weapon Manifesto"
[3]: https://web.archive.org/web/20190225071845/https://medium.com/hi-my-name-is/how-i-use-evernote-to-pitch-at-the-top-of-my-game-2c5966ef720b
[4]: https://github.com/waynew/shibboleth#fork-destination-box
[pipx]: https://pypa.github.io/pipx/
