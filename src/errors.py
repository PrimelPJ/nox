class NoxError(Exception):
    pass

class LexError(NoxError):
    pass

class ParseError(NoxError):
    pass

class NoxRuntimeError(NoxError):
    pass
