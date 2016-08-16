# import numpy as num
import numpy as num
import matplotlib.pyplot as plt
import matplotlib.patches
import logging
import time

DEFAULT_IMSHOW = {
    'cmap': 'RdBu',
    'aspect': 'equal'
}


def _getAxes(axes):
    if axes is None:
        return plt.subplots(1, 1)
    elif isinstance(axes, plt.Axes):
        return axes.get_figure(), axes
    else:
        raise TypeError('Axes has to be of type matplotlib.Axes')


def _finishPlot(figure=None, axes=None):
    if not isinstance(axes, plt.Axes) and not isinstance(figure, plt.Figure):
        return plt.show()
    return None


def _setCanvas(obj, figure=None, axes=None):
    if axes is None and figure is None:
        obj._fig, obj._ax = plt.subplots(1, 1)
    elif isinstance(axes, plt.Axes):
        obj._fig, obj._ax = axes.get_figure(), axes
    elif isinstance(figure, plt.Figure):
        obj._fig, obj._ax = figure, figure.gca()
    else:
        raise TypeError('Axes has to be of type matplotlib.Axes\n'
                        'Figure has to be of type matplotlib.Figure')


class Plot2D(object):
    def __init__(self, displacement):
        self.title = 'Displacement'
        self.colorbar_label = ''
        self.default_component = 'displacement'

        self._displacement = displacement

        self._fig = None
        self._ax = None
        self._im = None
        self._cb = None

    def __call__(self, *args, **kwargs):
        return self.plot(*args, **kwargs)

    def _decorateAxes(self):
        self._ax.set_title('%s\n%s' % (self.title,
                                       self._displacement.meta.title))

    def _decorateImshow(self):
        array = self._im.get_array()
        _vmax = num.abs(array).max()

        self._im.set_clim(-_vmax, _vmax)
        self._im.set_extent(
                    (self._displacement.x.min(), self._displacement.x.max(),
                     self._displacement.y.min(), self._displacement.y.max()))

    def plot(self, component=None, axes=None, figure=None, **kwargs):
        _setCanvas(self, figure, axes)
        self._decorateAxes()

        if component is None:
            component = self.default_component

        try:
            data = getattr(self._displacement, component)
        except:
            raise AttributeError('Invalid component %s' % component)
        self.colorbar_label = component

        _kwargs = DEFAULT_IMSHOW.copy()
        _kwargs.update(kwargs)

        self._im = self._ax.imshow(data, **_kwargs)
        self._decorateImshow()

        if figure is not None:
            self.addColorbar()

        _finishPlot(figure, axes)
        return self._im

    def addColorbar(self):
        self._cb = self._fig.colorbar(self._im)
        self._cb.set_label(self.colorbar_label)


class QuadLeafRectangle(matplotlib.patches.Rectangle):
    def __init__(self, plotquadtree, leaf, **kwargs):
        matplotlib.patches.Rectangle.__init__(self, (0, 0), 0, 0, **kwargs)

        self._plotquadtree = plotquadtree
        self.leaf = leaf

        self.set_xy((self.leaf.llx, self.leaf.lly))
        self.set_height(self.leaf.length)
        self.set_width(self.leaf.length)

        # self.set_alpha(.5)
        self.set_color(self._plotquadtree.sm.to_rgba(self.leaf.mean))


class Plot2DQuadTree(object):
    def __init__(self, quadtree, cmap='RdBu', **kwargs):
        from matplotlib import cm
        self._quadtree = quadtree

        self._fig = None
        self._ax = None

        self.sm = cm.ScalarMappable(cmap=cmap)
        self.sm.set_clim(-1, 1)

        self.log = logging.getLogger(self.__class__.__name__)
        # Init leafs
        self._rectangles = [QuadLeafRectangle(self, leaf)
                            for leaf in self._quadtree.leafs]

    def __call__(self, *args, **kwargs):
        return self.plot(*args, **kwargs)

    def plot(self, figure=None, axes=None, **kwargs):
        _setCanvas(self, figure, axes)

        self._ax.patches = self._rectangles

        self._decorateAxes()
        self._ax.set_xlim((0, self._quadtree._scene.x.size))
        self._ax.set_ylim((0, self._quadtree._scene.y.size))
        self._ax.set_aspect('equal')

        _finishPlot(figure, axes)

    def plotInteractive(self):
        from matplotlib.widgets import Slider

        _setCanvas(self)
        # pl = Plot2D(self._quadtree._scene.los)
        # pl(axes=self._ax)

        def change_epsilon(e):
            self._quadtree.epsilon = e

        def close_figure(*args):
            self._quadtree.unsubscribe(self._update)

        self._ax.set_position([0.05, 0.15, 0.90, 0.8])
        ax_eps = self._fig.add_axes([0.05, 0.1, 0.90, 0.03])

        self._ax.plot(axes=self._ax)

        epsilon = Slider(ax_eps, 'Epsilon',
                         self._quadtree.epsilon - 1*self._quadtree.epsilon,
                         self._quadtree.epsilon + 1*self._quadtree.epsilon,
                         valinit=self._quadtree.epsilon, valfmt='%1.3f')
        epsilon.on_changed(change_epsilon)
        self._quadtree.subscribe(self._update)

        self._fig.canvas.mpl_connect('close_event', close_figure)

        _finishPlot()

    def _update(self):
        t0 = time.time()

        _vmax = num.abs(self._quadtree.means).max()

        self.sm.set_clim(-_vmax, _vmax)

        self.patches = []
        self._rectangles = [QuadLeafRectangle(self, leaf)
                            for leaf in self._quadtree.leafs]
        for rect in self._rectangles:
            self._ax.add_patch(rect)

        self.collections = []
        self._ax.scatter(*zip(*self._quadtree.focal_points), s=4, color='k')

        self._ax.set_xlim((0, self._quadtree._scene.x.size))
        self._ax.set_ylim((0, self._quadtree._scene.y.size))
        self._fig.canvas.draw()

        self.log.info('Redrew %d rectangles [%0.8f s]' %
                       (len(self._rectangles), time.time()-t0))

    def _decorateAxes(self):
        pass


__all__ = """
Plot2D
""".split()

if __name__ == '__main__':
    from kite.scene import SceneSynTest
    sc = SceneSynTest.createGauss()