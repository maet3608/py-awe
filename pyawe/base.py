# Base class for analytics units
from __future__ import absolute_import, print_function

from uuid import uuid1
import threading
import dpath.util as du
import logging
import traceback

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


def is_iterable(obj):
    return hasattr(obj, '__iter__')


def result(obj):
    """Converts object into result"""
    if isinstance(obj, tuple): return list(obj)
    if isinstance(obj, list): return obj
    return [obj]


def walk(nodes, func, eval_id, level=0):
    for node in nodes:
        if node.eval_id == eval_id:
            continue
        node.eval_id = eval_id
        func(node, level)
        walk(node.innodes, func, eval_id, level + 1)


def pretty_print(nodes):
    def show(node, level):
        print('  ' * level, node.name)

    walk(result(nodes), show, uuid1())


def test(nodes):
    def run_test(node, level):
        print('testing', node.name, '...', end='')
        node.test()
        print('PASSED')

    walk(result(nodes), run_test, uuid1())


def finalize(nodes):
    walk(result(nodes), lambda n, l: n.finalize(), uuid1())


def defaultspec():
    return {'input':[], 'output':[]}


class AweBase(object):
    def __init__(self, name, spec):
        self._spec = spec
        self.name = name
        self.loginfo('created node')

    def spec(self, path):
        return du.get(self._spec, path)

    def spec(self, path, value):
        du.new(self._spec, path, value, '.')

    def _specio(self, channel, name, typ):
        self._spec[channel].append({
            "name": name,
            "type": typ
        })

    def input(self, name, typ):
        self._specio('input', name, typ)

    def output(self, name, typ):
        self._specio('output', name, typ)

    def loginfo(self, msg, *args, **kwargs):
        logger.info(self.name + ': ' + msg, *args, **kwargs)

    def process(self, *indata):
        return indata  # always return list

    def finalize(self):
        pass

    def test(self):
        assert 0, 'Implement test for node: ' + self.name


class AweNode(AweBase):
    def __init__(self, name, spec=None):
        AweBase.__init__(self, name, spec if spec else defaultspec())
        self.innodes = []
        self.outbuffer = {}
        self.eval_id = None

    def reset(self):
        pass

    def __repr__(self):
        return str(self.name)

    @staticmethod
    def __wrap(innode):
        if hasattr(innode, '__call__'):
            return Func(innode)
        if isinstance(innode, str):
            return JsonPath(innode)
        return innode

    def __rshift__(self, innode):
        self.loginfo('{} >> {}'.format(self, innode))
        innode = AweNode.__wrap(innode)
        if isinstance(innode, Group):
            for node in innode.innodes:
                node.innodes.append(self)
        else:
            innode.innodes.append(self)
        return innode

    def __pow__(self, innode):
        if isinstance(self, Group):
            self.innodes.append(innode)
            return self
        return Group(self, innode)

    def __floordiv__(self, innode):
        if isinstance(self, If):
            self.innodes.append(innode)
            return self
        return If(self, innode)

    def __getitem__(self, sliced):
        return self >> Slice(sliced)

    def __getslice__(self, start, stop):
        return self.__getitem__(slice(start, stop))

    def _store(self, outdata):
        self.outbuffer = outdata
        return outdata

    @staticmethod
    def is_done(data):
        return data is None or isinstance(data, Exception)

    def _save_process(self, indata):
        try:
            return self.process(*indata)
        except Exception:
            tb = traceback.format_exc()
            return Exception("Error in node '" + self.name + "':\n" + tb)

    def _eval_innodes(self, eval_id, innodes):
        indata = []
        for node in innodes:
            outdata = node._eval(eval_id)
            if AweNode.is_done(outdata):
                return self._store(outdata), True
            indata.extend(outdata)
        return indata, False

    def _eval(self, eval_id):
        if self.eval_id != eval_id:
            self.eval_id = eval_id
            indata, is_done = self._eval_innodes(eval_id, self.innodes)
            if is_done: return indata
            self.loginfo('processing')
            self._store(self._save_process(indata))
        return self.outbuffer

    def run(self, **kwargs):
        threaded = kwargs.get('threaded', False)
        max_n = kwargs.get('max_n', None)
        show = kwargs.get('show', False)
        others = kwargs.get('others', [])  # list of other nodes to run as well
        nodes = [self] + others
        params = (nodes, max_n, show)
        if threaded:
            thread = threading.Thread(target=_run, args=params)
            thread.start()
            return thread
        else:
            _run(*params)
            return threading.current_thread()


def _run(*params):
    nodes, max_n, show = params
    n = 0
    while 1:
        n += 1
        if max_n and n > max_n: return
        eval_id = uuid1()
        for node in nodes:
            result = node._eval(eval_id)
            if isinstance(result, Exception): raise Exception(result)
            if show: print(result)
            if result is None: return


class Slice(AweNode):
    def __init__(self, slize):
        name = 'Slice:' + str(slize)
        AweNode.__init__(self, name)
        self.slize = slize

    def process(self, *indata):
        return result(indata[self.slize])


class JsonPath(AweNode):
    def __init__(self, jsonpath):
        name = 'JsonPath:' + jsonpath
        AweNode.__init__(self, name)
        self.jsonpath = jsonpath

    def process(self, *indata):
        outdata = du.get(list(indata), self.jsonpath, separator='.')
        return result(outdata)


class If(AweNode):
    is_true = {'any': any, 'all': all, 'none': lambda d: not any(d)}

    def __init__(self, *nodes, **kwargs):
        mode = kwargs.get('mode', 'any')
        name = 'If:' + mode + ':' + str(nodes[0])
        AweNode.__init__(self, name)
        self.mode = mode
        self.innodes = list(nodes)

    def _eval_innodes(self, eval_id, innodes):
        assert 2 <= len(innodes) <= 3, 'Invalid #params for condition!'
        super_eval = super(If, self)._eval_innodes
        outdata, is_done = super_eval(eval_id, innodes[0:1])  # IF
        if is_done:
            return outdata, True
        if self.is_true[self.mode](outdata):  # THEN
            return super_eval(eval_id, innodes[1:2])
        if len(innodes) == 3:  # ELSE
            return super_eval(eval_id, innodes[2:3])


class Group(AweNode):
    def __init__(self, *nodes):
        AweNode.__init__(self, str(nodes))
        self.innodes = list(nodes)


class Func(AweNode):
    def __init__(self, function):
        name = 'Func: ' + function.__name__
        AweNode.__init__(self, name)
        self.function = function

    def process(self, *indata):
        return result(self.function(*indata))

class Display(AweNode):
    def __init__(self, name='Display'):
        AweNode.__init__(self, name)
        self.input('indata', 'any')
        self.output('outdata', 'any')

    def process(self, *indata):
        print(self.name, ' '.join(map(str, indata)))
        return result(indata)

class Counter(AweNode):
    def __init__(self, name='Counter'):
        AweNode.__init__(self, name)
        self.output('count', 'int')
        self.reset()

    def process(self):
        self.counter += 1
        return result(self.counter)

    def reset(self):
        self.counter = -1


if __name__ == "__main__":
    counter = Counter("MyCounter")
    disp = Display()

    print(counter._spec)
    print(disp._spec)

    counter >> disp
    disp.run(max_n=5)
