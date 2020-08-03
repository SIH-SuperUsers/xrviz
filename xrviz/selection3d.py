import panel as pn
import plotly.express as px
from .sigslot import SigSlot

class Selection3d(SigSlot):
    def __init__(self):
        super().__init__()
        self.skip_lon = pn.widgets.TextInput(name='skip_lon', value = "20", width=140)
        self.skip_lat = pn.widgets.TextInput(name='skip_lat', value = "20", width=140)
        self.skip_lev = pn.widgets.TextInput(name='skip_lev', value = "2", width=140)

        self.frame_height_3d = pn.widgets.IntSlider(name='frame_height_3d', value=600, start=100,
                                                 end=1200)
        self.frame_width_3d = pn.widgets.IntSlider(name='frame_width_3d', value=600, start=100,
                                                end=1200)
        self.surface_count = pn.widgets.IntSlider(name='surface_count', value=30, start=0,
                                                  end=100)
        self.cmap_3d = pn.widgets.Select(name='cmap_3d', value='inferno',
                                      options=px.colors.named_colorscales())
        self.opacity = pn.widgets.FloatSlider(name='opacity', start=0, end=1,
                                            step=0.01, value=0.2, width=300)

#         self.lower_limit = pn.widgets.TextInput(name='cmap lower limit', width=140)
#         self.upper_limit = pn.widgets.TextInput(name='cmap upper limit', width=140)
        TEXT = """Customize the Cube."""

        self.panel = pn.Column(
            pn.pane.Markdown(TEXT, margin=(0, 10)),
            pn.Row(self.skip_lon, self.skip_lat, self.skip_lev),
            pn.Row(self.frame_height_3d, self.frame_width_3d),
            pn.Row(self.opacity, self.surface_count),
            pn.Row(self.cmap_3d),
            name='Selection_3d'
        )

    @property
    def kwargs(self):
        out = {widget.name: widget.value
               for row in self.panel[1:] for widget in row}
        return out