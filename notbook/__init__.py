import inspect
from types import FrameType

from . import context
from .models import PlotBlock

try:
    from bokeh import plotting as bokeh_plotting
    from bokeh.embed import file_html as bokeh_file_html
    from bokeh.plotting import Figure as BokehFigure
except ImportError:
    bokeh_plotting = None

__all__ = ('show_plot',)

plot_id = 0


def show_plot(plot, *, title: str = None, filename: str = None):
    global plot_id
    if repr(plot.__class__) == "<class 'bokeh.plotting.figure.Figure'>":
        assert bokeh_plotting is not None, 'could not find bokeh install'
        assert isinstance(plot, BokehFigure), plot
        if context.is_active():
            frame = inspect.currentframe().f_back
            if plot.sizing_mode is None:
                plot.sizing_mode = 'stretch_both'
            if plot.aspect_ratio is None:
                plot.aspect_ratio = 1.78
            plot.title.text_font = 'Titillium Web, sans-serif'
            plot.title.text_font_size = '1.5rem'
            plot.title.align = 'center'
            plot.legend.label_text_font = 'Merriweather, serif'
            plot.legend.label_text_font_size = '1rem'

            plot.xaxis.axis_label_text_font = 'Ubuntu Mono, monospace'
            plot.xaxis.axis_label_text_font_size = '1.2rem'
            plot.xaxis.major_label_text_font_size = '1rem'
            plot.yaxis.axis_label_text_font = 'Ubuntu Mono, monospace'
            plot.yaxis.axis_label_text_font_size = '1.2rem'
            plot.yaxis.major_label_text_font_size = '1rem'
            bokeh_figure_to_html(plot, frame, title)
        else:
            if not filename:
                plot_id += 1
                filename = f'plot_{plot_id}.html'
            bokeh_plotting.output_file(filename, title=title)
            bokeh_plotting.show(plot)
    else:
        raise NotImplementedError(f'cannot render {plot} ({type(plot)})')


class FakeTemplate:
    def __init__(self):
        self.context = None

    def render(self, context):
        self.context = context


def bokeh_figure_to_html(fig, frame: FrameType, title: str = None):
    t = FakeTemplate()
    bokeh_file_html(fig, (None, None), template=t, title=title)
    plot_script = t.context['plot_script'].strip('\n')
    plot_div = t.context['plot_div'].strip('\n')
    block = PlotBlock(f'{plot_div}\n{plot_script}', frame.f_lineno)
    context.append(block)
