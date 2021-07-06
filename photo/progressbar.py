from sys import stdout
from time import sleep, time, strftime, gmtime

class Progressbar:
    def __init__(self, total = 100, header = '', verbose = False, width = 50, character = '='):
        self._total = total
        self._width = width
        self._verbose = verbose
        if header: self._header = header + ': '
        else: self._header = ''
        self._char = character
        self._start_time = time()
        stdout.write('\n')
        self.update(0)

    def update(self, value):
        perc = float(value) / self._total * 100
        s1 = self._char * int(self._width * perc / 100)
        s2 = (self._width - len(s1)) * ' '
        if self._verbose:
            time_elapsed = int(round(time() - self._start_time, 0))
            try: time_estimated = int((100-perc) * time_elapsed / perc)
            except ZeroDivisionError: time_estimated = 0
            t2 = strftime('%H:%M:%S', gmtime(time_estimated))
            stdout.write('\r{0}[{1}{2}] {3:05.2f}% {4}'.format(self._header, s1, s2, perc, t2))
        else:
            stdout.write('\r{0}[{1}{2}] {3:05.2f}% '.format(self._header, s1, s2, perc))
        stdout.flush()

    def finish(self):
        self.update(self._total)
        stdout.write('\n')
        stdout.flush()

p = Progressbar(200, verbose = True)
for i in range(1,200):
    sleep(1)
    p.update(i)
p.finish()
