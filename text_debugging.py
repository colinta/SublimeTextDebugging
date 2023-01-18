import os.path
import re
import json
from functools import cmp_to_key

import sublime
import sublime_plugin


def indent_at(view, region):
    line_start = view.line(region).begin()
    line_indent = view.rowcol(region.a)[1]
    return view.substr(sublime.Region(line_start, line_start + line_indent))


class TextDebugging(sublime_plugin.TextCommand):
    def run(self, edit, **kwargs):
        if not len(self.view.sel()):
            return

        location = self.view.sel()[0].begin()
        if self.view.score_selector(location, 'source.python'):
            self.view.run_command('text_debugging_python', kwargs)
        elif self.view.score_selector(location, 'source.ruby.mac') or self.view.score_selector(location, 'source.rubymotion'):
            self.view.run_command('text_debugging_ruby_motion', kwargs)
        elif self.view.score_selector(location, 'source.ruby'):
            self.view.run_command('text_debugging_ruby', kwargs)
        elif self.view.score_selector(location, 'source.objc'):
            self.view.run_command('text_debugging_objc', kwargs)
        elif self.view.score_selector(location, 'source.swift'):
            self.view.run_command('text_debugging_swift', kwargs)
        elif self.view.score_selector(location, 'source.js') or self.view.score_selector(location, 'source.jsx'):
            self.view.run_command('text_debugging_javascript', kwargs)
        elif self.view.score_selector(location, 'source.ts') or self.view.score_selector(location, 'source.tsx'):
            self.view.run_command('text_debugging_javascript', kwargs)
        elif self.view.score_selector(location, 'source.php'):
            self.view.run_command('text_debugging_php', kwargs)
        elif self.view.score_selector(location, 'source.java'):
            self.view.run_command('text_debugging_java', kwargs)
        elif self.view.score_selector(location, 'source.Kotlin'):
            self.view.run_command('text_debugging_kotlin', kwargs)
        elif self.view.score_selector(location, 'source.elixir'):
            self.view.run_command('text_debugging_elixir', kwargs)
        elif self.view.score_selector(location, 'source.elm'):
            self.view.run_command('text_debugging_elm', kwargs)
        elif self.view.score_selector(location, 'source.scala'):
            self.view.run_command('text_debugging_scala', kwargs)
        elif self.view.score_selector(location, 'source.arduino'):
            self.view.run_command('text_debugging_arduino', kwargs)
        elif self.view.score_selector(location, 'source.shell'):
            self.view.run_command('text_debugging_shell', kwargs)
        else:
            sublime.status_message('No support for the current language grammar.')


class TextDebuggingPython(sublime_plugin.TextCommand):
    def run(self, edit, puts="print"):
        error = None
        empty_regions = []
        debug = ''
        debug_vars = []
        regions = list(self.view.sel())
        for region in regions:
            if not region:
                empty_regions.append(region)
            else:
                s = self.view.substr(region)
                if debug:
                    debug += "\n"
                debug += "{s}: {{{count}!r}}".format(s=s, count=1 + len(debug_vars))
                debug_vars.append(s)
                self.view.sel().subtract(region)

        if not empty_regions:
            sublime.status_message('You must place an empty cursor somewhere')
            return

        # any edits that are performed will happen in reverse; this makes it
        # easy to keep region.a and region.b pointing to the correct locations
        def get_end(region):
            return region.end()
        empty_regions.sort(key=get_end, reverse=True)

        if self.view.file_name():
            name = os.path.basename(self.view.file_name())
        elif self.view.name():
            name = self.view.name()
        else:
            name = 'Untitled'

        if debug:
            output = puts + '("""=============== {name} at line {{0}} ==============='.format(name=name)
            output += "\n" + debug + "\n"
            output += '""".format(__import__(\'sys\')._getframe().f_lineno - {lines}, '.format(lines=1 + len(debug_vars))
            for var in debug_vars:
                output += var.strip() + ', '
            output += '))'
        else:
            output = puts + '("=============== {name} at line {{0}} ===============".format(__import__(\'sys\')._getframe().f_lineno))'.format(name=name)

        for empty in empty_regions:
            self.view.insert(edit, empty.a, output)

        if error:
            sublime.status_message(error)


class TextDebuggingRuby(sublime_plugin.TextCommand):
    def run(self, edit, puts="puts"):
        error = None
        empty_regions = []
        debug = ''
        regions = list(self.view.sel())
        for region in regions:
            if not region:
                empty_regions.append(region)
            else:
                s = self.view.substr(region)
                if debug:
                    debug += ',\n'
                if ' ' in s:
                    var = "({0})".format(s)
                else:
                    var = s
                debug += '''  "{s}: #{{{var}.inspect}}"'''.format(s=s.replace('"', r'\"'), var=var)
                self.view.sel().subtract(region)

        # any edits that are performed will happen in reverse; this makes it
        # easy to keep region.a and region.b pointing to the correct locations
        def get_end(region):
            return region.end()
        empty_regions.sort(key=get_end, reverse=True)

        if not empty_regions:
            sublime.status_message('You must place an empty cursor somewhere')
        else:
            if self.view.file_name():
                name = os.path.basename(self.view.file_name())
            elif self.view.name():
                name = self.view.name()
            else:
                name = 'Untitled'

            output = puts + '('
            if debug:
                output += '["=============== {name} line #{{__LINE__}} ===============",'.format(name=name)
                output += '\n  "=============== #{self.class == Class ? self.name + \'##\' : self.class.name + \'#\'}#{__method__} ===============",\n'
                output += debug
                output += ']'
            else:
                output += '"=============== {name} line #{{__LINE__}} ==============="'.format(name=name)
            output += ')'

            for empty in empty_regions:
                indent = indent_at(self.view, empty)
                line_output = output.replace("\n", "\n{0}".format(indent))
                self.view.insert(edit, empty.a, line_output)

        if error:
            sublime.status_message(error)


class TextDebuggingSwift(sublime_plugin.TextCommand):
    def run(self, edit, puts=None):
        error = None
        empty_regions = []
        debug = ''
        debug_vars = []
        regions = list(self.view.sel())
        if not puts and self.view.settings().get('swift.print'):
            puts = self.view.settings().get('swift.print')
        else:
            puts = "print"

        if self.view.settings().get('translate_tabs_to_spaces'):
            tab = ' ' * self.view.settings().get('tab_size')
        else:
            tab = "\t"

        for region in regions:
            if not region:
                empty_regions.append(region)
            else:
                s = self.view.substr(region)
                if ' ' in s:
                    var = "({0})".format(s)
                else:
                    var = s
                debug_vars.append((s, var))
                self.view.sel().subtract(region)

        # any edits that are performed will happen in reverse; this makes it
        # easy to keep region.a and region.b pointing to the correct locations
        def get_end(region):
            return region.end()
        empty_regions.sort(key=get_end, reverse=True)

        if not empty_regions:
            sublime.status_message('You must place an empty cursor somewhere')
        else:
            for (s, var) in debug_vars:
                if debug:
                    debug += "\n"
                debug += puts + "(\"{s}: \({var})\")".format(s=s.replace('"', r'\"'), var=var)

            output = puts + '("=============== \(#file) line \(#line) ===============")'
            if debug:
                output += "\n" + debug

            for empty in empty_regions:
                indent = indent_at(self.view, empty)
                line_output = output.replace("\n", "\n{0}".format(indent))
                self.view.insert(edit, empty.a, line_output)

        if error:
            sublime.status_message(error)



class TextDebuggingElixir(sublime_plugin.TextCommand):
    def run(self, edit, puts="IO.puts"):
        error = None
        empty_regions = []
        debug = ''
        debug_vars = []
        regions = list(self.view.sel())

        if self.view.settings().get('translate_tabs_to_spaces'):
            tab = ' ' * self.view.settings().get('tab_size')
        else:
            tab = "\t"

        for region in regions:
            if not region:
                empty_regions.append(region)
            else:
                s = self.view.substr(region)
                if ' ' in s:
                    var = "({0})".format(s)
                else:
                    var = s
                debug_vars.append((s, var))
                self.view.sel().subtract(region)

        # any edits that are performed will happen in reverse; this makes it
        # easy to keep region.a and region.b pointing to the correct locations
        def get_end(region):
            return region.end()
        empty_regions.sort(key=get_end, reverse=True)

        if not empty_regions:
            sublime.status_message('You must place an empty cursor somewhere')
        else:
            for (s, var) in debug_vars:
                if debug:
                    debug += "\n"
                debug += puts + "(\"{s}: #{{inspect({var})}}\")".format(s=s.replace('"', r'\"'), var=var)

            output = puts + '("=============== #{__ENV__.file} line #{__ENV__.line} ===============")'
            if debug:
                output += "\n" + debug

            for empty in empty_regions:
                indent = indent_at(self.view, empty)
                line_output = output.replace("\n", "\n{0}".format(indent))
                self.view.insert(edit, empty.a, line_output)

        if error:
            sublime.status_message(error)


class TextDebuggingObjc(sublime_plugin.TextCommand):
    def run(self, edit, puts="NSLog"):
        error = None
        empty_regions = []
        debug = ''
        debug_vars = ''
        regions = list(self.view.sel())
        not_empty_regions = 0
        for region in regions:
            if region:
                not_empty_regions += 1

        for region in regions:
            if not region:
                empty_regions.append(region)
            else:
                if not debug_vars:
                    debug_vars = ', __PRETTY_FUNCTION__, __LINE__ - {0}'.format(not_empty_regions)
                s = self.view.substr(region)
                debug += "\\n\\\n"
                debug_vars += ", "
                debug += "{s}: %@".format(s=s.replace('"', r'\"'))
                debug_vars += s
                self.view.sel().subtract(region)
        if not debug_vars:
            debug_vars = ', __PRETTY_FUNCTION__, __LINE__'

        # any edits that are performed will happen in reverse; this makes it
        # easy to keep region.a and region.b pointing to the correct locations
        def get_end(region):
            return region.end()
        empty_regions.sort(key=get_end, reverse=True)

        if not empty_regions:
            sublime.status_message('You must place an empty cursor somewhere')
        else:
            if self.view.file_name():
                name = os.path.basename(self.view.file_name())
            elif self.view.name():
                name = self.view.name()
            else:
                name = 'Untitled'

            output = puts + '(@"=============== {name}:%s at line %i ==============='.format(name=name)
            output += debug
            output += '"'
            output += debug_vars
            output += ");"

            for empty in empty_regions:
                self.view.insert(edit, empty.a, output)

        if error:
            sublime.status_message(error)


class TextDebuggingJavascript(sublime_plugin.TextCommand):
    def run(self, edit, puts="console.log"):
        error = None
        empty_regions = []
        debugs = []
        regions = list(self.view.sel())
        for region in regions:
            if not region:
                empty_regions.append(region)
            else:
                s = self.view.substr(region)
                if re.match(r'^\w+$', s):
                    debugs.append(s)
                else:
                    debugs.append("'{s_escaped}': {s}".format(s=s, s_escaped=s.replace("'", "\\'")))
                self.view.sel().subtract(region)

        # any edits that are performed will happen in reverse; this makes it
        # easy to keep region.a and region.b pointing to the correct locations
        def get_end(region):
            return region.end()
        empty_regions.sort(key=get_end, reverse=True)

        if not empty_regions:
            sublime.status_message('You must place an empty cursor somewhere')
        else:
            if self.view.file_name():
                name = os.path.basename(self.view.file_name())
            elif self.view.name():
                name = self.view.name()
            else:
                name = 'Untitled'

            output = puts + '(\'=============== {name} at line line_no ===============\');\n'.format(name=name)
            if debugs:
                output += puts + "({"
                first = True
                for debug in debugs:
                    if not first:
                        output += ', '
                    first = False
                    output += debug
                output += "});\n"
            output = output[:-1]

            for empty in empty_regions:
                indent = indent_at(self.view, empty)
                line_no = self.view.rowcol(empty.a)[0] + 1
                line_output = output.replace("\n", "\n{0}".format(indent)).replace("line_no", str(line_no))
                self.view.insert(edit, empty.a, line_output)

        if error:
            sublime.status_message(error)


class TextDebuggingPhp(sublime_plugin.TextCommand):
    def run(self, edit):
        error = None
        empty_regions = []
        debugs = ''
        regions = list(self.view.sel())
        for region in regions:
            if not region:
                empty_regions.append(region)
            else:
                s = self.view.substr(region)
                if debugs:
                    debugs += ", "
                debugs += "'{0}' => {1}".format(s.replace('\'', '\\\''), s)
                self.view.sel().subtract(region)

        # any edits that are performed will happen in reverse; this makes it
        # easy to keep region.a and region.b pointing to the correct locations
        def get_end(region):
            return region.end()
        empty_regions.sort(key=get_end, reverse=True)

        if not empty_regions:
            sublime.status_message('You must place an empty cursor somewhere')
        else:
            if self.view.file_name():
                name = os.path.basename(self.view.file_name())
            elif self.view.name():
                name = self.view.name()
            else:
                name = 'Untitled'

            output = '''$__LINE__ = __LINE__;error_log("=============== {name} at line $__LINE__ ===============");'''.format(name=name)
            if debugs:
                output += '''
ob_start();
var_dump(array({debugs}));
array_map('error_log', explode("\\n", ob_get_clean()));
'''[:-1].format(debugs=debugs)

            for empty in empty_regions:
                indent = indent_at(self.view, empty)
                line_output = output.replace("\n", "\n{0}".format(indent))
                self.view.insert(edit, empty.a, line_output)

        if error:
            sublime.status_message(error)


class TextDebuggingRubyMotion(TextDebuggingRuby):
    def run(self, edit, puts="NSLog"):
        return super(TextDebuggingRubyMotion, self).run(edit, puts)


class TextDebuggingJava(sublime_plugin.TextCommand):
    def run(self, edit, puts="System.out.println"):
        error = None
        empty_regions = []
        debugs = []
        regions = list(self.view.sel())
        for region in regions:
            if not region:
                empty_regions.append(region)
            else:
                s = self.view.substr(region)
                debugs += ['"{s_escaped}:", {s}'.format(s=s, s_escaped=s.replace('"', '\\"'))]
                self.view.sel().subtract(region)

        # any edits that are performed will happen in reverse; this makes it
        # easy to keep region.a and region.b pointing to the correct locations
        def get_end(region):
            return region.end()
        empty_regions.sort(key=get_end, reverse=True)

        if not empty_regions:
            sublime.status_message('You must place an empty cursor somewhere')
        else:
            if self.view.file_name():
                name = os.path.basename(self.view.file_name())
            elif self.view.name():
                name = self.view.name()
            else:
                name = 'Untitled'

            output = puts + '("=============== {name} at line line_no ===============");\n'.format(name=name)
            for debug in debugs:
                output += puts + "({debug});\n".format(debug=debug)
            output = output[:-1]

            for empty in empty_regions:
                indent = indent_at(self.view, empty)
                line_no = self.view.rowcol(empty.a)[0] + 1
                line_output = output.replace("\n", "\n{0}".format(indent)).replace("line_no", str(line_no))
                self.view.insert(edit, empty.a, line_output)

        if error:
            sublime.status_message(error)




class TextDebuggingKotlin(sublime_plugin.TextCommand):
    def run(self, edit, puts="println"):
        error = None
        empty_regions = []
        debugs = []
        regions = list(self.view.sel())
        for region in regions:
            if not region:
                empty_regions.append(region)
            else:
                s = self.view.substr(region)
                debugs += ['"{s_escaped}: ${{{s}}}"'.format(s=s, s_escaped=s.replace('"', '\\"'))]
                self.view.sel().subtract(region)

        # any edits that are performed will happen in reverse; this makes it
        # easy to keep region.a and region.b pointing to the correct locations
        def get_end(region):
            return region.end()
        empty_regions.sort(key=get_end, reverse=True)

        if not empty_regions:
            sublime.status_message('You must place an empty cursor somewhere')
        else:
            if self.view.file_name():
                name = os.path.basename(self.view.file_name())
            elif self.view.name():
                name = self.view.name()
            else:
                name = 'Untitled'

            output = puts + '("=============== {name} at line line_no ===============")\n'.format(name=name)
            for debug in debugs:
                output += puts + "({debug})\n".format(debug=debug)
            output = output[:-1]

            for empty in empty_regions:
                indent = indent_at(self.view, empty)
                line_no = self.view.rowcol(empty.a)[0] + 1
                line_output = output.replace("\n", "\n{0}".format(indent)).replace("line_no", str(line_no))
                self.view.insert(edit, empty.a, line_output)

        if error:
            sublime.status_message(error)


class TextDebuggingElm(sublime_plugin.TextCommand):
    def run(self, edit, puts="Debug.log"):
        error = None
        empty_regions = []
        debug = ''
        debug_vars = []
        regions = list(self.view.sel())

        if self.view.settings().get('translate_tabs_to_spaces'):
            tab = ' ' * self.view.settings().get('tab_size')
        else:
            tab = "\t"

        for region in regions:
            if not region:
                empty_regions.append(region)
            else:
                s = self.view.substr(region)
                if ' ' in s:
                    var = "({0})".format(s)
                else:
                    var = s
                debug_vars.append((s, var))
                self.view.sel().subtract(region)

        # any edits that are performed will happen in reverse; this makes it
        # easy to keep region.a and region.b pointing to the correct locations
        def get_end(region):
            return region.end()
        empty_regions.sort(key=get_end, reverse=True)

        if not empty_regions:
            sublime.status_message('You must place an empty cursor somewhere')
        else:
            for (s, var) in debug_vars:
                if debug:
                    debug += "\n"
                debug += "|> " + puts + " \"{s}\"".format(s=s.replace('"', r'\"'))

            if not debug:
                output = '"here"'
            else:
                output = debug

            for empty in empty_regions:
                indent = indent_at(self.view, empty)
                line_output = output.replace("\n", "\n{0}".format(indent))
                self.view.insert(edit, empty.a, line_output)

        if error:
            sublime.status_message(error)


class TextDebuggingScala(sublime_plugin.TextCommand):
    def run(self, edit, puts="println"):
        error = None
        empty_regions = []
        debugs = []
        regions = list(self.view.sel())
        for region in regions:
            if not region:
                empty_regions.append(region)
            else:
                s = self.view.substr(region)
                debugs += ['s"{s_escaped}: ${{{s}}}"'.format(s=s, s_escaped=s.replace('"', '\\"'))]
                self.view.sel().subtract(region)

        # any edits that are performed will happen in reverse; this makes it
        # easy to keep region.a and region.b pointing to the correct locations
        def get_end(region):
            return region.end()
        empty_regions.sort(key=get_end, reverse=True)

        if not empty_regions:
            sublime.status_message('You must place an empty cursor somewhere')
        else:
            if self.view.file_name():
                name = os.path.basename(self.view.file_name())
            elif self.view.name():
                name = self.view.name()
            else:
                name = 'Untitled'

            output = puts + '("=============== {name} at line line_no ===============")\n'.format(name=name)
            for debug in debugs:
                output += puts + "({debug})\n".format(debug=debug)
            output = output[:-1]

            for empty in empty_regions:
                indent = indent_at(self.view, empty)
                line_no = self.view.rowcol(empty.a)[0] + 1
                line_output = output.replace("\n", "\n{0}".format(indent)).replace("line_no", str(line_no))
                self.view.insert(edit, empty.a, line_output)

        if error:
            sublime.status_message(error)


class TextDebuggingArduino(sublime_plugin.TextCommand):
    def run(self, edit, puts="Serial.println", put="Serial.print"):
        error = None
        empty_regions = []
        debugs = []
        regions = list(self.view.sel())
        for region in regions:
            if not region:
                empty_regions.append(region)
            else:
                selection = self.view.substr(region)
                debugs += ['{put}("{s_escaped} = ");'.format(put=put, s_escaped=selection.replace('"', '\\"'))]
                debugs += ['{puts}({selection});'.format(puts=puts, selection=selection)]
                self.view.sel().subtract(region)

        # any edits that are performed will happen in reverse; this makes it
        # easy to keep region.a and region.b pointing to the correct locations
        def get_end(region):
            return region.end()
        empty_regions.sort(key=get_end, reverse=True)

        if not empty_regions:
            sublime.status_message('You must place an empty cursor somewhere')
        else:
            if self.view.file_name():
                name = os.path.basename(self.view.file_name())
            elif self.view.name():
                name = self.view.name()
            else:
                name = 'Untitled'

            output = '{puts}("=========== {name} at line line_no ===========");\n'.format(puts=puts, name=name)
            for debug in debugs:
                output += "{debug}\n".format(debug=debug)
            output = output[:-1]

            for empty in empty_regions:
                indent = indent_at(self.view, empty)
                line_no = self.view.rowcol(empty.a)[0] + 1
                line_output = output.replace("\n", "\n{0}".format(indent)).replace("line_no", str(line_no))
                self.view.insert(edit, empty.a, line_output)

        if error:
            sublime.status_message(error)


class TextDebuggingShell(sublime_plugin.TextCommand):
    def run(self, edit, puts="echo"):
        error = None
        empty_regions = []
        debugs = []
        regions = list(self.view.sel())
        for region in regions:
            if not region:
                empty_regions.append(region)
            else:
                selection = self.view.substr(region)
                selection_var = selection

                if re.match(r'^\w+$', selection_var) and not selection_var.startswith("$"):
                    selection_var = "$" + selection_var
                debugs += ["'{s_escaped}:' {selection_var}".format(selection_var=selection_var, s_escaped=selection.replace('"', '\\"'))]
                self.view.sel().subtract(region)

        # any edits that are performed will happen in reverse; this makes it
        # easy to keep region.a and region.b pointing to the correct locations
        def get_end(region):
            return region.end()
        empty_regions.sort(key=get_end, reverse=True)

        if not empty_regions:
            sublime.status_message('You must place an empty cursor somewhere')
        else:
            if self.view.file_name():
                name = os.path.basename(self.view.file_name())
            elif self.view.name():
                name = self.view.name()
            else:
                name = 'Untitled'

            output = "{puts} '=========== {name} at line line_no ==========='\n".format(puts=puts, name=name)
            for debug in debugs:
                output += "{puts} {debug}\n".format(puts=puts, debug=debug)
            output = output[:-1]

            for empty in empty_regions:
                indent = indent_at(self.view, empty)
                line_no = self.view.rowcol(empty.a)[0] + 1
                line_output = output.replace("\n", "\n{0}".format(indent)).replace("line_no", str(line_no))
                self.view.insert(edit, empty.a, line_output)

        if error:
            sublime.status_message(error)
