"""md
This is a very simple script.
"""
# {

def fib(n: int) -> int:
    if n < 2:
        return n
    return fib(n-2) + fib(n-1)

print(fib(10))

print({i: fib(i) for i in range(9)})
