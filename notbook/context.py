_exec_context = None


def activate():
    global _exec_context
    _exec_context = []


def is_active() -> bool:
    return _exec_context is not None


def get():
    return _exec_context


def append(obj):
    assert isinstance(_exec_context, list), 'context not prepared'
    _exec_context.append(obj)
