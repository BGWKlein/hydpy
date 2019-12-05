# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# imports...
# ...from HydPy
from hydpy.core import modeltools
from hydpy.cythons import modelutils
# ...from lland
from hydpy.models.lland import lland_control
from hydpy.models.lland import lland_derived
from hydpy.models.lland import lland_inputs
from hydpy.models.lland import lland_fluxes
from hydpy.models.lland import lland_states
from hydpy.models.lland import lland_logs
from hydpy.models.lland import lland_aides
from hydpy.models.lland import lland_outlets
from hydpy.models.lland.lland_constants import WASSER, FLUSS, SEE, VERS


class Calc_NKor_V1(modeltools.Method):
    """Adjust the given precipitation values.

    Basic equation:
      :math:`NKor = KG \\cdot Nied`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(3)
        >>> kg(0.8, 1.0, 1.2)
        >>> inputs.nied = 10.0
        >>> model.calc_nkor_v1()
        >>> fluxes.nkor
        nkor(8.0, 10.0, 12.0)
    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.KG,
    )
    REQUIREDSEQUENCES = (
        lland_inputs.Nied,
    )
    RESULTSEQUENCES = (
        lland_fluxes.NKor,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.nkor[k] = con.kg[k] * inp.nied


class Calc_TKor_V1(modeltools.Method):
    """Adjust the given air temperature values.

    Basic equation:
      :math:`TKor = KT + TemL`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(3)
        >>> kt(-2.0, 0.0, 2.0)
        >>> inputs.teml(1.)
        >>> model.calc_tkor_v1()
        >>> fluxes.tkor
        tkor(-1.0, 1.0, 3.0)
    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.KT,
    )
    REQUIREDSEQUENCES = (
        lland_inputs.TemL,
    )
    RESULTSEQUENCES = (
        lland_fluxes.TKor,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.tkor[k] = con.kt[k] + inp.teml


class Calc_ET0_V1(modeltools.Method):
    """Calculate reference evapotranspiration after Turc-Wendling.

    Basic equation:
      :math:`ET0 = KE \\cdot
      \\frac{(8.64 \\cdot Glob+93 \\cdot KF) \\cdot (TKor+22)}
      {165 \\cdot (TKor+123) \\cdot (1 + 0.00019 \\cdot min(HNN, 600))}`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> simulationstep('12h')
        >>> nhru(3)
        >>> ke(1.1)
        >>> kf(0.6)
        >>> hnn(200.0, 600.0, 1000.0)
        >>> inputs.glob = 200.0
        >>> fluxes.tkor = 15.0
        >>> model.calc_et0_v1()
        >>> fluxes.et0
        et0(3.07171, 2.86215, 2.86215)
    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.KE,
        lland_control.KF,
        lland_control.HNN,
    )
    REQUIREDSEQUENCES = (
        lland_inputs.Glob,
        lland_fluxes.TKor,
    )
    RESULTSEQUENCES = (
        lland_fluxes.ET0,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.et0[k] = (con.ke[k]*(((8.64*inp.glob+93.*con.kf[k]) *
                                      (flu.tkor[k]+22.)) /
                                     (165.*(flu.tkor[k]+123.) *
                                      (1.+0.00019*min(con.hnn[k], 600.)))))


class Calc_ET0_WET0_V1(modeltools.Method):
    """Correct the given reference evapotranspiration and update the
    corresponding log sequence.

    Basic equation:
      :math:`ET0_{new} = WfET0 \\cdot KE \\cdot PET +
      (1-WfET0) \\cdot ET0_{alt}`

    Example:

        Prepare four hydrological response units with different value
        combinations of parameters |KE| and |WfET0|:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> simulationstep('12h')
        >>> nhru(4)
        >>> ke(0.8, 1.2, 0.8, 1.2)
        >>> wfet0(2.0, 2.0, 0.2, 0.2)

        Note that the actual value of time dependend parameter |WfET0|
        is reduced due the difference between the given parameter and
        simulation time steps:

        >>> from hydpy import round_
        >>> round_(wfet0.values)
        1.0, 1.0, 0.1, 0.1

        For the first two hydrological response units, the given |PET|
        value is modified by -0.4 mm and +0.4 mm, respectively.  For the
        other two response units, which weight the "new" evaporation
        value with 10 %, |ET0| does deviate from the old value of |WET0|
        by -0.04 mm and +0.04 mm only:

        >>> inputs.pet = 2.0
        >>> logs.wet0 = 2.0
        >>> model.calc_et0_wet0_v1()
        >>> fluxes.et0
        et0(1.6, 2.4, 1.96, 2.04)
        >>> logs.wet0
        wet0([[1.6, 2.4, 1.96, 2.04]])
    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.WfET0,
        lland_control.KE,
    )
    REQUIREDSEQUENCES = (
        lland_inputs.PET,
    )
    UPDATEDSEQUENCES = (
        lland_logs.WET0,
    )
    RESULTSEQUENCES = (
        lland_fluxes.ET0,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        for k in range(con.nhru):
            flu.et0[k] = (con.wfet0[k]*con.ke[k]*inp.pet +
                          (1.-con.wfet0[k])*log.wet0[0, k])
            log.wet0[0, k] = flu.et0[k]


class Calc_EvPo_V1(modeltools.Method):
    """Calculate land use and month specific values of potential
    evapotranspiration.

    Additional requirements:
      |Model.idx_sim|

    Basic equation:
      :math:`EvPo = FLn \\cdot ET0`

    Example:

        For clarity, this is more of a kind of an integration example.
        Parameter |FLn| both depends on time (the actual month) and space
        (the actual land use).  Firstly, let us define a initialization
        time period spanning the transition from June to July:

        >>> from hydpy import pub
        >>> pub.timegrids = '30.06.2000', '02.07.2000', '1d'

        Secondly, assume that the considered subbasin is differenciated in
        two HRUs, one of primarily consisting of arable land and the other
        one of deciduous forests:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(2)
        >>> lnk(ACKER, LAUBW)

        Thirdly, set the |FLn|
        values, one for the relevant months and land use classes:

        >>> fln.acker_jun = 1.299
        >>> fln.acker_jul = 1.304
        >>> fln.laubw_jun = 1.350
        >>> fln.laubw_jul = 1.365

        Fourthly, the index array connecting the simulation time steps
        defined above and the month indexes (0...11) can be retrieved
        from the |pub| module.  This can be done manually more
        conveniently via its update method:

        >>> derived.moy.update()
        >>> derived.moy
        moy(5, 6)

        Finally, the actual method (with its simple equation) is applied
        as usual:

        >>> fluxes.et0 = 2.0
        >>> model.idx_sim = 0
        >>> model.calc_evpo_v1()
        >>> fluxes.evpo
        evpo(2.598, 2.7)
        >>> model.idx_sim = 1
        >>> model.calc_evpo_v1()
        >>> fluxes.evpo
        evpo(2.608, 2.73)

        Reset module |pub| to not interfere the following examples:

        >>> del pub.timegrids
    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.FLn,
    )
    DERIVEDPARAMETERS = (
        lland_derived.MOY,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.ET0,
    )
    RESULTSEQUENCES = (
        lland_fluxes.EvPo,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            flu.evpo[k] = \
                con.fln[con.lnk[k]-1, der.moy[model.idx_sim]] * flu.et0[k]


class Calc_NBes_Inzp_V1(modeltools.Method):
    """Calculate stand precipitation and update the interception storage
    accordingly.

    Additional requirements:
      |Model.idx_sim|

    Basic equation:
      :math:`NBes = \\Bigl \\lbrace
      {
      {PKor \\ | \\ Inzp = KInz}
      \\atop
      {0 \\ | \\ Inzp < KInz}
      }`

    Examples:

        Initialize five HRUs with different land usages:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(5)
        >>> lnk(SIED_D, FEUCHT, GLETS, FLUSS, SEE)

        Define |KInz| values for July the selected land usages directly:

        >>> derived.kinz.sied_d_jul = 2.0
        >>> derived.kinz.feucht_jul = 1.0
        >>> derived.kinz.glets_jul = 0.0
        >>> derived.kinz.fluss_jul = 1.0
        >>> derived.kinz.see_jul = 1.0

        Now we prepare a |MOY| object, that assumes that the first, second,
        and third simulation time steps are in June, July, and August
        respectively (we make use of the value defined above for July, but
        setting the values of parameter |MOY| this way allows for a more
        rigorous testing of proper indexing):

        >>> derived.moy.shape = 3
        >>> derived.moy = 5, 6, 7
        >>> model.idx_sim = 1

        The dense settlement (|SIED_D|), the wetland area (|FEUCHT|), and
        both water areas (|FLUSS| and |SEE|) start with a initial interception
        storage of 1/2 mm, the glacier (|GLETS|) and water areas (|FLUSS| and
        |SEE|) start with 0 mm.  In the first example, actual precipition
        is 1 mm:

        >>> states.inzp = 0.5, 0.5, 0.0, 1.0, 1.0
        >>> fluxes.nkor = 1.0
        >>> model.calc_nbes_inzp_v1()
        >>> states.inzp
        inzp(1.5, 1.0, 0.0, 0.0, 0.0)
        >>> fluxes.nbes
        nbes(0.0, 0.5, 1.0, 0.0, 0.0)

        Only for the settled area, interception capacity is not exceeded,
        meaning no stand precipitation occurs.  Note that it is common in
        define zero interception capacities for glacier areas, but not
        mandatory.  Also note that the |KInz|, |Inzp| and |NKor| values
        given for both water areas are ignored completely, and |Inzp|
        and |NBes| are simply set to zero.

        If there is no precipitation, there is of course also no stand
        precipitation and interception storage remains unchanged:

        >>> states.inzp = 0.5, 0.5, 0.0, 0.0, 0.0
        >>> fluxes.nkor = 0.
        >>> model.calc_nbes_inzp_v1()
        >>> states.inzp
        inzp(0.5, 0.5, 0.0, 0.0, 0.0)
        >>> fluxes.nbes
        nbes(0.0, 0.0, 0.0, 0.0, 0.0)

        Interception capacities change discontinuously between consecutive
        months.  This can result in little stand precipitation events in
        periods without precipitation:

        >>> states.inzp = 1.0, 0.0, 0.0, 0.0, 0.0
        >>> derived.kinz.sied_d_jul = 0.6
        >>> fluxes.nkor = 0.0
        >>> model.calc_nbes_inzp_v1()
        >>> states.inzp
        inzp(0.6, 0.0, 0.0, 0.0, 0.0)
        >>> fluxes.nbes
        nbes(0.4, 0.0, 0.0, 0.0, 0.0)
    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
    )
    DERIVEDPARAMETERS = (
        lland_derived.MOY,
        lland_derived.KInz,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.NKor,
    )
    UPDATEDSEQUENCES = (
        lland_states.Inzp,
    )
    RESULTSEQUENCES = (
        lland_fluxes.NBes,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (WASSER, FLUSS, SEE):
                flu.nbes[k] = 0.
                sta.inzp[k] = 0.
            else:
                flu.nbes[k] = \
                    max(flu.nkor[k]+sta.inzp[k] -
                        der.kinz[con.lnk[k]-1, der.moy[model.idx_sim]], 0.)
                sta.inzp[k] += flu.nkor[k]-flu.nbes[k]


class Calc_EvI_Inzp_V1(modeltools.Method):
    """Calculate interception evaporation and update the interception
    storage accordingly.

    Basic equation:
      :math:`EvI = \\Bigl \\lbrace
      {
      {EvPo \\ | \\ Inzp > 0}
      \\atop
      {0 \\ | \\ Inzp = 0}
      }`

    Examples:

        Initialize five HRUs with different combinations of land usage
        and initial interception storage and apply a value of potential
        evaporation of 3 mm on each one:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(5)
        >>> lnk(FLUSS, SEE, ACKER, ACKER, ACKER)
        >>> states.inzp = 2.0, 2.0, 0.0, 2.0, 4.0
        >>> fluxes.evpo = 3.0
        >>> model.calc_evi_inzp_v1()
        >>> states.inzp
        inzp(0.0, 0.0, 0.0, 0.0, 1.0)
        >>> fluxes.evi
        evi(3.0, 3.0, 0.0, 2.0, 3.0)

        For arable land (|ACKER|) and most other land types, interception
        evaporation (|EvI|) is identical with potential evapotranspiration
        (|EvPo|), as long as it is met by available intercepted water
        ([Inzp|).  Only water areas (|FLUSS| and |SEE|),  |EvI| is
        generally equal to |EvPo| (but this might be corrected by a method
        called after |Calc_EvI_Inzp_V1| has been applied) and [Inzp| is
        set to zero.
    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.EvPo,
    )
    UPDATEDSEQUENCES = (
        lland_states.Inzp,
    )
    RESULTSEQUENCES = (
        lland_fluxes.EvI,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (WASSER, FLUSS, SEE):
                flu.evi[k] = flu.evpo[k]
                sta.inzp[k] = 0.
            else:
                flu.evi[k] = min(flu.evpo[k], sta.inzp[k])
                sta.inzp[k] -= flu.evi[k]


class Calc_SBes_V1(modeltools.Method):
    """Calculate the frozen part of stand precipitation.

    Examples:

        In the first example, the threshold temperature of seven hydrological
        response units is 0 °C and the corresponding temperature interval of
        mixed precipitation 2 °C:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(7)
        >>> tgr(0.0)
        >>> tsp(2.0)

        The value of |NBes| is zero above 1 °C and equal to the value of
        |NBes| below -1 °C.  Between these temperature values, |NBes|
        decreases linearly:

        >>> fluxes.nbes = 4.0
        >>> fluxes.tkor = -10.0, -1.0, -0.5, 0.0, 0.5, 1.0, 10.0
        >>> model.calc_sbes_v1()
        >>> fluxes.sbes
        sbes(4.0, 4.0, 3.0, 2.0, 1.0, 0.0, 0.0)

        Note the special case of a zero temperature interval.  With the
        actual temperature being equal to the threshold temperature, the
        the value of `sbes` is zero:

        >>> tsp(0.)
        >>> model.calc_sbes_v1()
        >>> fluxes.sbes
        sbes(4.0, 4.0, 4.0, 0.0, 0.0, 0.0, 0.0)
    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.TGr,
        lland_control.TSp,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.NBes,
    )
    RESULTSEQUENCES = (
        lland_fluxes.SBes,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            if flu.nbes[k] <= 0.:
                flu.sbes[k] = 0.
            elif flu.tkor[k] >= (con.tgr[k]+con.tsp[k]/2.):
                flu.sbes[k] = 0.
            elif flu.tkor[k] <= (con.tgr[k]-con.tsp[k]/2.):
                flu.sbes[k] = flu.nbes[k]
            else:
                flu.sbes[k] = ((((con.tgr[k]+con.tsp[k]/2.)-flu.tkor[k]) /
                                con.tsp[k])*flu.nbes[k])


class Calc_WGTF_V1(modeltools.Method):
    """Calculate the potential snowmelt.

    Basic equation:
      :math:`WGTF = max(GTF \\cdot (TKor - TRefT), 0) +
      max(\\frac{CPWasser}{RSchmelz} \\cdot (TKor - TRefN), 0)`

    Examples:

        Initialize seven HRUs with identical degree-day factors and
        temperature thresholds, but different combinations of land use
        and air temperature:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> simulationstep('12h')
        >>> nhru(7)
        >>> lnk(ACKER, LAUBW, FLUSS, SEE, ACKER, ACKER, ACKER)
        >>> gtf(5.0)
        >>> treft(0.0)
        >>> trefn(1.0)
        >>> fluxes.tkor = 2.0, 2.0, 2.0, 2.0, -1.0, 0.0, 1.0

        Compared to most other LARSIM parameters, the specific heat capacity
        and melt heat capacity of water can be seen as fixed properties:

        >>> cpwasser(4.1868)
        >>> rschmelz(334.0)

        Note that the values of the degree-day factor are only half
        as much as the given value, due to the simulation step size
        being only half as long as the parameter step size:

        >>> gtf
        gtf(5.0)
        >>> gtf.values
        array([ 2.5,  2.5,  2.5,  2.5,  2.5,  2.5,  2.5])

        After performing the calculation, one can see that the potential
        melting rate is identical for the first two HRUs (|ACKER| and
        |LAUBW|).  The land use class results in no difference, except for
        water areas (third and forth HRU, |FLUSS| and |SEE|), where no
        potential melt needs to be calculated.  The last three HRUs (again
        |ACKER|) show the usual behaviour of the degree day method, when the
        actual temperature is below (fourth HRU), equal to (fifth HRU) or
        above (sixths zone) the threshold temperature.  Additionally, the
        first two zones show the influence of the additional energy intake
        due to "warm" precipitation.  Obviously, this additional term is
        quite negligible for common parameterizations, even if lower
        values for the separate threshold temperature |TRefT| would be
        taken into account:

        >>> model.calc_wgtf_v1()
        >>> fluxes.wgtf
        wgtf(5.012535, 5.012535, 0.0, 0.0, 0.0, 0.0, 2.5)
    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.GTF,
        lland_control.TRefT,
        lland_control.CPWasser,
        lland_control.RSchmelz,
        lland_control.TRefN,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.TKor,
    )
    RESULTSEQUENCES = (
        lland_fluxes.WGTF,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (WASSER, FLUSS, SEE):
                flu.wgtf[k] = 0.
            else:
                flu.wgtf[k] = (
                    max(con.gtf[k]*(flu.tkor[k]-con.treft[k]), 0) +
                    max(con.cpwasser/con.rschmelz*(flu.tkor[k]-con.trefn[k]),
                        0.))


class Calc_Schm_WATS_V1(modeltools.Method):
    """Calculate the actual amount of water melting within the snow cover.

    Basic equations:
      :math:`\\frac{dWATS}{dt}  = SBes - Schm`

      :math:`Schm = \\Bigl \\lbrace
      {
      {WGTF \\ | \\ WATS > 0}
      \\atop
      {0 \\ | \\ WATS = 0}
      }`

    Examples:

        Initialize two water (|FLUSS| and |SEE|) and four arable land
        (|ACKER|) HRUs.  Assume the same values for the initial amount
        of frozen water (|WATS|) and the frozen part of stand precipitation
        (|SBes|), but different values for potential snowmelt (|WGTF|):

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(6)
        >>> lnk(FLUSS, SEE, ACKER, ACKER, ACKER, ACKER)
        >>> states.wats = 2.0
        >>> fluxes.sbes = 1.0
        >>> fluxes.wgtf = 1.0, 1.0, 0.0, 1.0, 3.0, 5.0
        >>> model.calc_schm_wats_v1()
        >>> states.wats
        wats(0.0, 0.0, 3.0, 2.0, 0.0, 0.0)
        >>> fluxes.schm
        schm(0.0, 0.0, 0.0, 1.0, 3.0, 3.0)

        For the water areas, both the frozen amount of water and actual melt
        are set to zero.  For all other land use classes, actual melt
        is either limited by potential melt or the available frozen water,
        which is the sum of initial frozen water and the frozen part
        of stand precipitation.
    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.SBes,
        lland_fluxes.WGTF,
    )
    UPDATEDSEQUENCES = (
        lland_states.WATS,
    )
    RESULTSEQUENCES = (
        lland_fluxes.Schm,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (WASSER, FLUSS, SEE):
                sta.wats[k] = 0.
                flu.schm[k] = 0.
            else:
                sta.wats[k] += flu.sbes[k]
                flu.schm[k] = min(flu.wgtf[k], sta.wats[k])
                sta.wats[k] -= flu.schm[k]


class Calc_WaDa_WAeS_V1(modeltools.Method):
    """Calculate the actual water release from the snow cover.

    Basic equations:
      :math:`\\frac{dWAeS}{dt} = NBes - WaDa`

      :math:`WAeS \\leq PWMax \\cdot WATS`

    Examples:

        For simplicity, the threshold parameter |PWMax| is set to a value
        of two for each of the six initialized HRUs.  Thus, snow cover can
        hold as much liquid water as it contains frozen water.  Stand
        precipitation is also always set to the same value, but the initial
        conditions of the snow cover are varied:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(6)
        >>> lnk(FLUSS, SEE, ACKER, ACKER, ACKER, ACKER)
        >>> pwmax(2.0)
        >>> fluxes.nbes = 1.0
        >>> states.wats = 0.0, 0.0, 0.0, 1.0, 1.0, 1.0
        >>> states.waes = 1.0, 1.0, 0.0, 1.0, 1.5, 2.0
        >>> model.calc_wada_waes_v1()
        >>> states.waes
        waes(0.0, 0.0, 0.0, 2.0, 2.0, 2.0)
        >>> fluxes.wada
        wada(1.0, 1.0, 1.0, 0.0, 0.5, 1.0)

        Note the special cases of the first two HRUs of type |FLUSS| and
        |SEE|.  For water areas, stand precipitaton |NBes| is generally
        passed to |WaDa| and |WAeS| is set to zero.  For all other land
        use classes (of which only |ACKER| is selected), only the amount
        of |NBes| exceeding the actual snow holding capacity is passed
        to |WaDa|.
    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.PWMax,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.NBes,
        lland_states.WATS,
    )
    UPDATEDSEQUENCES = (
        lland_states.WAeS,
    )
    RESULTSEQUENCES = (
        lland_fluxes.WaDa,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (WASSER, FLUSS, SEE):
                sta.waes[k] = 0.
                flu.wada[k] = flu.nbes[k]
            else:
                sta.waes[k] += flu.nbes[k]
                flu.wada[k] = max(sta.waes[k]-con.pwmax[k]*sta.wats[k], 0.)
                sta.waes[k] -= flu.wada[k]


class Calc_EvB_V1(modeltools.Method):
    """Calculate the actual water release from the snow cover.

    Basic equations:
      :math:`temp = exp(-GrasRef_R \\cdot \\frac{BoWa}{WMax})`

      :math:`EvB = (EvPo - EvI) \\cdot
      \\frac{1 - temp}{1 + temp -2 \\cdot exp(-GrasRef_R)}`

    Examples:

        Soil evaporation is calculated neither for water nor for sealed
        areas (see the first three HRUs of type |FLUSS|, |SEE|, and |VERS|).
        All other land use classes are handled in accordance with a
        recommendation of the set of codes described in ATV-DVWK-M 504
        (arable land |ACKER| has been selected for the last four HRUs
        arbitrarily):

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(7)
        >>> lnk(FLUSS, SEE, VERS, ACKER, ACKER, ACKER, ACKER)
        >>> grasref_r(5.0)
        >>> wmax(100.0, 100.0, 100.0, 0.0, 100.0, 100.0, 100.0)
        >>> fluxes.evpo = 5.0
        >>> fluxes.evi = 3.0
        >>> states.bowa = 50.0, 50.0, 50.0, 0.0, 0.0, 50.0, 100.0
        >>> model.calc_evb_v1()
        >>> fluxes.evb
        evb(0.0, 0.0, 0.0, 0.0, 0.0, 1.717962, 2.0)

        In case maximum soil water storage (|WMax|) is zero, soil evaporation
        (|EvB|) is generally set to zero (see the forth HRU).  The last
        three HRUs demonstrate the rise in soil evaporation with increasing
        soil moisture, which is lessening in the high soil moisture range.
    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.WMax,
        lland_control.GrasRef_R,
    )
    REQUIREDSEQUENCES = (
        lland_states.BoWa,
        lland_fluxes.EvPo,
        lland_fluxes.EvI,
    )
    RESULTSEQUENCES = (
        lland_fluxes.EvB,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if (con.lnk[k] in (VERS, WASSER, FLUSS, SEE)) or \
                    (con.wmax[k] <= 0.):
                flu.evb[k] = 0.
            else:
                d_temp = modelutils.exp(-con.grasref_r *
                                        sta.bowa[k]/con.wmax[k])
                flu.evb[k] = ((flu.evpo[k]-flu.evi[k]) * (1.-d_temp) /
                              (1.+d_temp-2.*modelutils.exp(-con.grasref_r)))


class Calc_QBB_V1(modeltools.Method):
    """Calculate the amount of base flow released from the soil.

    Basic equations:
      :math:`Beta_{eff} = \\Bigl \\lbrace
      {
      {Beta \\ | \\ BoWa \\leq FK}
      \\atop
      {Beta \\cdot (1+(FBeta-1)\\cdot\\frac{BoWa-FK}{WMax-FK}) \\|\\ BoWa > FK}
      }`

      :math:`QBB = \\Bigl \\lbrace
      {
      {0 \\ | \\ BoWa \\leq PWP}
      \\atop
      {Beta_{eff}  \\cdot (BoWa - PWP) \\|\\ BoWa > PWP}
      }`

    Examples:

        For water and sealed areas, no base flow is calculated (see the
        first three HRUs of type |VERS|, |FLUSS|, and |SEE|).  No principal
        distinction is made between the remaining land use classes (arable
        land |ACKER| has been selected for the last five HRUs arbitrarily):

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> simulationstep('12h')
        >>> nhru(8)
        >>> lnk(FLUSS, SEE, VERS, ACKER, ACKER, ACKER, ACKER, ACKER)
        >>> beta(0.04)
        >>> fbeta(2.0)
        >>> wmax(100.0, 100.0, 100.0, 0.0, 100.0, 100.0, 100.0, 200.0)
        >>> pwp(10.0)
        >>> fk(70.0)

        Note the time dependence of parameter |Beta|:

        >>> beta
        beta(0.04)
        >>> beta.values
        array([ 0.02,  0.02,  0.02,  0.02,  0.02,  0.02,  0.02,  0.02])

        In the first example, the actual soil water content |BoWa| is set
        to low values.  For values below the threshold |PWP|, no percolation
        occurs.  Above |PWP| (but below |FK|), |QBB| increases linearly by
        an amount defined by parameter |Beta|:

        >>> states.bowa = 20.0, 20.0, 20.0, 0.0, 0.0, 10.0, 20.0, 20.0
        >>> model.calc_qbb_v1()
        >>> fluxes.qbb
        qbb(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.2, 0.2)

        Note that for the last two HRUs the same amount of
        base flow generation is determined, in spite of the fact
        that both exhibit different relative soil moistures.  It is
        common to modify this "pure absolute dependency" to a "mixed
        absolute/relative dependency" through defining the values of
        parameter |PWP| indirectly via a relative parameter |PWP|.

        In the second example, the actual soil water content |BoWa| is set
        to high values.  For values below threshold |FK|, the discussion above
        remains valid.  For values above |FK|, percolation shows a nonlinear
        behaviour when factor |FBeta| is set to values larger than one:

        >>> wmax(0.0, 0.0, 0.0, 100.0, 100.0, 100.0, 100.0, 200.0)
        >>> states.bowa = 0.0, 0.0, 0.0, 60.0, 70.0, 80.0, 100.0, 200.0
        >>> model.calc_qbb_v1()
        >>> fluxes.qbb
        qbb(0.0, 0.0, 0.0, 1.0, 1.2, 1.866667, 3.6, 7.6)
    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.WMax,
        lland_control.Beta,
        lland_control.FBeta,
        lland_control.PWP,
        lland_control.FK,
    )
    REQUIREDSEQUENCES = (
        lland_states.BoWa,
    )
    RESULTSEQUENCES = (
        lland_fluxes.QBB,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if ((con.lnk[k] in (VERS, WASSER, FLUSS, SEE)) or
                    (sta.bowa[k] <= con.pwp[k]) or (con.wmax[k] <= 0.)):
                flu.qbb[k] = 0.
            elif sta.bowa[k] <= con.fk[k]:
                flu.qbb[k] = con.beta[k]*(sta.bowa[k]-con.pwp[k])
            else:
                flu.qbb[k] = (con.beta[k]*(sta.bowa[k]-con.pwp[k]) *
                              (1.+(con.fbeta[k]-1.)*((sta.bowa[k]-con.fk[k]) /
                                                     (con.wmax[k]-con.fk[k]))))


class Calc_QIB1_V1(modeltools.Method):
    """Calculate the first inflow component released from the soil.

    Basic equation:
      :math:`QIB1 = DMin \\cdot \\frac{BoWa}{WMax}`

    Examples:

        For water and sealed areas, no interflow is calculated (the first
        three HRUs are of type |FLUSS|, |SEE|, and |VERS|, respectively).
        No principal distinction is made between the remaining land use
        classes (arable land |ACKER| has been selected for the last five
        HRUs arbitrarily):

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> simulationstep('12h')
        >>> nhru(8)
        >>> lnk(FLUSS, SEE, VERS, ACKER, ACKER, ACKER, ACKER, ACKER)
        >>> dmax(10.0)
        >>> dmin(4.0)
        >>> wmax(101.0, 101.0, 101.0, 0.0, 101.0, 101.0, 101.0, 202.0)
        >>> pwp(10.0)
        >>> states.bowa = 10.1, 10.1, 10.1, 0.0, 0.0, 10.0, 10.1, 10.1

        Note the time dependence of parameter |DMin|:

        >>> dmin
        dmin(4.0)
        >>> dmin.values
        array([ 2.,  2.,  2.,  2.,  2.,  2.,  2.,  2.])

        Compared to the calculation of |QBB|, the following results show
        some relevant differences:

        >>> model.calc_qib1_v1()
        >>> fluxes.qib1
        qib1(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.2, 0.1)

        Firstly, as demonstrated with the help of the seventh and the
        eight HRU, the generation of the first interflow component |QIB1|
        depends on relative soil moisture.  Secondly, as demonstrated with
        the help the sixth and seventh HRU, it starts abruptly whenever
        the slightest exceedance of the threshold  parameter |PWP| occurs.
        Such sharp discontinuouties are a potential source of trouble.
    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.DMin,
        lland_control.WMax,
        lland_control.PWP,
    )
    REQUIREDSEQUENCES = (
        lland_states.BoWa,
    )
    RESULTSEQUENCES = (
        lland_fluxes.QIB1,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if ((con.lnk[k] in (VERS, WASSER, FLUSS, SEE)) or
                    (sta.bowa[k] <= con.pwp[k])):
                flu.qib1[k] = 0.
            else:
                flu.qib1[k] = con.dmin[k]*(sta.bowa[k]/con.wmax[k])


class Calc_QIB2_V1(modeltools.Method):
    """Calculate the first inflow component released from the soil.

    Basic equation:
      :math:`QIB2 = (DMax-DMin) \\cdot
      (\\frac{BoWa-FK}{WMax-FK})^\\frac{3}{2}`

    Examples:

        For water and sealed areas, no interflow is calculated (the first
        three HRUs are of type |FLUSS|, |SEE|, and |VERS|, respectively).
        No principal distinction is made between the remaining land use
        classes (arable land |ACKER| has been selected for the last
        five HRUs arbitrarily):

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> simulationstep('12h')
        >>> nhru(8)
        >>> lnk(FLUSS, SEE, VERS, ACKER, ACKER, ACKER, ACKER, ACKER)
        >>> dmax(10.0)
        >>> dmin(4.0)
        >>> wmax(100.0, 100.0, 100.0, 50.0, 100.0, 100.0, 100.0, 200.0)
        >>> fk(50.0)
        >>> states.bowa = 100.0, 100.0, 100.0, 50.1, 50.0, 75.0, 100.0, 100.0

        Note the time dependence of parameters |DMin| (see the example above)
        and |DMax|:

        >>> dmax
        dmax(10.0)
        >>> dmax.values
        array([ 5.,  5.,  5.,  5.,  5.,  5.,  5.,  5.])

        The following results show that he calculation of |QIB2| both
        resembles those of |QBB| and |QIB1| in some regards:

        >>> model.calc_qib2_v1()
        >>> fluxes.qib2
        qib2(0.0, 0.0, 0.0, 0.0, 0.0, 1.06066, 3.0, 0.57735)

        In the given example, the maximum rate of total interflow
        generation is 5 mm/12h (parameter |DMax|).  For the seventh zone,
        which contains a saturated soil, the value calculated for the
        second interflow component (|QIB2|) is 3 mm/h.  The "missing"
        value of 2 mm/12h is be calculated by method |Calc_QIB1_V1|.

        (The fourth zone, which is slightly oversaturated, is only intended
        to demonstrate that zero division due to |WMax| = |FK| is circumvented.)
    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.WMax,
        lland_control.DMax,
        lland_control.DMin,
        lland_control.FK,
    )
    REQUIREDSEQUENCES = (
        lland_states.BoWa,
    )
    RESULTSEQUENCES = (
        lland_fluxes.QIB1,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nhru):
            if ((con.lnk[k] in (VERS, WASSER, FLUSS, SEE)) or
                    (sta.bowa[k] <= con.fk[k]) or (con.wmax[k] <= con.fk[k])):
                flu.qib2[k] = 0.
            else:
                flu.qib2[k] = ((con.dmax[k]-con.dmin[k]) *
                               ((sta.bowa[k]-con.fk[k]) /
                                (con.wmax[k]-con.fk[k]))**1.5)


class Calc_QDB_V1(modeltools.Method):
    """Calculate direct runoff released from the soil.

    Basic equations:
      :math:`QDB = \\Bigl \\lbrace
      {
      {max(Exz, 0) \\ | \\ SfA \\leq 0}
      \\atop
      {max(Exz + WMax \\cdot SfA^{BSf+1}, 0) \\ | \\ SfA > 0}
      }`

      :math:`SFA = (1 - \\frac{BoWa}{WMax})^\\frac{1}{BSf+1} -
      \\frac{WaDa}{(BSf+1) \\cdot WMax}`

      :math:`Exz = (BoWa + WaDa) - WMax`

    Examples:

        For water areas (|FLUSS| and |SEE|), sealed areas (|VERS|), and
        areas without any soil storage capacity, all water is completely
        routed as direct runoff |QDB| (see the first four HRUs).  No
        principal distinction is made between the remaining land use
        classes (arable land |ACKER| has been selected for the last five
        HRUs arbitrarily):

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> simulationstep('12h')
        >>> nhru(9)
        >>> lnk(FLUSS, SEE, VERS, ACKER, ACKER, ACKER, ACKER, ACKER, ACKER)
        >>> bsf(0.4)
        >>> wmax(100.0, 100.0, 100.0, 0.0, 100.0, 100.0, 100.0, 100.0, 100.0)
        >>> fluxes.wada = 10.0
        >>> states.bowa = (
        ...     100.0, 100.0, 100.0, 0.0, -0.1, 0.0, 50.0, 100.0, 100.1)
        >>> model.calc_qdb_v1()
        >>> fluxes.qdb
        qdb(10.0, 10.0, 10.0, 10.0, 0.142039, 0.144959, 1.993649, 10.0, 10.1)

        With the common |BSf| value of 0.4, the discharge coefficient
        increases more or less exponentially with soil moisture.
        For soil moisture values slightly below zero or above usable
        field capacity, plausible amounts of generated direct runoff
        are ensured.
    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.WMax,
        lland_control.BSf,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.WaDa,
        lland_states.BoWa,
    )
    RESULTSEQUENCES = (
        lland_aides.SfA,
        lland_aides.Exz,
        lland_fluxes.QDB,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        aid = model.sequences.aides.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] == WASSER:
                flu.qdb[k] = 0.
            elif ((con.lnk[k] in (VERS, FLUSS, SEE)) or
                  (con.wmax[k] <= 0.)):
                flu.qdb[k] = flu.wada[k]
            else:
                if sta.bowa[k] < con.wmax[k]:
                    aid.sfa[k] = (
                        (1.-sta.bowa[k]/con.wmax[k])**(1./(con.bsf[k]+1.)) -
                        (flu.wada[k]/((con.bsf[k]+1.)*con.wmax[k])))
                else:
                    aid.sfa[k] = 0.
                aid.exz[k] = sta.bowa[k]+flu.wada[k]-con.wmax[k]
                flu.qdb[k] = aid.exz[k]
                if aid.sfa[k] > 0.:
                    flu.qdb[k] += aid.sfa[k]**(con.bsf[k]+1.)*con.wmax[k]
                flu.qdb[k] = max(flu.qdb[k], 0.)


class Calc_BoWa_V1(modeltools.Method):
    """Update soil moisture and correct fluxes if necessary.

    Basic equations:
       :math:`\\frac{dBoWa}{dt} = WaDa - EvB - QBB - QIB1 - QIB2 - QDB`

       :math:`BoWa \\geq 0`

    Examples:

        For water areas (|FLUSS| and |SEE|) and sealed areas (|VERS|),
        soil moisture |BoWa| is simply set to zero and no flux correction
        are performed (see the first three HRUs).  No principal distinction
        is made between the remaining land use classes (arable land |ACKER|
        has been selected for the last four HRUs arbitrarily):

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(7)
        >>> lnk(FLUSS, SEE, VERS, ACKER, ACKER, ACKER, ACKER)
        >>> states.bowa = 2.0
        >>> fluxes.wada = 1.0
        >>> fluxes.evb = 1.0, 1.0, 1.0, 0.0, 0.1, 0.2, 0.3
        >>> fluxes.qbb = 1.0, 1.0, 1.0, 0.0, 0.2, 0.4, 0.6
        >>> fluxes.qib1 = 1.0, 1.0, 1.0, 0.0, 0.3, 0.6, 0.9
        >>> fluxes.qib2 = 1.0, 1.0, 1.0, 0.0, 0.4, 0.8, 1.2
        >>> fluxes.qdb = 1.0, 1.0, 1.0, 0.0, 0.5, 1.0, 1.5
        >>> model.calc_bowa_v1()
        >>> states.bowa
        bowa(0.0, 0.0, 0.0, 3.0, 1.5, 0.0, 0.0)
        >>> fluxes.evb
        evb(1.0, 1.0, 1.0, 0.0, 0.1, 0.2, 0.2)
        >>> fluxes.qbb
        qbb(1.0, 1.0, 1.0, 0.0, 0.2, 0.4, 0.4)
        >>> fluxes.qib1
        qib1(1.0, 1.0, 1.0, 0.0, 0.3, 0.6, 0.6)
        >>> fluxes.qib2
        qib2(1.0, 1.0, 1.0, 0.0, 0.4, 0.8, 0.8)
        >>> fluxes.qdb
        qdb(1.0, 1.0, 1.0, 0.0, 0.5, 1.0, 1.0)

        For the seventh HRU, the original total loss terms would result in a
        negative soil moisture value.  Hence it is reduced to the total loss
        term of the sixt HRU, which results exactly in a complete emptying
        of the soil storage.
    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.WaDa,
    )
    UPDATEDSEQUENCES = (
        lland_states.BoWa,
        lland_fluxes.EvB,
        lland_fluxes.QBB,
        lland_fluxes.QIB1,
        lland_fluxes.QIB2,
        lland_fluxes.QDB,
    )
    RESULTSEQUENCES = (
        lland_aides.BVl,
        lland_aides.MVl,
        lland_aides.RVl,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        aid = model.sequences.aides.fastaccess
        for k in range(con.nhru):
            if con.lnk[k] in (VERS, WASSER, FLUSS, SEE):
                sta.bowa[k] = 0.
            else:
                aid.bvl[k] = (
                    flu.evb[k]+flu.qbb[k]+flu.qib1[k]+flu.qib2[k]+flu.qdb[k])
                aid.mvl[k] = sta.bowa[k]+flu.wada[k]
                if aid.bvl[k] > aid.mvl[k]:
                    aid.rvl[k] = aid.mvl[k]/aid.bvl[k]
                    flu.evb[k] *= aid.rvl[k]
                    flu.qbb[k] *= aid.rvl[k]
                    flu.qib1[k] *= aid.rvl[k]
                    flu.qib2[k] *= aid.rvl[k]
                    flu.qdb[k] *= aid.rvl[k]
                    sta.bowa[k] = 0.
                else:
                    sta.bowa[k] = aid.mvl[k]-aid.bvl[k]


class Calc_QBGZ_V1(modeltools.Method):
    """Aggregate the amount of base flow released by all "soil type" HRUs
    and the "net precipitation" above water areas of type |SEE|.

    Water areas of type |SEE| are assumed to be directly connected with
    groundwater, but not with the stream network.  This is modelled by
    adding their (positive or negative) "net input" (|NKor|-|EvI|) to the
    "percolation output" of the soil containing HRUs.

    Basic equation:
       :math:`QBGZ = \\Sigma(FHRU \\cdot QBB) +
       \\Sigma(FHRU \\cdot (NKor_{SEE}-EvI_{SEE}))`

    Examples:

        The first example shows that |QBGZ| is the area weighted sum of
        |QBB| from "soil type" HRUs like arable land (|ACKER|) and of
        |NKor|-|EvI| from water areas of type |SEE|.  All other water
        areas (|WASSER| and |FLUSS|) and also sealed surfaces (|VERS|)
        have no impact on |QBGZ|:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(6)
        >>> lnk(ACKER, ACKER, VERS, WASSER, FLUSS, SEE)
        >>> fhru(0.1, 0.2, 0.1, 0.1, 0.1, 0.4)
        >>> fluxes.qbb = 2., 4.0, 300.0, 300.0, 300.0, 300.0
        >>> fluxes.nkor = 200.0, 200.0, 200.0, 200.0, 200.0, 20.0
        >>> fluxes.evi = 100.0, 100.0, 100.0, 100.0, 100.0, 10.0
        >>> model.calc_qbgz_v1()
        >>> states.qbgz
        qbgz(5.0)

        The second example shows that large evaporation values above a
        HRU of type |SEE| can result in negative values of |QBGZ|:

        >>> fluxes.evi[5] = 30
        >>> model.calc_qbgz_v1()
        >>> states.qbgz
        qbgz(-3.0)
    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.FHRU,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.NKor,
        lland_fluxes.EvI,
        lland_fluxes.QBB,
    )
    RESULTSEQUENCES = (
        lland_states.QBGZ,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        sta.qbgz = 0.
        for k in range(con.nhru):
            if con.lnk[k] == SEE:
                sta.qbgz += con.fhru[k]*(flu.nkor[k]-flu.evi[k])
            elif con.lnk[k] not in (WASSER, FLUSS, VERS):
                sta.qbgz += con.fhru[k]*flu.qbb[k]


class Calc_QIGZ1_V1(modeltools.Method):
    """Aggregate the amount of the first interflow component released
    by all HRUs.

    Basic equation:
       :math:`QIGZ1 = \\Sigma(FHRU \\cdot QIB1)`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(2)
        >>> fhru(0.75, 0.25)
        >>> fluxes.qib1 = 1.0, 5.0
        >>> model.calc_qigz1_v1()
        >>> states.qigz1
        qigz1(2.0)
    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.FHRU,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.QIB1,
    )
    RESULTSEQUENCES = (
        lland_states.QIGZ1,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        sta.qigz1 = 0.
        for k in range(con.nhru):
            sta.qigz1 += con.fhru[k]*flu.qib1[k]


class Calc_QIGZ2_V1(modeltools.Method):
    """Aggregate the amount of the second interflow component released
    by all HRUs.

    Basic equation:
       :math:`QIGZ2 = \\Sigma(FHRU \\cdot QIB2)`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(2)
        >>> fhru(0.75, 0.25)
        >>> fluxes.qib2 = 1.0, 5.0
        >>> model.calc_qigz2_v1()
        >>> states.qigz2
        qigz2(2.0)
    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.FHRU,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.QIB2,
    )
    RESULTSEQUENCES = (
        lland_states.QIGZ2,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        sta.qigz2 = 0.
        for k in range(con.nhru):
            sta.qigz2 += con.fhru[k]*flu.qib2[k]


class Calc_QDGZ_V1(modeltools.Method):
    """Aggregate the amount of total direct flow released by all HRUs.

    Basic equation:
       :math:`QDGZ = \\Sigma(FHRU \\cdot QDB) +
       \\Sigma(FHRU \\cdot (NKor_{FLUSS}-EvI_{FLUSS}))`

    Examples:

        The first example shows that |QDGZ| is the area weighted sum of
        |QDB| from "land type" HRUs like arable land (|ACKER|) and sealed
        surfaces (|VERS|) as well as of |NKor|-|EvI| from water areas of
        type |FLUSS|.  Water areas of type |WASSER| and |SEE| have no
        impact on |QDGZ|:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(5)
        >>> lnk(ACKER, VERS, WASSER, SEE, FLUSS)
        >>> fhru(0.1, 0.2, 0.1, 0.2, 0.4)
        >>> fluxes.qdb = 2., 4.0, 300.0, 300.0, 300.0
        >>> fluxes.nkor = 200.0, 200.0, 200.0, 200.0, 20.0
        >>> fluxes.evi = 100.0, 100.0, 100.0, 100.0, 10.0
        >>> model.calc_qdgz_v1()
        >>> fluxes.qdgz
        qdgz(5.0)

        The second example shows that large evaporation values above a
        HRU of type |FLUSS| can result in negative values of |QDGZ|:

        >>> fluxes.evi[4] = 30
        >>> model.calc_qdgz_v1()
        >>> fluxes.qdgz
        qdgz(-3.0)
    """
    CONTROLPARAMETERS = (
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.FHRU,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.NKor,
        lland_fluxes.EvI,
        lland_fluxes.QDB,
    )
    RESULTSEQUENCES = (
        lland_fluxes.QDGZ,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.qdgz = 0.
        for k in range(con.nhru):
            if con.lnk[k] == FLUSS:
                flu.qdgz += con.fhru[k]*(flu.nkor[k]-flu.evi[k])
            elif con.lnk[k] not in (WASSER, SEE):
                flu.qdgz += con.fhru[k]*flu.qdb[k]


class Calc_QDGZ1_QDGZ2_V1(modeltools.Method):
    """Separate total direct flow into a slower and a faster component.

    Basic equations:
       :math:`QDGZ2 = \\frac{(QDGZ-A2)^2}{QDGZ+A1-A2}`

       :math:`QDGZ1 = QDGZ - QDGZ1`

    Examples:

        We borrowed the formula for calculating the amount of the faster
        component of direct flow from the well-known curve number approach.
        Parameter |A2| would be the initial loss and parameter |A1| the
        maximum storage, but one should not take this analogy too literally.

        With the value of parameter |A1| set to zero, parameter |A2| defines
        the maximum amount of "slow" direct runoff per time step:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> simulationstep('12h')
        >>> a1(0.0)

        Let us set the value of |A2| to 4 mm/d, which is 2 mm/12h concerning
        the selected simulation step size:

        >>> a2(4.0)
        >>> a2
        a2(4.0)
        >>> a2.value
        2.0

        Define a test function and let it calculate |QDGZ1| and |QDGZ1| for
        values of |QDGZ| ranging from -10 to 100 mm/12h:

        >>> from hydpy import UnitTest
        >>> test = UnitTest(model,
        ...                 model.calc_qdgz1_qdgz2_v1,
        ...                 last_example=6,
        ...                 parseqs=(fluxes.qdgz,
        ...                          states.qdgz1,
        ...                          states.qdgz2))
        >>> test.nexts.qdgz = -10.0, 0.0, 1.0, 2.0, 3.0, 100.0
        >>> test()
        | ex. |  qdgz | qdgz1 | qdgz2 |
        -------------------------------
        |   1 | -10.0 | -10.0 |   0.0 |
        |   2 |   0.0 |   0.0 |   0.0 |
        |   3 |   1.0 |   1.0 |   0.0 |
        |   4 |   2.0 |   2.0 |   0.0 |
        |   5 |   3.0 |   2.0 |   1.0 |
        |   6 | 100.0 |   2.0 |  98.0 |

        Setting |A2| to zero and |A1| to 4 mm/d (or 2 mm/12h) results in
        a smoother transition:

        >>> a2(0.0)
        >>> a1(4.0)
        >>> test()
        | ex. |  qdgz |    qdgz1 |     qdgz2 |
        --------------------------------------
        |   1 | -10.0 |    -10.0 |       0.0 |
        |   2 |   0.0 |      0.0 |       0.0 |
        |   3 |   1.0 | 0.666667 |  0.333333 |
        |   4 |   2.0 |      1.0 |       1.0 |
        |   5 |   3.0 |      1.2 |       1.8 |
        |   6 | 100.0 | 1.960784 | 98.039216 |

        Alternatively, one can mix these two configurations by setting
        the values of both parameters to 2 mm/h:

        >>> a2(2.0)
        >>> a1(2.0)
        >>> test()
        | ex. |  qdgz |    qdgz1 |    qdgz2 |
        -------------------------------------
        |   1 | -10.0 |    -10.0 |      0.0 |
        |   2 |   0.0 |      0.0 |      0.0 |
        |   3 |   1.0 |      1.0 |      0.0 |
        |   4 |   2.0 |      1.5 |      0.5 |
        |   5 |   3.0 | 1.666667 | 1.333333 |
        |   6 | 100.0 |     1.99 |    98.01 |

        Note the similarity of the results for very high values of total
        direct flow |QDGZ| in all three examples, which converge to the sum
        of the values of parameter |A1| and |A2|, representing the maximum
        value of `slow` direct flow generation per simulation step
    """
    CONTROLPARAMETERS = (
        lland_control.A2,
        lland_control.A1,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.QDGZ,
    )
    RESULTSEQUENCES = (
        lland_states.QDGZ2,
        lland_states.QDGZ1,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        if flu.qdgz > con.a2:
            sta.qdgz2 = (flu.qdgz-con.a2)**2/(flu.qdgz+con.a1-con.a2)
            sta.qdgz1 = flu.qdgz-sta.qdgz2
        else:
            sta.qdgz2 = 0.
            sta.qdgz1 = flu.qdgz


class Calc_QBGA_V1(modeltools.Method):
    """Perform the runoff concentration calculation for base flow.

    The working equation is the analytical solution of the linear storage
    equation under the assumption of constant change in inflow during
    the simulation time step.

    Basic equation:
       :math:`QBGA_{neu} = QBGA_{alt} +
       (QBGZ_{alt}-QBGA_{alt}) \\cdot (1-exp(-KB^{-1})) +
       (QBGZ_{neu}-QBGZ_{alt}) \\cdot (1-KB\\cdot(1-exp(-KB^{-1})))`

    Examples:

        A normal test case:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> derived.kb(0.1)
        >>> states.qbgz.old = 2.0
        >>> states.qbgz.new = 4.0
        >>> states.qbga.old = 3.0
        >>> model.calc_qbga_v1()
        >>> states.qbga
        qbga(3.800054)

        First extreme test case (zero division is circumvented):

        >>> derived.kb(0.0)
        >>> model.calc_qbga_v1()
        >>> states.qbga
        qbga(4.0)

        Second extreme test case (numerical overflow is circumvented):

        >>> derived.kb(1e500)
        >>> model.calc_qbga_v1()
        >>> states.qbga
        qbga(5.0)
    """
    DERIVEDPARAMETERS = (
        lland_derived.KB,
    )
    REQUIREDSEQUENCES = (
        lland_states.QBGZ,
        lland_states.QBGA,
    )
    RESULTSEQUENCES = (
        lland_states.QBGA,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        if der.kb <= 0.:
            new.qbga = new.qbgz
        elif der.kb > 1e200:
            new.qbga = old.qbga+new.qbgz-old.qbgz
        else:
            d_temp = (1.-modelutils.exp(-1./der.kb))
            new.qbga = (old.qbga +
                        (old.qbgz-old.qbga)*d_temp +
                        (new.qbgz-old.qbgz)*(1.-der.kb*d_temp))


class Calc_QIGA1_V1(modeltools.Method):
    """Perform the runoff concentration calculation for the first
    interflow component.

    The working equation is the analytical solution of the linear storage
    equation under the assumption of constant change in inflow during
    the simulation time step.

    Basic equation:
       :math:`QIGA1_{neu} = QIGA1_{alt} +
       (QIGZ1_{alt}-QIGA1_{alt}) \\cdot (1-exp(-KI1^{-1})) +
       (QIGZ1_{neu}-QIGZ1_{alt}) \\cdot (1-KI1\\cdot(1-exp(-KI1^{-1})))`

    Examples:

        A normal test case:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> derived.ki1(0.1)
        >>> states.qigz1.old = 2.0
        >>> states.qigz1.new = 4.0
        >>> states.qiga1.old = 3.0
        >>> model.calc_qiga1_v1()
        >>> states.qiga1
        qiga1(3.800054)

        First extreme test case (zero division is circumvented):

        >>> derived.ki1(0.0)
        >>> model.calc_qiga1_v1()
        >>> states.qiga1
        qiga1(4.0)

        Second extreme test case (numerical overflow is circumvented):

        >>> derived.ki1(1e500)
        >>> model.calc_qiga1_v1()
        >>> states.qiga1
        qiga1(5.0)
    """
    DERIVEDPARAMETERS = (
        lland_derived.KI1,
    )
    REQUIREDSEQUENCES = (
        lland_states.QIGZ1,
        lland_states.QIGA1,
    )
    RESULTSEQUENCES = (
        lland_states.QIGA1,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        if der.ki1 <= 0.:
            new.qiga1 = new.qigz1
        elif der.ki1 > 1e200:
            new.qiga1 = old.qiga1+new.qigz1-old.qigz1
        else:
            d_temp = (1.-modelutils.exp(-1./der.ki1))
            new.qiga1 = (old.qiga1 +
                         (old.qigz1-old.qiga1)*d_temp +
                         (new.qigz1-old.qigz1)*(1.-der.ki1*d_temp))


class Calc_QIGA2_V1(modeltools.Method):
    """Perform the runoff concentration calculation for the second
    interflow component.

    The working equation is the analytical solution of the linear storage
    equation under the assumption of constant change in inflow during
    the simulation time step.

    Basic equation:
       :math:`QIGA2_{neu} = QIGA2_{alt} +
       (QIGZ2_{alt}-QIGA2_{alt}) \\cdot (1-exp(-KI2^{-1})) +
       (QIGZ2_{neu}-QIGZ2_{alt}) \\cdot (1-KI2\\cdot(1-exp(-KI2^{-1})))`

    Examples:

        A normal test case:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> derived.ki2(0.1)
        >>> states.qigz2.old = 2.0
        >>> states.qigz2.new = 4.0
        >>> states.qiga2.old = 3.0
        >>> model.calc_qiga2_v1()
        >>> states.qiga2
        qiga2(3.800054)

        First extreme test case (zero division is circumvented):

        >>> derived.ki2(0.0)
        >>> model.calc_qiga2_v1()
        >>> states.qiga2
        qiga2(4.0)

        Second extreme test case (numerical overflow is circumvented):

        >>> derived.ki2(1e500)
        >>> model.calc_qiga2_v1()
        >>> states.qiga2
        qiga2(5.0)
    """
    DERIVEDPARAMETERS = (
        lland_derived.KI2,
    )
    REQUIREDSEQUENCES = (
        lland_states.QIGZ2,
        lland_states.QIGA2,
    )
    RESULTSEQUENCES = (
        lland_states.QIGA2,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        if der.ki2 <= 0.:
            new.qiga2 = new.qigz2
        elif der.ki2 > 1e200:
            new.qiga2 = old.qiga2+new.qigz2-old.qigz2
        else:
            d_temp = (1.-modelutils.exp(-1./der.ki2))
            new.qiga2 = (old.qiga2 +
                         (old.qigz2-old.qiga2)*d_temp +
                         (new.qigz2-old.qigz2)*(1.-der.ki2*d_temp))


class Calc_QDGA1_V1(modeltools.Method):
    """Perform the runoff concentration calculation for "slow" direct runoff.

    The working equation is the analytical solution of the linear storage
    equation under the assumption of constant change in inflow during
    the simulation time step.

    Basic equation:
       :math:`QDGA1_{neu} = QDGA1_{alt} +
       (QDGZ1_{alt}-QDGA1_{alt}) \\cdot (1-exp(-KD1^{-1})) +
       (QDGZ1_{neu}-QDGZ1_{alt}) \\cdot (1-KD1\\cdot(1-exp(-KD1^{-1})))`

    Examples:

        A normal test case:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> derived.kd1(0.1)
        >>> states.qdgz1.old = 2.0
        >>> states.qdgz1.new = 4.0
        >>> states.qdga1.old = 3.0
        >>> model.calc_qdga1_v1()
        >>> states.qdga1
        qdga1(3.800054)

        First extreme test case (zero division is circumvented):

        >>> derived.kd1(0.0)
        >>> model.calc_qdga1_v1()
        >>> states.qdga1
        qdga1(4.0)

        Second extreme test case (numerical overflow is circumvented):

        >>> derived.kd1(1e500)
        >>> model.calc_qdga1_v1()
        >>> states.qdga1
        qdga1(5.0)
    """
    DERIVEDPARAMETERS = (
        lland_derived.KD1,
    )
    REQUIREDSEQUENCES = (
        lland_states.QDGZ1,
        lland_states.QDGA1,
    )
    RESULTSEQUENCES = (
        lland_states.QDGA1,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        if der.kd1 <= 0.:
            new.qdga1 = new.qdgz1
        elif der.kd1 > 1e200:
            new.qdga1 = old.qdga1+new.qdgz1-old.qdgz1
        else:
            d_temp = (1.-modelutils.exp(-1./der.kd1))
            new.qdga1 = (old.qdga1 +
                         (old.qdgz1-old.qdga1)*d_temp +
                         (new.qdgz1-old.qdgz1)*(1.-der.kd1*d_temp))


class Calc_QDGA2_V1(modeltools.Method):
    """Perform the runoff concentration calculation for "fast" direct runoff.

    The working equation is the analytical solution of the linear storage
    equation under the assumption of constant change in inflow during
    the simulation time step.

    Basic equation:
       :math:`QDGA2_{neu} = QDGA2_{alt} +
       (QDGZ2_{alt}-QDGA2_{alt}) \\cdot (1-exp(-KD2^{-1})) +
       (QDGZ2_{neu}-QDGZ2_{alt}) \\cdot (1-KD2\\cdot(1-exp(-KD2^{-1})))`

    Examples:

        A normal test case:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> derived.kd2(0.1)
        >>> states.qdgz2.old = 2.0
        >>> states.qdgz2.new = 4.0
        >>> states.qdga2.old = 3.0
        >>> model.calc_qdga2_v1()
        >>> states.qdga2
        qdga2(3.800054)

        First extreme test case (zero division is circumvented):

        >>> derived.kd2(0.0)
        >>> model.calc_qdga2_v1()
        >>> states.qdga2
        qdga2(4.0)

        Second extreme test case (numerical overflow is circumvented):

        >>> derived.kd2(1e500)
        >>> model.calc_qdga2_v1()
        >>> states.qdga2
        qdga2(5.0)
    """
    DERIVEDPARAMETERS = (
        lland_derived.KD2,
    )
    REQUIREDSEQUENCES = (
        lland_states.QDGZ2,
        lland_states.QDGA2,
    )
    RESULTSEQUENCES = (
        lland_states.QDGA2,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        if der.kd2 <= 0.:
            new.qdga2 = new.qdgz2
        elif der.kd2 > 1e200:
            new.qdga2 = old.qdga2+new.qdgz2-old.qdgz2
        else:
            d_temp = (1.-modelutils.exp(-1./der.kd2))
            new.qdga2 = (old.qdga2 +
                         (old.qdgz2-old.qdga2)*d_temp +
                         (new.qdgz2-old.qdgz2)*(1.-der.kd2*d_temp))


class Calc_Q_V1(modeltools.Method):
    """Calculate the final runoff.

    Note that, in case there are water areas, their |NKor| values are
    added and their |EvPo| values are subtracted from the "potential"
    runoff value, if possible.  This hold true for |WASSER| only and is
    due to compatibility with the original LARSIM implementation. Using land
    type |WASSER| can result  in problematic modifications of simulated
    runoff series. It seems advisable to use land type |FLUSS| and/or
    land type |SEE| instead.

    Basic equations:
       :math:`Q = QBGA + QIGA1 + QIGA2 + QDGA1 + QDGA2 +
       NKor_{WASSER} - EvI_{WASSER}`

       :math:`Q \\geq 0`

    Examples:

        When there are no water areas in the respective subbasin (we
        choose arable land |ACKER| arbitrarily), the different runoff
        components are simply summed up:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(3)
        >>> lnk(ACKER, ACKER, ACKER)
        >>> fhru(0.5, 0.2, 0.3)
        >>> negq(False)
        >>> states.qbga = 0.1
        >>> states.qiga1 = 0.3
        >>> states.qiga2 = 0.5
        >>> states.qdga1 = 0.7
        >>> states.qdga2 = 0.9
        >>> fluxes.nkor = 10.0
        >>> fluxes.evi = 4.0, 5.0, 3.0
        >>> model.calc_q_v1()
        >>> fluxes.q
        q(2.5)
        >>> fluxes.evi
        evi(4.0, 5.0, 3.0)

        The defined values of interception evaporation do not show any
        impact on the result of the given example, the predefined values
        for sequence |EvI| remain unchanged.  But when the first HRU is
        assumed to be a water area (|WASSER|), its adjusted precipitaton
        |NKor| value and its interception  evaporation |EvI| value are added
        to and subtracted from |lland_fluxes.Q| respectively:

        >>> control.lnk(WASSER, VERS, NADELW)
        >>> model.calc_q_v1()
        >>> fluxes.q
        q(5.5)
        >>> fluxes.evi
        evi(4.0, 5.0, 3.0)

        Note that only 5 mm are added (instead of the |NKor| value 10 mm)
        and that only 2 mm are substracted (instead of the |EvI| value 4 mm,
        as the first HRU`s area only accounts for 50 % of the subbasin area.

        Setting also the land use class of the second HRU to land type
        |WASSER| and resetting |NKor| to zero would result in overdrying.
        To avoid this, both actual water evaporation values stored in
        sequence |EvI| are reduced by the same factor:

        >>> control.lnk(WASSER, WASSER, NADELW)
        >>> fluxes.nkor = 0.0
        >>> model.calc_q_v1()
        >>> fluxes.q
        q(0.0)
        >>> fluxes.evi
        evi(3.333333, 4.166667, 3.0)

        The handling from water areas of type |FLUSS| and |SEE| differs
        from those of type |WASSER|, as these do receive their net input
        before the runoff concentration routines are applied.  This
        should be more realistic in most cases (especially for type |SEE|
        representing lakes not direct connected to the stream network).
        But it could sometimes result in negative outflow values. This
        is avoided by simply setting |lland_fluxes.Q| to zero and adding
        the truncated negative outflow value to the |EvI| value of all
        HRUs of type |FLUSS| and |SEE|:

        >>> control.lnk(FLUSS, SEE, NADELW)
        >>> states.qbga = -1.0
        >>> states.qdga2 = -1.5
        >>> fluxes.evi = 4.0, 5.0, 3.0
        >>> model.calc_q_v1()
        >>> fluxes.q
        q(0.0)
        >>> fluxes.evi
        evi(2.571429, 3.571429, 3.0)

        This adjustment of |EvI| is only correct regarding the total
        water balance.  Neither spatial nor temporal consistency of the
        resulting |EvI| values are assured.  In the most extreme case,
        even negative |EvI| values might occur.  This seems acceptable,
        as long as the adjustment of |EvI| is rarely triggered.  When in
        doubt about this, check sequences |EvPo| and |EvI| of HRUs of
        types |FLUSS| and |SEE| for possible discrepancies.  Also note
        that there might occur unnecessary corrections of |lland_fluxes.Q|
        in case landtype |WASSER| is combined with either landtype
        |SEE| or |FLUSS|.

        Eventually you might want to avoid correcting |lland_fluxes.Q|.
        This can be achieved by setting parameter |NegQ| to `True`:

        >>> negq(True)
        >>> fluxes.evi = 4.0, 5.0, 3.0
        >>> model.calc_q_v1()
        >>> fluxes.q
        q(-1.0)
        >>> fluxes.evi
        evi(4.0, 5.0, 3.0)
    """
    CONTROLPARAMETERS = (
        lland_control.NegQ,
        lland_control.NHRU,
        lland_control.Lnk,
        lland_control.FHRU,
    )
    REQUIREDSEQUENCES = (
        lland_states.QBGA,
        lland_states.QIGA1,
        lland_states.QIGA2,
        lland_states.QDGA1,
        lland_states.QDGA2,
        lland_fluxes.NKor,
        lland_fluxes.EvI,
    )
    UPDATEDSEQUENCES = (
        lland_fluxes.EvI,
    )
    RESULTSEQUENCES = (
        lland_fluxes.Q,
        lland_aides.EPW,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        aid = model.sequences.aides.fastaccess
        flu.q = sta.qbga+sta.qiga1+sta.qiga2+sta.qdga1+sta.qdga2
        if (not con.negq) and (flu.q < 0.):
            d_area = 0.
            for k in range(con.nhru):
                if con.lnk[k] in (FLUSS, SEE):
                    d_area += con.fhru[k]
            if d_area > 0.:
                for k in range(con.nhru):
                    if con.lnk[k] in (FLUSS, SEE):
                        flu.evi[k] += flu.q/d_area
            flu.q = 0.
        aid.epw = 0.
        for k in range(con.nhru):
            if con.lnk[k] == WASSER:
                flu.q += con.fhru[k]*flu.nkor[k]
                aid.epw += con.fhru[k]*flu.evi[k]
        if (flu.q > aid.epw) or con.negq:
            flu.q -= aid.epw
        elif aid.epw > 0.:
            for k in range(con.nhru):
                if con.lnk[k] == WASSER:
                    flu.evi[k] *= flu.q/aid.epw
            flu.q = 0.


class Pass_Q_V1(modeltools.Method):
    """Update the outlet link sequence.

    Basic equation:
       :math:`Q_{outlets} = QFactor \\cdot Q_{fluxes}`
    """
    DERIVEDPARAMETERS = (
        lland_derived.QFactor,
    )
    REQUIREDSEQUENCES = (
        lland_fluxes.Q,
    )
    RESULTSEQUENCES = (
        lland_outlets.Q,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        out = model.sequences.outlets.fastaccess
        out.q[0] += der.qfactor*flu.q


class Model(modeltools.AdHocModel):
    """Base model for HydPy-L-Land."""
    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        Calc_NKor_V1,
        Calc_TKor_V1,
        Calc_ET0_V1,
        Calc_ET0_WET0_V1,
        Calc_EvPo_V1,
        Calc_NBes_Inzp_V1,
        Calc_EvI_Inzp_V1,
        Calc_SBes_V1,
        Calc_WGTF_V1,
        Calc_Schm_WATS_V1,
        Calc_WaDa_WAeS_V1,
        Calc_EvB_V1,
        Calc_QBB_V1,
        Calc_QIB1_V1,
        Calc_QIB2_V1,
        Calc_QDB_V1,
        Calc_BoWa_V1,
        Calc_QBGZ_V1,
        Calc_QIGZ1_V1,
        Calc_QIGZ2_V1,
        Calc_QDGZ_V1,
        Calc_QDGZ1_QDGZ2_V1,
        Calc_QBGA_V1,
        Calc_QIGA1_V1,
        Calc_QIGA2_V1,
        Calc_QDGA1_V1,
        Calc_QDGA2_V1,
        Calc_Q_V1,
    )
    ADD_METHODS = ()
    OUTLET_METHODS = (
        Pass_Q_V1,
    )
    SENDER_METHODS = ()
