from notbook import show_plot
from bokeh.plotting import figure
import numpy as np
import scipy.optimize as opt

"""md
_This is an example of a better way to work on and display numerical python code._

# Logistic curve fitting example

(Example is taken mostly from 
[here](https://ipython-books.github.io/93-fitting-a-function-to-data-with-nonlinear-least-squares/))

We define a logistic function with four parameters:

```maths
  \[f_{a,b,c,d}(x) = \frac{a}{1 + \exp\left(-c (x-d)\right)} + b\]
```
"""

# {
def f(x, a, b, c, d):
    return a / (1. + np.exp(-c * (x - d))) + b
# } The equation we'll try and fit

"""md
Define some random parameters:
"""
# {
a, c = np.random.exponential(size=2)
b, d = np.random.randn(2)
# }

# we actually cheat here and keep a "good" set of paramters
a = 0.8744
b = -2.0836
c = 1.3389
d = 0.4991

"""md
which are:
"""
print(f'a={a:0.4f} b={b:0.4f} c={c:0.4f} d={d:0.4f}')

"""md
Now, we generate random data points by using the sigmoid function and adding a bit of noise:
"""
# {
n = 100
x = np.linspace(-10, 10, n)
y_model = f(x, a, b, c, d)
y = y_model + a * 0.2 * np.random.randn(n)
# }

"""md
Plot that to see how it looks:
"""

p = figure(title='Model and random data')
p.line(x, y_model, color='black', line_dash='dashed', line_width=5, legend_label='model')
p.circle(x, y, size=10, legend_label='random data')
p.legend.location = 'top_left'
p.legend.click_policy = 'hide'
show_plot(p)

"""md
We now assume that we only have access to the data points and not the underlying generative function. 
These points could have been obtained during an experiment. 

By looking at the data, the points appear to approximately follow a sigmoid, so we may want to try to fit such a 
curve to the points. 
That's what curve fitting is about. 

SciPy's [`curve_fit()`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.curve_fit.html) 
function allows us to fit a curve defined by an 
arbitrary Python function to the data:
"""

# {
(a_, b_, c_, d_), _ = opt.curve_fit(f, x, y)

"""md
And use those parameters to estimate our underlying curve
"""
y_fit = f(x, a_, b_, c_, d_)
# }

p = figure(title='Model, random data and curve fit')
p.line(x, y_model, color='black', line_dash='dashed', line_width=5, legend_label='model')
p.circle(x, y, size=10, legend_label='random data')
p.line(x, y_fit, color='red', line_width=5, legend_label='curve fit')
p.legend.location = 'top_left'
p.legend.click_policy = 'hide'
show_plot(p)

"""md
we can also manually compare our initial parameters with with those from `curve_fit()`:
"""

print(f'initial parameters:    a={a:0.4f} b={b:0.4f} c={c:0.4f} d={d:0.4f}')
print(f'curve_fit parameters:  a={a_:0.4f} b={b_:0.4f} c={c_:0.4f} d={d_:0.4f}')
