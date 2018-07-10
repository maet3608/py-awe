from base import AweNode, result
from glob import iglob
import time


class Const(AweNode):
    def __init__(self, outdata):
        name = 'Const:' + str(outdata)
        AweNode.__init__(self, name)
        self.outdata = outdata

    def process(self):
        return result(self.outdata)


class Once(AweNode):
    def __init__(self, outdata):
        name = 'Once:' + str(outdata)
        AweNode.__init__(self, name)
        self.done = False
        self.outdata = outdata

    def process(self):
        if self.done: []
        self.done = True
        return result(self.outdata)

    def reset(self):
        self.done = False


class Sleep(AweNode):
    def __init__(self, seconds):
        name = 'Sleep:' + str(seconds)
        AweNode.__init__(self, name)
        self.seconds = seconds

    def process(self, *indata):
        time.sleep(self.seconds)
        return indata


class Join(AweNode):
    def __init__(self, name='Join'):
        AweNode.__init__(self, name)

    def process(self, *indata):
        return indata


class Stop(AweNode):
    def __init__(self):
        AweNode.__init__(self, 'Stop')

    def process(self, *indata):
        return None


class ImageReader(AweNode):
    def __init__(self, filepattern):
        name = 'ImageReader:' + filepattern
        AweNode.__init__(self, name)
        self.filepattern = filepattern
        self.reset()

    def process(self):
        try:
            fullpath = next(self.iter, None)
            return [fullpath]
        except StopIteration:
            return None

    def reset(self):
        self.iter = iglob(self.filepattern)
