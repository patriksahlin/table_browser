'''Table browser is a curses based data table browser.'''
import argparse
import curses
import sys
import pandas as pd

class Selection():
    '''Keeps track of current selection and current range.'''

    def __init__(self, length, height):
        self.length = length
        self.height = height
        self.start = 0
        self.end = min(self.length, self.height)
        self.selection = self.start

    def move_up(self):
        '''Move selection up (decrease count).'''
        self.selection = max(self.selection - 1, 0)
        if self.selection < self.start:
            self.start = max(self.start - self.height, 0)
            self.end = min(self.start + self.height, self.length)

    def move_down(self):
        '''Move selection down (increase count).'''
        self.selection = min(self.selection + 1, self.length - 1)

        if self.selection < self.end:
            pass
        else:
            self.start = self.selection
            self.end = min(self.length, self.start + self.height)

    def move_page_up(self):
        '''Move selection to start of range, or if at start, move range up.'''
        if self.selection > self.start:
            self.selection = self.start
        else:
            self.start = max(self.start - self.height, 0)
            self.end = min(self.start + self.height, self.length)
            self.selection = self.start

    def move_page_down(self):
        '''Move selection down to end of range, or if at end, move range down.'''
        if self.selection < (self.end - 1):
            self.selection = self.end - 1
        else:
            if self.end < self.length:
                self.start = self.end
                self.end = min(self.start + self.height, self.length)
                self.selection = self.end - 1

    def get_range(self):
        '''Get current range.'''
        return range(self.start, self.end)

class RecordBrowser():
    '''Browser that displays data fields per one record at the time.'''
    def __init__(self, stdscr, df, buffer_name):
        self.stdscr = stdscr
        self.df = df # pylint: disable=C0103
        self.buffer_name = buffer_name
        self.set_dimensions()
        self.header_window = curses.newwin(1, curses.COLS, 0, 0)
        self.footer_window = curses.newwin(1, curses.COLS, curses.LINES - 1, 0)
        self.left_window = curses.newwin(self.height, self.left_window_width, 1, 0)
        self.right_window = curses.newwin(self.height,
                                          self.right_window_width,
                                          1,
                                          self.left_window_width)

        self.resize_windows()

        self.labels = [str(label) for label in self.df.index]
        self.left_selection = Selection(len(self.labels), self.height)

        self.columns = [str(column) for column in self.df.columns]
        self.right_selection = Selection(len(self.columns), self.height)

        self.selected_window = 'left'

        self.draw_footer()
        self.draw_header()

        self.draw_left_window()
        self.draw_right_window()

        self.redraw_screen()

    def resize_terminal(self):
        '''Resize terminal.'''
        lines, cols = self.stdscr.getmaxyx()
        curses.resize_term(lines, cols)
        self.set_dimensions()
        self.resize_windows()

    def set_dimensions(self):
        '''Read dimensions from curses.'''
        self.height = curses.LINES - 2
        self.left_window_width = int(curses.COLS * 0.2)
        self.right_window_width = curses.COLS - int(curses.COLS * 0.2)

    def resize_windows(self):
        '''Resize all windows.'''
        self.header_window.resize(1, curses.COLS)
        self.header_window.mvwin(0, 0)

        self.left_window.resize(self.height, self.left_window_width)
        self.left_window.mvwin(1, 0)

        self.right_window.resize(self.height, self.right_window_width)
        self.right_window.mvwin(1, self.left_window_width)

        self.footer_window.resize(1, curses.COLS)
        self.footer_window.mvwin(curses.LINES - 1, 0)


    def draw_footer(self):
        '''Draw footer window.'''
        self.footer_window.erase()
        self.footer_window.bkgd(' ', curses.A_REVERSE)
        self.footer_window.addstr(0, 0, '-- {} --'.format(self.buffer_name))

    def draw_header(self):
        '''Draw header window.'''
        self.header_window.erase()
        self.header_window.bkgd(' ', curses.A_REVERSE)
        self.header_window.addstr(0, 0, 'Row')
        self.header_window.addstr(0, self.left_window_width, 'Column')

    def draw_left_window(self):
        '''Draw left pane window.'''
        self.left_window.erase()

        self.left_window.vline(0, self.left_window_width - 1, curses.ACS_VLINE, self.height)

        for row, i in enumerate(self.left_selection.get_range()):
            if i == self.left_selection.selection:
                self.left_window.addstr(row, 0, str(self.labels[i]), curses.A_REVERSE)
            else:
                self.left_window.addstr(row, 0, str(self.labels[i]))

    def draw_right_window(self):
        '''Draw right pane window.'''
        self.right_window.erase()
        for row, i in enumerate(self.right_selection.get_range()):
            column_name = self.columns[i]
            if i == self.right_selection.selection and self.selected_window == 'right':
                self.right_window.addstr(row, 0, column_name + ':', curses.A_REVERSE)
            else:
                self.right_window.addstr(row, 0, column_name + ':')
            self.right_window.addstr(row,
                                     len(column_name) + 2,
                                     ' ' + str(self.df.iloc[self.left_selection.selection, i]))

    def redraw_screen(self):
        '''Redraw screen.'''
        self.stdscr.noutrefresh()
        self.draw_header()
        self.draw_footer()
        self.header_window.noutrefresh()
        self.footer_window.noutrefresh()
        self.draw_left_window()
        self.draw_right_window()
        self.left_window.noutrefresh()
        self.right_window.noutrefresh()
        curses.doupdate()

    def parse_key(self, key):
        '''Parse key input.'''

        if key == ord('\t'):
            if self.selected_window == 'left':
                self.selected_window = 'right'
            else:
                self.selected_window = 'left'
            return

        if self.selected_window == 'left':
            if key == curses.KEY_UP:
                self.left_selection.move_up()
            if key == curses.KEY_DOWN:
                self.left_selection.move_down()
            if key == curses.KEY_PPAGE:
                self.left_selection.move_page_up()
            elif key == curses.KEY_NPAGE:
                self.left_selection.move_page_down()

        elif self.selected_window == 'right':
            if key == curses.KEY_UP:
                self.right_selection.move_up()
            elif key == curses.KEY_DOWN:
                self.right_selection.move_down()
            if key == curses.KEY_PPAGE:
                self.right_selection.move_page_up()
            elif key == curses.KEY_NPAGE:
                self.right_selection.move_page_down()

def browser_main(stdscr, df, buffer_name): # pylint: disable=C0103
    '''Main function for table browser and is sent to curses.wrapper'''
    curses.curs_set(0)
    stdscr.clear()

    record_browser = RecordBrowser(stdscr, df, buffer_name)

    while True:
        key = stdscr.getch()
        if key == curses.KEY_RESIZE:
            record_browser.resize_terminal()
        elif key == ord('x'):
            break
        else:
            record_browser.parse_key(key)

        record_browser.redraw_screen()

def browser(df, buffer_name): # pylint: disable=C0103
    '''Initiates and starts the table browser.

    Arguments:
        df          : Pandas data frame
        buffer_name : Name of buffer
    '''
    curses.wrapper(browser_main, df=df, buffer_name=buffer_name)

def main():
    '''Main function for calls from command line.'''
    parser = argparse.ArgumentParser(prog='table_browser',
                                     description='Browse data tables in the terminal.')

    parser.add_argument('file_name', nargs=1, type=str, help='name of comma separated file')
    parser.add_argument('--no-header', action='store_true', help='file has no header row')

    args = parser.parse_args()
    if args.no_header:
        header = None
    else:
        header = 'infer'

    df = pd.read_csv(args.file_name[0], dtype=object, header=header) # pylint: disable=C0103
    buffer_name = args.file_name[0]

    browser(df, buffer_name)
