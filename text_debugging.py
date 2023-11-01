# import os.path
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

        if self.view.settings().get('translate_tabs_to_spaces'):
            tab = ' ' * self.view.settings().get('tab_size')
        else:
            tab = "\t"
        kwargs['tab'] = tab

        location = self.view.sel()[0].begin()
        selectors = [
            ['arduino', 'text_debugging_arduino'],
            ['elixir', 'text_debugging_elixir'],
            ['elm', 'text_debugging_elm'],
            ['java', 'text_debugging_java'],
            ['js', 'text_debugging_javascript'],
            ['jsx', 'text_debugging_javascript'],
            ['Kotlin', 'text_debugging_kotlin'],
            ['lua', 'text_debugging_lua'],
            ['objc', 'text_debugging_objc'],
            ['php', 'text_debugging_php'],
            ['python', 'text_debugging_python'],
            ['ruby', 'text_debugging_ruby'],
            ['scala', 'text_debugging_scala'],
            ['shell', 'text_debugging_shell'],
            ['swift', 'text_debugging_swift'],
            ['ts', 'text_debugging_javascript'],
            ['tsx', 'text_debugging_javascript'],
        ]

        for lang, command in selectors:
            source = "source.{}".format(lang)
            score = self.view.score_selector(location, source)
            if score:
                config = "{}.print".format(lang)
                if 'puts' not in kwargs and self.view.settings().get(config):
                    kwargs['puts'] = self.view.settings().get(config)

                self.view.run_command(command, kwargs)
                return
        self.view.show_popup('No support for the current language grammar.')


class TextDebuggingPython(sublime_plugin.TextCommand):
    def run(self, edit, tab, puts="print"):
        error = None
        empty_regions = []
        debug = ''
        debug_vars = []
        regions = list(self.view.sel())
        for region in regions:
            if not region:
                empty_regions.append(region)
            else:
                selection = self.view.substr(region)
                if debug:
                    debug += "\n"
                debug += "{selection}: {{{count}!r}}".format(selection=selection, count=1 + len(debug_vars))
                debug_vars.append(selection)
                self.view.sel().subtract(region)

        if not empty_regions:
            self.view.show_popup('You must place an empty cursor somewhere')
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
            output = puts + '("""=========== {name} at line {{0}} ==========='.format(name=name)
            output += "\n" + debug + "\n"
            output += '""".format(__import__(\'sys\')._getframe().f_lineno - {lines}, '.format(lines=1 + len(debug_vars))
            for var in debug_vars:
                output += var.strip() + ', '
            output += '))'
        else:
            output = puts + '("=========== {name} at line {{0}} ===========".format(__import__(\'sys\')._getframe().f_lineno))'.format(name=name)

        for empty in empty_regions:
            self.view.insert(edit, empty.a, output)

        if error:
            self.view.show_popup(error)


class TextDebuggingRuby(sublime_plugin.TextCommand):
    def run(self, edit, tab, puts="puts"):
        error = None
        empty_regions = []
        debug = ''
        regions = list(self.view.sel())
        for region in regions:
            if not region:
                empty_regions.append(region)
            else:
                selection = self.view.substr(region)
                if debug:
                    debug += ',\n'
                if ' ' in selection:
                    var = "({0})".format(selection)
                else:
                    var = selection
                debug += '''  "{selection}: #{{{var}.inspect}}"'''.format(selection=selection.replace('"', r'\"'), var=var)
                self.view.sel().subtract(region)

        # any edits that are performed will happen in reverse; this makes it
        # easy to keep region.a and region.b pointing to the correct locations
        def get_end(region):
            return region.end()
        empty_regions.sort(key=get_end, reverse=True)

        if not empty_regions:
            self.view.show_popup('You must place an empty cursor somewhere')
        else:
            if self.view.file_name():
                name = os.path.basename(self.view.file_name())
            elif self.view.name():
                name = self.view.name()
            else:
                name = 'Untitled'

            output = puts + '('
            if debug:
                output += '["=========== {name} line #{{__LINE__}} ===========",'.format(name=name)
                output += '\n  "=========== #{self.class == Class ? self.name + \'##\' : self.class.name + \'#\'}#{__method__} ===========",\n'
                output += debug
                output += ']'
            else:
                output += '"=========== {name} line #{{__LINE__}} ==========="'.format(name=name)
            output += ')'

            for empty in empty_regions:
                indent = indent_at(self.view, empty)
                line_output = output.replace("\n", "\n{0}".format(indent))
                self.view.insert(edit, empty.a, line_output)

        if error:
            self.view.show_popup(error)


class TextDebuggingSwift(sublime_plugin.TextCommand):
    def run(self, edit, tab, puts="print"):
        error = None
        empty_regions = []
        debug = ''
        debug_vars = []
        regions = list(self.view.sel())

        for region in regions:
            if not region:
                empty_regions.append(region)
            else:
                selection = self.view.substr(region)
                if ' ' in selection:
                    var = "({0})".format(selection)
                else:
                    var = selection
                debug_vars.append((selection, var))
                self.view.sel().subtract(region)

        # any edits that are performed will happen in reverse; this makes it
        # easy to keep region.a and region.b pointing to the correct locations
        def get_end(region):
            return region.end()
        empty_regions.sort(key=get_end, reverse=True)

        if not empty_regions:
            self.view.show_popup('You must place an empty cursor somewhere')
        else:
            for (selection, var) in debug_vars:
                if debug:
                    debug += "\n"
                debug += "{puts}(\"{selection}: \\({var})\")".format(selection=selection.replace('"', r'\"'), var=var)

            output = puts + '("=========== \\(#file) line \\(#line) ===========")'
            if debug:
                output += "\n" + debug

            for empty in empty_regions:
                indent = indent_at(self.view, empty)
                line_output = output.replace("\n", "\n{0}".format(indent))
                self.view.insert(edit, empty.a, line_output)

        if error:
            self.view.show_popup(error)



class TextDebuggingElixir(sublime_plugin.TextCommand):
    def run(self, edit, tab, puts="IO.puts"):
        error = None
        empty_regions = []
        debug = ''
        debug_vars = []
        regions = list(self.view.sel())

        for region in regions:
            if not region:
                empty_regions.append(region)
            else:
                selection = self.view.substr(region)
                if ' ' in selection:
                    var = "({0})".format(selection)
                else:
                    var = selection
                debug_vars.append((selection, var))
                self.view.sel().subtract(region)

        # any edits that are performed will happen in reverse; this makes it
        # easy to keep region.a and region.b pointing to the correct locations
        def get_end(region):
            return region.end()
        empty_regions.sort(key=get_end, reverse=True)

        if not empty_regions:
            self.view.show_popup('You must place an empty cursor somewhere')
        else:
            for (selection, var) in debug_vars:
                if debug:
                    debug += "\n"
                debug += "{puts}(\"{selection}: #{{inspect({var})}}\")".format(selection=selection.replace('"', r'\"'), var=var)

            output = puts + '("=========== #{__ENV__.file} line #{__ENV__.line} ===========")'
            if debug:
                output += "\n" + debug

            for empty in empty_regions:
                indent = indent_at(self.view, empty)
                line_output = output.replace("\n", "\n{0}".format(indent))
                self.view.insert(edit, empty.a, line_output)

        if error:
            self.view.show_popup(error)


class TextDebuggingObjc(sublime_plugin.TextCommand):
    def run(self, edit, tab, puts="NSLog"):
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
                selection = self.view.substr(region)
                debug += "\\n\\\n"
                debug_vars += ", "
                debug += "{selection}: %@".format(selection=selection.replace('"', r'\"'))
                debug_vars += selection
                self.view.sel().subtract(region)
        if not debug_vars:
            debug_vars = ', __PRETTY_FUNCTION__, __LINE__'

        # any edits that are performed will happen in reverse; this makes it
        # easy to keep region.a and region.b pointing to the correct locations
        def get_end(region):
            return region.end()
        empty_regions.sort(key=get_end, reverse=True)

        if not empty_regions:
            self.view.show_popup('You must place an empty cursor somewhere')
        else:
            if self.view.file_name():
                name = os.path.basename(self.view.file_name())
            elif self.view.name():
                name = self.view.name()
            else:
                name = 'Untitled'

            output = puts + '(@"=========== {name}:%selection at line %i ==========='.format(name=name)
            output += debug
            output += '"'
            output += debug_vars
            output += ");"

            for empty in empty_regions:
                self.view.insert(edit, empty.a, output)

        if error:
            self.view.show_popup(error)


class TextDebuggingJavascript(sublime_plugin.TextCommand):
    def run(self, edit, tab, puts="console.log"):
        error = None
        empty_regions = []
        debugs = []
        regions = list(self.view.sel())
        for region in regions:
            if not region:
                empty_regions.append(region)
            else:
                selection = self.view.substr(region)
                if selection == 'this':
                    debugs.append('this: this')
                elif re.match(r'^\w+$', selection):
                    debugs.append(selection)
                else:
                    s_escaped = selection.replace("'", "\\'")
                    debugs.append("'{s_escaped}': {selection}".format(selection=selection, s_escaped=s_escaped))
                self.view.sel().subtract(region)

        # any edits that are performed will happen in reverse; this makes it
        # easy to keep region.a and region.b pointing to the correct locations
        def get_end(region):
            return region.end()
        empty_regions.sort(key=get_end, reverse=True)

        if not empty_regions:
            self.view.show_popup('You must place an empty cursor somewhere')
        else:
            if self.view.file_name():
                name = os.path.basename(self.view.file_name())
            elif self.view.name():
                name = self.view.name()
            else:
                name = 'Untitled'

            output = puts + '(\'=========== {name} at line line_no ===========\');\n'.format(name=name)
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
            self.view.show_popup(error)


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
                selection = self.view.substr(region)
                if debugs:
                    debugs += ", "
                debugs += "'{0}' => {1}".format(selection.replace('\'', '\\\''), selection)
                self.view.sel().subtract(region)

        # any edits that are performed will happen in reverse; this makes it
        # easy to keep region.a and region.b pointing to the correct locations
        def get_end(region):
            return region.end()
        empty_regions.sort(key=get_end, reverse=True)

        if not empty_regions:
            self.view.show_popup('You must place an empty cursor somewhere')
        else:
            if self.view.file_name():
                name = os.path.basename(self.view.file_name())
            elif self.view.name():
                name = self.view.name()
            else:
                name = 'Untitled'

            output = '''$__LINE__ = __LINE__;error_log("=========== {name} at line $__LINE__ ===========");'''.format(name=name)
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
            self.view.show_popup(error)


class TextDebuggingJava(sublime_plugin.TextCommand):
    def run(self, edit, tab, puts="System.out.println"):
        error = None
        empty_regions = []
        debugs = []
        regions = list(self.view.sel())
        for region in regions:
            if not region:
                empty_regions.append(region)
            else:
                selection = self.view.substr(region)
                debugs += ['"{s_escaped}:", {selection}'.format(selection=selection, s_escaped=selection.replace('"', '\\"'))]
                self.view.sel().subtract(region)

        # any edits that are performed will happen in reverse; this makes it
        # easy to keep region.a and region.b pointing to the correct locations
        def get_end(region):
            return region.end()
        empty_regions.sort(key=get_end, reverse=True)

        if not empty_regions:
            self.view.show_popup('You must place an empty cursor somewhere')
        else:
            if self.view.file_name():
                name = os.path.basename(self.view.file_name())
            elif self.view.name():
                name = self.view.name()
            else:
                name = 'Untitled'

            output = puts + '("=========== {name} at line line_no ===========");\n'.format(name=name)
            for debug in debugs:
                output += "{puts}({debug});\n".format(debug=debug)
            output = output[:-1]

            for empty in empty_regions:
                indent = indent_at(self.view, empty)
                line_no = self.view.rowcol(empty.a)[0] + 1
                line_output = output.replace("\n", "\n{0}".format(indent)).replace("line_no", str(line_no))
                self.view.insert(edit, empty.a, line_output)

        if error:
            self.view.show_popup(error)




class TextDebuggingKotlin(sublime_plugin.TextCommand):
    def run(self, edit, tab, puts="println"):
        error = None
        empty_regions = []
        debugs = []
        regions = list(self.view.sel())
        for region in regions:
            if not region:
                empty_regions.append(region)
            else:
                selection = self.view.substr(region)
                debugs += ['"{s_escaped}: ${{{selection}}}"'.format(selection=selection, s_escaped=selection.replace('"', '\\"'))]
                self.view.sel().subtract(region)

        # any edits that are performed will happen in reverse; this makes it
        # easy to keep region.a and region.b pointing to the correct locations
        def get_end(region):
            return region.end()
        empty_regions.sort(key=get_end, reverse=True)

        if not empty_regions:
            self.view.show_popup('You must place an empty cursor somewhere')
        else:
            if self.view.file_name():
                name = os.path.basename(self.view.file_name())
            elif self.view.name():
                name = self.view.name()
            else:
                name = 'Untitled'

            output = puts + '("=========== {name} at line line_no ===========")\n'.format(name=name)
            for debug in debugs:
                output += "{puts}({debug})\n".format(debug=debug)
            output = output[:-1]

            for empty in empty_regions:
                indent = indent_at(self.view, empty)
                line_no = self.view.rowcol(empty.a)[0] + 1
                line_output = output.replace("\n", "\n{0}".format(indent)).replace("line_no", str(line_no))
                self.view.insert(edit, empty.a, line_output)

        if error:
            self.view.show_popup(error)


class TextDebuggingElm(sublime_plugin.TextCommand):
    def run(self, edit, tab, puts="Debug.log"):
        error = None
        empty_regions = []
        debug = ''
        debug_vars = []
        regions = list(self.view.sel())

        for region in regions:
            if not region:
                empty_regions.append(region)
            else:
                selection = self.view.substr(region)
                if ' ' in selection:
                    var = "({0})".format(selection)
                else:
                    var = selection
                debug_vars.append((selection, var))
                self.view.sel().subtract(region)

        # any edits that are performed will happen in reverse; this makes it
        # easy to keep region.a and region.b pointing to the correct locations
        def get_end(region):
            return region.end()
        empty_regions.sort(key=get_end, reverse=True)

        if not empty_regions:
            self.view.show_popup('You must place an empty cursor somewhere')
        else:
            for (selection, var) in debug_vars:
                if debug:
                    debug += "\n"
                debug += "|> " + "{puts} \"{selection}\"".format(selection=selection.replace('"', r'\"'))

            if not debug:
                output = '"here"'
            else:
                output = debug

            for empty in empty_regions:
                indent = indent_at(self.view, empty)
                line_output = output.replace("\n", "\n{0}".format(indent))
                self.view.insert(edit, empty.a, line_output)

        if error:
            self.view.show_popup(error)


class TextDebuggingScala(sublime_plugin.TextCommand):
    def run(self, edit, tab, puts="println"):
        error = None
        empty_regions = []
        debugs = []
        regions = list(self.view.sel())
        for region in regions:
            if not region:
                empty_regions.append(region)
            else:
                selection = self.view.substr(region)
                debugs += ['selection"{s_escaped}: ${{{selection}}}"'.format(selection=selection, s_escaped=selection.replace('"', '\\"'))]
                self.view.sel().subtract(region)

        # any edits that are performed will happen in reverse; this makes it
        # easy to keep region.a and region.b pointing to the correct locations
        def get_end(region):
            return region.end()
        empty_regions.sort(key=get_end, reverse=True)

        if not empty_regions:
            self.view.show_popup('You must place an empty cursor somewhere')
        else:
            if self.view.file_name():
                name = os.path.basename(self.view.file_name())
            elif self.view.name():
                name = self.view.name()
            else:
                name = 'Untitled'

            output = puts + '("=========== {name} at line line_no ===========")\n'.format(name=name)
            for debug in debugs:
                output += "{puts}({debug})\n".format(debug=debug)
            output = output[:-1]

            for empty in empty_regions:
                indent = indent_at(self.view, empty)
                line_no = self.view.rowcol(empty.a)[0] + 1
                line_output = output.replace("\n", "\n{0}".format(indent)).replace("line_no", str(line_no))
                self.view.insert(edit, empty.a, line_output)

        if error:
            self.view.show_popup(error)


class TextDebuggingArduino(sublime_plugin.TextCommand):
    def run(self, edit, tab, puts="Serial.println", put="Serial.print"):
        error = None
        empty_regions = []
        debugs = []
        regions = list(self.view.sel())
        for region in regions:
            if not region:
                empty_regions.append(region)
            else:
                selection = self.view.substr(region)
                debugs += [put + '("{s_escaped} = ");'.format(put=put, s_escaped=selection.replace('"', '\\"'))]
                debugs += [puts + '({selection});'.format(selection=selection)]
                self.view.sel().subtract(region)

        # any edits that are performed will happen in reverse; this makes it
        # easy to keep region.a and region.b pointing to the correct locations
        def get_end(region):
            return region.end()
        empty_regions.sort(key=get_end, reverse=True)

        if not empty_regions:
            self.view.show_popup('You must place an empty cursor somewhere')
        else:
            if self.view.file_name():
                name = os.path.basename(self.view.file_name())
            elif self.view.name():
                name = self.view.name()
            else:
                name = 'Untitled'

            output = puts + '("=========== {name} at line line_no ===========");\n'.format(name=name)
            for debug in debugs:
                output += "{debug}\n".format(debug=debug)
            output = output[:-1]

            for empty in empty_regions:
                indent = indent_at(self.view, empty)
                line_no = self.view.rowcol(empty.a)[0] + 1
                line_output = output.replace("\n", "\n{0}".format(indent)).replace("line_no", str(line_no))
                self.view.insert(edit, empty.a, line_output)

        if error:
            self.view.show_popup(error)


class TextDebuggingShell(sublime_plugin.TextCommand):
    def run(self, edit, tab, puts="echo"):
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
            self.view.show_popup('You must place an empty cursor somewhere')
        else:
            if self.view.file_name():
                name = os.path.basename(self.view.file_name())
            elif self.view.name():
                name = self.view.name()
            else:
                name = 'Untitled'

            output = "{puts} '=========== {name} at line line_no ==========='\n".format(name=name)
            for debug in debugs:
                output += "{puts} {debug}\n".format(debug=debug)
            output = output[:-1]

            for empty in empty_regions:
                indent = indent_at(self.view, empty)
                line_no = self.view.rowcol(empty.a)[0] + 1
                line_output = output.replace("\n", "\n{0}".format(indent)).replace("line_no", str(line_no))
                self.view.insert(edit, empty.a, line_output)

        if error:
            self.view.show_popup(error)


class TextDebuggingLua(sublime_plugin.TextCommand):
    def run(self, edit, tab, puts="print"):
        error = None
        empty_regions = []

        debug = ''
        debug_vars = []
        regions = list(self.view.sel())

        for region in regions:
            if not region:
                empty_regions.append(region)
            else:
                selection = self.view.substr(region)
                if ' ' in selection:
                    var = "({0})".format(selection)
                else:
                    var = selection
                debug_vars.append((selection, var))
                self.view.sel().subtract(region)

        # any edits that are performed will happen in reverse; this makes it
        # easy to keep region.a and region.b pointing to the correct locations
        def get_end(region):
            return region.end()
        empty_regions.sort(key=get_end, reverse=True)

        if not empty_regions:
            self.view.show_popup('You must place an empty cursor somewhere')
        else:
            for (selection, var) in debug_vars:
                if debug:
                    debug += "\n"
                debug += "{puts}(\"{selection}: \\({var})\")".format(selection=selection.replace('"', r'\"'), var=var)

            output = puts + \
                '("=========== ".. debug.getinfo(1).source:sub(2):match("^.*/(.*)$") ..' + \
                '" at line ".. debug.getinfo(1).currentline .." ===========")'
            if debug:
                output += "\n" + debug

            for empty in empty_regions:
                indent = indent_at(self.view, empty)
                line_output = output.replace("\n", "\n{0}".format(indent))
                self.view.insert(edit, empty.a, line_output)

        if error:
            self.view.show_popup(error)
