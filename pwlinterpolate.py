

""" Classes for interpolating values.
"""



from numpy import shape, sometrue, array, transpose, searchsorted, \
                  ones, logical_or, atleast_1d, atleast_2d, meshgrid, ravel, \
                  dot, poly1d, asarray, intp
import numpy as np
import scipy.special as spec
import math

import errormsg

class interp1d(object):
    """
    This class was copied and modified from the scipy.interpolate.interp1d class.
    see the scipy documentation or source code for more details. 
    Parameters
    ----------
    x : array_like
        A 1-D array of monotonically increasing or decreasing real values.
    y : array_like
        A N-D array of real values. The length of `y` along the interpolation
        axis must be equal to the length of `x`.
    """
    def __init__(self, x, y, name = 'unnamed',
                 copy=True, bounds_error=True, fill_value=np.nan):
        """ Initialize a 1D linear interpolation class."""

        self.name = name
        self.copy = copy
        self.bounds_error = bounds_error
        self.fill_value = fill_value


        if x.ndim != 1:
            raise ValueError("the x array must have exactly one dimension.")
        if y.ndim != 1:
            raise ValueError("the y array must have exactly one dimension.")

        # Force-cast y to a floating-point type, if it's not yet one
        if not issubclass(y.dtype.type, np.inexact):
            y = y.astype(np.float_)

        minval = 2
        self._call = self._call_linear

        len_y = len(y)
        len_x = len(x)
        if len_x != len_y:
            raise ValueError("x and y arrays must be equal in length along "
                             "interpolation axis.")
        if len_x < minval:
            raise ValueError("x and y arrays must have at "
                             "least %d entries" % minval)

        order = x.argsort() 
        x = array(x[order] , copy=self.copy)
        y = array(y[order], copy=self.copy)

        self.x = x
        self.y = y

    def _call_linear(self, x_new):

        # 2. Find where in the orignal data, the values to interpolate
        #    would be inserted.
        #    Note: If x_new[n] == x[m], then m is returned by searchsorted.
        x_new_indices = searchsorted(self.x, x_new)

        # 3. Clip x_new_indices so that they are within the range of
        #    self.x indices and at least 1.  Removes mis-interpolation
        #    of x_new[n] = x[0]
        x_new_indices = x_new_indices.clip(1, len(self.x)-1).astype(int)

        # 4. Calculate the slope of regions that each x_new value falls in.
        lo = x_new_indices - 1
        hi = x_new_indices

        x_lo = self.x[lo]
        x_hi = self.x[hi]
        y_lo = self.y[..., lo]
        y_hi = self.y[..., hi]

        # Note that the following two expressions rely on the specifics of the
        # broadcasting semantics.
        slope = (y_hi-y_lo) / (x_hi-x_lo)


        # 5. Calculate the actual value for each entry in x_new.
        y_new = slope*(x_new-x_lo) + y_lo

        return y_new

    def __call__(self, x_new):
        """Find interpolated y_new = f(x_new).

        Parameters
        ----------
        x_new : number or array
            New independent variable(s).

        Returns
        -------
        y_new : ndarray
            Interpolated value(s) corresponding to x_new.

        """

        # 1. Handle values in x_new that are outside of x.  Throw error,
        #    or return a list of mask array indicating the outofbounds values.
        #    The behavior is set by the bounds_error variable.
        x_new = asarray(x_new)
        out_of_bounds = self._check_bounds(x_new)

        y_new = self._call(x_new)

        # Rotate the values of y_new back so that they correspond to the
        # correct x_new values. For N-D x_new, take the last (for linear)
        # or first (for other splines) N axes
        # from y_new and insert them where self.axis was in the list of axes.
        nx = x_new.ndim
        ny = y_new.ndim

        # 6. Fill any values that were out of bounds with fill_value.
        # and
        # 7. Rotate the values back to their proper place.

        if nx == 0:
            # special case: x is a scalar
            if out_of_bounds:
                if ny == 0:
                    return asarray(self.fill_value)
                else:
                    y_new[...] = self.fill_value
            return asarray(y_new)
        else:
            y_new[..., out_of_bounds] = self.fill_value
            return y_new

    def _check_bounds(self, x_new):
        """Check the inputs for being in the bounds of the interpolated data.

        Parameters
        ----------
        x_new : array

        Returns
        -------
        out_of_bounds : bool array
            The mask on x_new of values that are out of the bounds.
        """

        # If self.bounds_error is True, we raise an error if any x_new values
        # fall outside the range of x.  Otherwise, we return an array indicating
        # which values are outside the boundary region.
        below_bounds = x_new < self.x[0]
        above_bounds = x_new > self.x[-1]
        
        # !! Could provide more information about which values are out of bounds
        if self.bounds_error and below_bounds.any():
            out_of_bounds_below = None
              
            msg = "The following values are below the interpolation range: "

            if x_new.ndim < 1:
                out_of_bounds_below = x_new
                msg = msg + '\n\t' + str(out_of_bounds_below) 
            else:
                out_of_bounds_below  = x_new[ np.where( x_new < self.x[0] ) ]
                msg = msg + '\n\t' + str(out_of_bounds_below) 
            
            print msg 
              
            errormsg.box('INTERPOLATION :: ' + self.name, msg)

            raise ValueError("A value in x_new is below the interpolation "
                "range.")
                
                
        if self.bounds_error and above_bounds.any():
            out_of_bounds_above = None
              
            msg = "The following values are above the interpolation range: "

            if x_new.ndim < 1:
                out_of_bounds_above = x_new
                msg = msg + '\n\t' + str(out_of_bounds_above) 
            else:
                out_of_bounds_above  = x_new[ np.where( x_new < self.x[0] ) ]
                msg = msg + '\n\t' + str(out_of_bounds_above) 
            
            print msg 
              
            errormsg.box('INTERPOLATION :: ' + self.name, msg)

            raise ValueError("A value in x_new is above the interpolation "
                "range.")
            

        # !! Should we emit a warning if some values are out of bounds?
        # !! matlab does not.
        out_of_bounds = logical_or(below_bounds, above_bounds)
        return out_of_bounds

