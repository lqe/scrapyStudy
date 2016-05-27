class Storage(dict):
    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError,e:
            raise AttributeError,e

    def __delattr__(self, item):
        try:
            del self[item]
        except KeyError, e:
            raise AttributeError,e

    def __setattr__(self, key, value):
        self[key] = value