from functools import wraps


def simple_decorator_with_args(accumulator):
    
    def simple_decorator(f):
        
        @wraps(f)
        def wrapper(*args, **kwargs):
            kwargs['accumulator'] = accumulator
            print('Calling decorated function')
            return f(*args, **kwargs)
        
        return wrapper
    
    return simple_decorator