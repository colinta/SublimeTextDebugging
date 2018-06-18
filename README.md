Text Debugging
===============

Adds prinf-style debugging.  Select some variables or expressions and a blank line, and this command
will insert language-appropriate debugging statements.  I try to insert dynamic line numbers when
possible (easy in some languages, impossible in others).  It falls back to
static line numbers if the language doesn't have "compile time" line numbers.

Installation
------------

1. Using Package Control, install "TextDebugging"

Or:

1. Open the Sublime Text 3 Packages folder

    - OS X: ~/Library/Application Support/Sublime Text 3/Packages/
    - Windows: %APPDATA%/Sublime Text 3/Packages/
    - Linux: ~/.Sublime Text 3/Packages/

2. clone this repo
3. Install keymaps for the commands (see Example.sublime-keymap for my preferred keys)

Commands
--------

`text_debugging`: Select multiple variables, then put an empty cursor somewhere
and run this command (default: `ctrl+p` twice or `ctrl+p,p`).  You'll get some
good debug output that looks like this (Python example):

```python
print("""=============== Untitled at line {0} ===============
looks: {1!r}
like: {2!r}
this: {3!r}
""".format(__import__('sys')._getframe().f_lineno - 2, looks, like, this, ))
```

This package supports many languages, here's a ruby example:

```ruby
puts("=============== at line 49 ===============
looks: #{looks.inspect}
like: #{like.inspect}
this: #{this.inspect}")
```
