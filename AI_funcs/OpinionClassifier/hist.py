__author__ = 'Weiliang Guo'

import numpy as np
import matplotlib.pyplot as plt

def plot9():
    data = [ ("data1", 34), ("data2", 22),
            ("data3", 11), ( "data4", 28),
            ("data5", 57), ( "data6", 39),
            ("data7", 23), ( "data8", 98)]
    N = len( data )
    x = np.arange(1, N+1)
    y = [ num for (s, num) in data ]
    labels = [ s for (s, num) in data ]
    width = 1
    bar1 = plt.bar( x, y, width, color="y" )
    plt.ylabel( 'Intensity' )
    plt.xticks(x + width/2.0, labels )
    plt.show()

plot9()