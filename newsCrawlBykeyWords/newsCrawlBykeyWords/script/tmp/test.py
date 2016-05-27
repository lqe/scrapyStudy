class Describe(object):

    def __get__(self, instance, owner):
        return 1

    def __set__(self, instance, value):
        print value


class Test():
    a = Describe()


t = Test()
# t.a = 1
print t.a
t.a = 3
print t.a
