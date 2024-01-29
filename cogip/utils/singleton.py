class Singleton(type):
    """
    Meta class used to declare singleton

    Example:

        from dataclasses import dataclass


        @dataclass
        class Data(metaclass=Singleton):
            name: str = ""


        data = Data()
        print(data)            # output: Data(name='')
        data.name = "foo"
        print(data)            # output: Data(name='foo')
        print(Data())          # output: Data(name='foo')
        print(data is Data())  # output: True
    """
    _instance = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instance:
            cls._instance[cls] = super().__call__(*args, **kwargs)
        return cls._instance[cls]
