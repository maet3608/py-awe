# py-awe

Another workflow engine (awe) based on Python.


Prototype implementation of a simple workflow engine. Allows to build
flows such as the following:

```
    counter1 = Counter('Counter1')
    counter2 = Counter('Counter2')
    adder = MyAdder('Adder')
    display = Display('sum =')

    counter1 ** counter2 >> adder >> display

    display.run(max_n=5)
```

which outputs

```
sum = 0
sum = 2
sum = 4
sum = 6
sum = 8
```


