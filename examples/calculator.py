from __future__ import absolute_import, print_function

from aursol.base import Counter, Display, AweNode
from specification import SPEC


class MyAdder(AweNode):
    def __init__(self, name='MyAdder'):
        AweNode.__init__(self, name, SPEC)

    def process(self, number1, number2):
        output = number1 + number2
        return [output]

    def test(self):
        assert self.process([1, 2]) == [3]


if __name__ == "__main__":
    counter1 = Counter('Counter1')
    counter2 = Counter('Counter2')
    adder = MyAdder('Adder')
    display = Display('sum =')

    counter1 ** counter2 >> adder >> display

    display.run(max_n=5)