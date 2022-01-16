#external functions:
######################
"""
This sources were obtained from different places of internet.
    iswt from PyWavelets google groups. author:Michael Marino
    extrema from http://mail.scipy.org/pipermail/scipy-user/2008-October/018318.html.\
        author:  iCy-fLaME
    smooth from http://www.scipy.org/Cookbook/SignalSmooth
"""
import pywt
from numpy import arange, zeros, math, r_, convolve, ones, roll, diff, sign, nonzero

def iswt(coefficients, wavelet):
    """
     Input parameters:
       coefficients
         approx and detail coefficients, arranged in level value
         exactly as output from swt:
         e.g. [(cA1, cD1), (cA2, cD2), ..., (cAn, cDn)]
       wavelet
         Either the name of a wavelet or a Wavelet object
   """
    output = coefficients[0][0].copy() # Avoid modification of input data
    #num_levels, equivalent to the decomposition level, n
    num_levels = len(coefficients)
    for j in range(num_levels,0,-1):
        step_size = int(math.pow(2, j-1))
        last_index = step_size
        _, cD = coefficients[num_levels - j]
        for first in range(last_index): # 0 to last_index - 1
            # Getting the indices that we will transform
            indices = arange(first, len(cD), step_size)
            # select the even indices
            even_indices = indices[0::2]
            # select the odd indices
            odd_indices = indices[1::2]
            # perform the inverse dwt on the selected indices,
            # making sure to use periodic boundary conditions
            x1 = pywt.idwt(output[even_indices], cD[even_indices],wavelet, 'per')
            x2 = pywt.idwt(output[odd_indices], cD[odd_indices],wavelet, 'per')
            # perform a circular shift right
            x2 = roll(x2, 1)
            # average and insert into the correct indices
            output[indices] = (x1 + x2)/2.
    return output

def extrema(x, _max = True, _min = True, strict = False, withend = False):
    """
    This function will index the extrema of a given array x.

    Options:
    _max        If true, will index maxima
    _min        If true, will index minima
    strict        If true, will not index changes to zero gradient
    withend    If true, always include x[0] and x[-1]
    This function will return a tuple of extrema indexies and values
    """

    # This is the gradient

    dx = zeros(len(x))

    dx[1:] = diff(x)
    dx[0] = dx[1]

    # Clean up the gradient in order to pick out any change of sign

    dx = sign(dx)

    # define the threshold for whether to pick out changes to zero gradient
    threshold = 0
    if strict:
        threshold = 1

    # Second order diff to pick out the spikes
    d2x = diff(dx)

    if _max and _min:
        d2x = abs(d2x)
    elif _max:
        d2x = -d2x
    # Take care of the two ends
    if withend:
        d2x[0] = 2
        d2x[-1] = 2

    # Sift out the list of extremas

    ind = nonzero(d2x > threshold)[0]

    return ind, x[ind]

def smooth(x,window_len=11,window='hanning'):
    """
       x: the input signal
       window_len: the dimension of the smoothing window; should be an odd integer
       window: the type of window from 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'
           flat window will produce a moving average smoothing.
    output:
       the smoothed signal
    """

    if x.ndim != 1:
        raise ValueError("smooth only accepts 1 dimension arrays.")

    if x.size < window_len:
        raise ValueError("Input vector needs to be bigger than window size.")

    if window_len<3:
        return x

    if not window in ['flat','hanning', 'hamming', 'bartlett', 'blackman']:
        raise ValueError("Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'")

    s=r_[x[window_len-1:0:-1],x,x[-1:-window_len:-1]]
    if window == 'flat': #moving average
        w=ones(window_len,'d')
    else:
        w=eval(window+'(window_len)')

    y=convolve(w/w.sum(),s,mode='valid')
    return y[3:]
