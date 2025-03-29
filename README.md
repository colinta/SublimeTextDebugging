Text Debugging
===============

Adds prinf-style debugging.  Select some variables or expressions and a blank line, and this command
will insert language-appropriate debugging statements.  I try to insert dynamic line numbers when
possible (easy in some languages, impossible in others).  It falls back to
static line numbers if the language doesn't have "compile time" line numbers.

Installation
------------

Using Package Control, install "TextDebugging" or clone this repo in your packages folder.

I recommended you add key bindings for the commands. I've included my preferred bindings below.
Copy them to your key bindings file (⌘⇧,).

Commands
--------

`text_debugging`: First, select multiple variables. Then put an empty cursor
somewhere and run this command (recommended: `ctrl+p`).  You'll
get some good debug output that looks like this (Python example):

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
Key Bindings
------------

Copy these to your user key bindings file.

<!-- keybindings start -->
    { "keys": ["ctrl+p"], "command": "text_debugging" },
<!-- keybindings stop -->
