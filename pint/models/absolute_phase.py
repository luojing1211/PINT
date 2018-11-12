""" This module implements the timing model absolute phase (TZRMJD, TZRSITE ...)
"""
from __future__ import absolute_import, print_function, division
from warnings import warn
from astropy import log
from . import parameter as p
from .timing_model import PhaseComponent
import astropy.units as u
import pint.toa as toa
import numpy as np

class AbsPhase(PhaseComponent):
    """ This is a class that implements the absolute phase model. The model
        defines the absolute phase's reference time and observatory.
        Note
        ----
        Although this class is condisder as a phase component, it does not
        provide the phase_func
    """
    register = True

    def __init__(self):
        super(AbsPhase, self).__init__()
        self.add_param(p.MJDParameter(name="TZRMJD",
                       description="Epoch of the zero phase.", frozen=False))
        self.add_param(p.strParameter(name="TZRSITE",
                       description="Observatory of the zero phase measured."))
        self.add_param(p.floatParameter(name="TZRFRQ", units=u.MHz,
                       description="The frequency of the zero phase mearsured."))

        self.category = 'absolute_phase'

    def setup(self):
        super(AbsPhase, self).setup()
        # Check input Parameters
        if self.TZRMJD.value is None:
            raise MissingParameter("AbsPhase", "TZRMJD", "TZRMJD is required "
                                   "to compute the absolute phase. ")
        if self.TZRSITE.value is None:
            self.TZRSITE.value = "ssb"
            # update the TZRMJD to new time scale
            self.TZRMJD.time_scale = 'tdb'
            log.info("The TZRSITE is set at the solar system barycenter.")

        if (self.TZRFRQ.value is None) or (self.TZRFRQ.value == 0.0):
            self.TZRFRQ.quantity = float("inf")*u.MHz
            log.info("TZRFRQ was 0.0 or None. Setting to infinite frequency.")

        # Add TZRMJD to the derivative functions
        self.register_deriv_funcs(self.d_phase_d_TZRMJD, 'TZRMJD')

    def get_TZR_toa(self, toas):
        """ Get the TOAs class for the TZRMJD. We are treating the TZRMJD as a
            special TOA.
        """
        # NOTE: Using TZRMJD.quantity.jd[1,2] so that the time scale can be properly
        # set to the TZRSITE default timescale (e.g. UTC for TopoObs and TDB for SSB)
        TZR_toa = toa.TOA((self.TZRMJD.quantity.jd1-2400000.5,
                           self.TZRMJD.quantity.jd2), obs=self.TZRSITE.value,
                          freq=self.TZRFRQ.quantity)
        clkc_info = toas.clock_corr_info
        tz = toa.get_TOAs_list([TZR_toa,], include_bipm=clkc_info['include_bipm'],
                               include_gps=clkc_info['include_gps'],
                               ephem=toas.ephem, planets=toas.planets)
        return tz

    def d_phase_d_TZRMJD(self, toas, param, delay):
        """ The derivative of phase with respect to the absolute phase refrence
            time, TZRMJD.
        """
        return np.ones(len(toas)) * (u.cycle/u.cycle)
