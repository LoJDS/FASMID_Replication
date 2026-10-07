import numpy as np
import dill
import math
import pandas as pd
#import seaborn as sns
import statistics
from statistics import mode
import matplotlib.pyplot as plt
from matplotlib import colors
import matplotlib.font_manager
import matplotlib.patches as mpatches
import matplotlib.cm  as cm
import matplotlib.lines as mlines
import matplotlib as mpl
import plotly.graph_objects as go
import importlib
#import astropy
from mpl_toolkits.mplot3d import Axes3D
import csv
import pickle
import datetime
from datetime import datetime
from datetime import date
from matplotlib.legend_handler import HandlerPatch
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredAuxTransformBox
import sys
import cmasher as cmr
np.set_printoptions(threshold=sys.maxsize)
from matplotlib.patches import Rectangle
from matplotlib.pylab import *
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d import proj3d
from matplotlib.collections import LineCollection
from matplotlib.colors import ListedColormap, BoundaryNorm
import SALib

class HandlerEllipse(HandlerPatch):
    def create_artists(self, legend, orig_handle,
                       xdescent, ydescent, width, height, fontsize, trans):
        center = 0.5 * width - 0.5 * xdescent, 0.5 * height - 0.5 * ydescent
        p = mpatches.Ellipse(xy=center, width=height + xdescent,
                             height=height + ydescent)
        self.update_prop(p, orig_handle, legend)
        p.set_transform(trans)
        return [p]


