class rigid_dict(dict):
    def __init__(self, defaults, dct=None, **kwargs):
        super().__init__(kwargs)
        self.keys = defaults
        for key in self.keys:
            self.setdefault(key, self.keys[key][1])
        if isinstance(dct, dict):
            for key in dct:
                self[key] = dct[key]

    def __setitem__(self, key, value):
        if key not in self.keys.keys():
            raise KeyError(f'{key} is an invalid key')
        if not isinstance(value, self.keys[key][0]):
            if value is not None:
                raise TypeError(f'{key}:{value} is not a {self.keys[key][0]}.')
        super().__setitem__(key, value)

    def __getitem__(self, key):
        if key not in self.keys:
            raise KeyError(f'{key} is an invalid key')
        return super().__getitem__(key)

class state_item(rigid_dict):
    def __init__(self, dct=None, **kwargs):
        default_keys = {'name':      [str, None],
                        'valves':    [list, None],
                        'h2o':       [(int, float), None],
                        'ads':       [(int, float), None],
                        'battery':   [(int, float), None],
                        'sample':    [(int, float), None],
                        'backflush': [(int, float), None],
                        'pump':      [(str, int, bool), None],
                        'aux1':      [(str, int, bool), None],
                        'aux2':      [(str, int, bool), None],
                        'monitor':   [bool, False],
                        'condition': [str, None],
                        'value':     [(int, float, str), None],
                        'message':   [str, ''],
<<<<<<< Updated upstream
                        'timeout':   [(int, float), None]}
=======
                        'timeout':   [(int, float), None],
                        'active':    [str, None]}
>>>>>>> Stashed changes
        super().__init__(default_keys, dct, **kwargs)

class sequence_item(rigid_dict):
    def __init__(self, dct=None, **kwargs):
       default_keys = {'Method':      [str, None],
                       'Stream':      [int, None],
                       'Sample Name': [str, None],
                       'Repetition':  [int, 1],
                       'Description': [str, None],
                       'Macro':       [str, None],
                       'on_error':    [str, None],
                       'time':        [(int, float), 0],}
<<<<<<< Updated upstream
       super().__init__(default_keys, dct, **kwargs)
=======
       super().__init__(default_keys, dct, **kwargs)

class LowTemp(Exception):
        pass
>>>>>>> Stashed changes
