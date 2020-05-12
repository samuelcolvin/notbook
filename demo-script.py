from notbook import show_plot
from bokeh.plotting import figure
from bokeh.sampledata.iris import flowers

"""md
# This is a title

This should be a **section** of markdown.

Here we have bullets:

* one bullet
* another bullet
"""

# { Testing Section
question = 422
foobar = 123
print('answer:', question + 2)
# }

"""md
another section of **markdown**.
"""

print('this should be shown as a standalone code block')
print({'foo': 'bar', 2: 3, 4: list(range(5)), (1, 2): range(10)}, [1, 2, 3])
print('last part of print')

"""md
different
"""
print(1, 2, '3')

# {
import re
RE_URI_NOT_ALLOWED = re.compile(r'[^a-zA-Z0-9_\-/.]')
RE_HTML_SYMBOL = re.compile(r'&(?:#\d{2,}|[a-z0-9]{2,});')
RE_TITLE_NOT_ALLOWED = re.compile(r'[^a-z0-9_\-]')
RE_REPEAT_DASH = re.compile(r'-{2,}')


def slugify(v, *, path_like=True):
    v = v.replace(' ', '-').lower()
    if path_like:
        v = RE_URI_NOT_ALLOWED.sub('', v)
    else:
        v = RE_HTML_SYMBOL.sub('', v)
        v = RE_TITLE_NOT_ALLOWED.sub('', v)
    return RE_REPEAT_DASH.sub('-', v).strip('_-')


print('slugify:', slugify('This is - a sentence'))
# } useful bit of code about this


colormap = {'setosa': 'red', 'versicolor': 'green', 'virginica': 'blue'}
colors = [colormap[x] for x in flowers['species']]

p = figure(title='Iris Morphology')
p.xaxis.axis_label = 'Petal Length'
p.yaxis.axis_label = 'Petal Width'

p.circle(flowers['petal_length'], flowers['petal_width'], color=colors, fill_alpha=0.2, size=10)

show_plot(p)
