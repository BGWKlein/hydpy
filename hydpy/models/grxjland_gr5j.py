# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, wildcard-import, unused-wildcard-import
"""
GR5J Version of the GrXJ-Land model.
The model can briefly be summarized as follows:

TODO

The following figure shows the general structure of HydPy GrXJ-Land Version GR5J:

.. image:: HydPy-GrXJ-Land_Version-Gr5J.png

Integration tests:

    As integration test we use the example of the R-package airGR gauging station
    Blue River at Nourlangie Rock with a catchment area 360 km².

    The integration test is performed over a period of 50 days with
    a simulation step of one day:

    >>> from hydpy import pub
    >>> pub.timegrids = '01.01.1990', '20.02.1990', '1d'

    Prepare the model instance and build the connections to element `land`
    and node `outlet`:

    >>> from hydpy.models.grxjland_gr5j import *
    >>> from hydpy import pub
    >>> pub.options.reprdigits = 6
    >>> ret = pub.options.printprogress(False)
    >>> parameterstep('1d')
    >>> from hydpy import Node, Element
    >>> outlet = Node('outlet')
    >>> land = Element('land', outlets=outlet)
    >>> land.model = model

    All tests are performed using a lumped basin with a size of
    360 km²:

    >>> area(360.0)

    Initialize a test function object, which prepares and runs the tests
    and prints their results for the given sequences:

    >>> from hydpy import IntegrationTest
    >>> IntegrationTest.plotting_options.height = 900
    >>> IntegrationTest.plotting_options.activated=(
    ...     inputs.e, inputs.p, fluxes.qt)
    >>> test = IntegrationTest(land)
    >>> test.dateformat = '%d.%m.'

    .. _grxjland_gr5j_ex1:

    **Example 1**

    We compared the results of grxjland_gr5j with the results of
    the GR5J implementation of the airGR package:
    The following code was used to run the airGR Gr5J model to compare our results:
    
    .. code-block:: none

        library(airGR)
        ## loading catchment data
        data(L0123001)
        # preparation of the InputsModel object
        InputsModel <- CreateInputsModel(FUN_MOD = RunModel_GR5J, DatesR = BasinObs$DatesR,
            Precip = BasinObs$P, PotEvap = BasinObs$E)
        ## run period selection
        Ind_Run <- seq(which(format(BasinObs$DatesR, format = "%Y-%m-%d")=="1990-01-01"),
            which(format(BasinObs$DatesR, format = "%Y-%m-%d")=="1990-02-19"))
        ## preparation of the RunOptions object
        RunOptions <- CreateRunOptions(FUN_MOD = RunModel_GR5J,
            InputsModel = InputsModel,
			IndPeriod_WarmUp = 0L, IndPeriod_Run = Ind_Run)
        ## simulation
        Param <- c(X1 = 245.918, X2 = 1.027, X3 = 90.017, X4 = 2.198, X5 = 0.434)
        OutputsModel <- RunModel_GR5J(InputsModel = InputsModel,
            RunOptions = RunOptions, Param = Param)
    
    Set control parameters:
    
    >>> x1(245.918)
    >>> x2(1.027)
    >>> x3(90.017)
    >>> x4(2.198)
    >>> x5(0.434)
    
    Set initial storage levels: production store 30% filled, routing store 50% filled. log.sequences empty
    

    >>> test.inits = ((states.s, 0.3 * x1),
    ...               (states.r, 0.5 * x3),
    ...               (logs.quh2, [0.0, 0.0, 0.0, 0.0, 0.0]))

    Input sequences |P| and |E|:

    >>> inputs.p.series = (
    ...     0.0,  9.3,  3.2,  7.3,  0.0,  0.0,  0.0,  0.0,  0.1,  0.2,  2.9,  0.2,  0.0,  0.0,  0.0,
    ...     3.3,  4.6,  0.8,  1.8,  1.1,  0.0,  5.0, 13.1, 14.6,  4.0,  0.8,  0.1,  3.3,  7.7, 10.3,
    ...     3.7, 15.3,  3.2,  2.7,  2.2,  8.0, 14.3,  6.3,  0.0,  5.9,  9.2,  6.1,  0.1,  0.0,  2.8,
    ...     10.6,  8.8,  7.2,  4.9,  1.8)
    >>> inputs.e.series = (
    ...     0.3, 0.4, 0.4, 0.3, 0.1, 0.1, 0.1, 0.2, 0.2, 0.3, 0.3, 0.2, 0.2, 0.2, 0.2, 0.3, 0.3, 0.2, 0.2,
    ...     0.3, 0.2, 0.2, 0.3, 0.6, 0.4, 0.4, 0.4, 0.5, 0.4, 0.3, 0.3, 0.5, 0.5, 0.3, 0.3, 0.4, 0.4, 0.3,
    ...     0.2, 0.1, 0.1, 0.0, 0.1, 0.1, 0.0, 0.2, 0.9, 0.9, 0.5, 0.9)


    >>> test('grxjland_gr5j_ex1')
    |   date |    p |   e |  en |   pn |        ps |       es |       pr |     perc |       q9 |       q1 |         f |       qr |       qd |       qt |          s |         r |    outlet |
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |  0.0 | 0.3 | 0.3 |  0.0 |       0.0 | 0.152869 | 0.005768 | 0.005768 | 0.000362 |  0.00004 |  0.067782 |    0.682 | 0.067822 | 0.749822 |  73.616763 | 44.394645 |  3.124258 |
    | 02.01. |  9.3 | 0.4 | 0.0 |  8.9 |   8.01214 |      0.4 | 0.897523 | 0.009664 | 0.058076 | 0.006453 |  0.060779 | 0.641622 | 0.067231 | 0.708854 |  81.619239 | 43.871877 |  2.953558 |
    | 03.01. |  3.2 | 0.4 | 0.0 |  2.8 |  2.482079 |      0.4 | 0.329139 | 0.011218 | 0.285578 | 0.031731 |  0.054814 | 0.620795 | 0.086545 | 0.707341 |    84.0901 | 43.591473 |  2.947252 |
    | 04.01. |  7.3 | 0.3 | 0.0 |  7.0 |  6.120298 |      0.3 | 0.895629 | 0.015927 | 0.512318 | 0.056924 |  0.051615 | 0.616923 | 0.108539 | 0.725463 |  90.194471 | 43.538483 |  3.022761 |
    | 05.01. |  0.0 | 0.1 | 0.1 |  0.0 |       0.0 | 0.059886 |  0.01586 |  0.01586 | 0.518979 | 0.057664 |  0.051011 | 0.613741 | 0.108675 | 0.722416 |  90.118724 | 43.494731 |  3.010067 |
    | 06.01. |  0.0 | 0.1 | 0.1 |  0.0 |       0.0 | 0.059847 | 0.015794 | 0.015794 | 0.414966 | 0.046107 |  0.050511 | 0.603772 | 0.096619 | 0.700391 |  90.043083 | 43.356436 |  2.918296 |
    | 07.01. |  0.0 | 0.1 | 0.1 |  0.0 |       0.0 | 0.059808 | 0.015728 | 0.015728 | 0.138004 | 0.015334 |  0.048934 | 0.576415 | 0.064267 | 0.640683 |  89.967547 | 42.966959 |  2.669511 |
    | 08.01. |  0.0 | 0.2 | 0.2 |  0.0 |       0.0 | 0.119507 |  0.01561 |  0.01561 | 0.019648 | 0.002183 |   0.04449 | 0.544119 | 0.046673 | 0.590792 |   89.83243 | 42.486978 |  2.461632 |
    | 09.01. |  0.1 | 0.2 | 0.1 |  0.0 |       0.0 | 0.159699 | 0.015545 | 0.015545 | 0.014119 | 0.001569 |  0.039014 | 0.514498 | 0.040583 |  0.55508 |  89.757186 | 42.025613 |  2.312835 |
    | 10.01. |  0.2 | 0.3 | 0.1 |  0.0 |       0.0 | 0.259661 |  0.01548 |  0.01548 | 0.014039 |  0.00156 |   0.03375 | 0.487516 |  0.03531 | 0.522826 |  89.682045 | 41.585887 |  2.178444 |
    | 11.01. |  2.9 | 0.3 | 0.0 |  2.6 |  2.245475 |      0.3 | 0.372026 | 0.017501 | 0.036378 | 0.004042 |  0.028734 | 0.464056 | 0.032776 | 0.496831 |   91.91002 | 41.186942 |  2.070131 |
    | 12.01. |  0.2 | 0.2 | 0.0 |  0.0 |       0.0 |      0.2 | 0.017485 | 0.017485 | 0.118384 | 0.013154 |  0.024182 | 0.446796 | 0.037336 | 0.484132 |  91.892535 | 40.882712 |  2.017217 |
    | 13.01. |  0.0 | 0.2 | 0.2 |  0.0 |       0.0 | 0.121481 | 0.017353 | 0.017353 | 0.157232 |  0.01747 |  0.020711 |  0.43275 | 0.038181 | 0.470931 |  91.753702 | 40.627905 |  1.962214 |
    | 14.01. |  0.0 | 0.2 | 0.2 |  0.0 |       0.0 | 0.121339 | 0.017222 | 0.017222 |  0.06476 | 0.007196 |  0.017804 | 0.414973 | 0.024999 | 0.439973 |   91.61514 | 40.295495 |  1.833219 |
    | 15.01. |  0.0 | 0.2 | 0.2 |  0.0 |       0.0 | 0.121198 | 0.017093 | 0.017093 |  0.01778 | 0.001976 |  0.014012 | 0.396179 | 0.015987 | 0.412166 |   91.47685 | 39.931108 |  1.717358 |
    | 16.01. |  3.3 | 0.3 | 0.0 |  3.0 |  2.573086 |      0.3 |  0.44653 | 0.019616 | 0.042454 | 0.004717 |  0.009854 | 0.379885 | 0.014571 | 0.394456 |   94.03032 | 39.603532 |  1.643566 |
    | 17.01. |  4.6 | 0.3 | 0.0 |  4.3 |  3.646577 |      0.3 | 0.677123 |   0.0237 | 0.182513 | 0.020279 |  0.006117 | 0.371051 | 0.026396 | 0.397447 |  97.653197 |  39.42111 |  1.656031 |
    | 18.01. |  0.8 | 0.2 | 0.0 |  0.6 |  0.504898 |      0.2 | 0.119391 | 0.024289 | 0.386667 | 0.042963 |  0.004036 | 0.371951 | 0.046999 |  0.41895 |  98.133806 | 39.439861 |  1.745626 |
    | 19.01. |  1.8 | 0.2 | 0.0 |  1.6 |  1.341711 |      0.2 | 0.284252 | 0.025962 | 0.385529 | 0.042837 |   0.00425 |  0.37277 | 0.047086 | 0.419856 |  99.449555 |  39.45687 |  1.749399 |
    | 20.01. |  1.1 | 0.3 | 0.0 |  0.8 |  0.668286 |      0.3 | 0.158525 | 0.026811 | 0.237398 | 0.026378 |  0.004444 | 0.366794 | 0.030821 | 0.397615 |  100.09103 | 39.331918 |   1.65673 |
    | 21.01. |  0.0 | 0.2 | 0.2 |  0.0 |       0.0 |  0.12961 | 0.026602 | 0.026602 | 0.182463 | 0.020274 |  0.003018 | 0.358643 | 0.023292 | 0.381935 |  99.934817 | 39.158756 |  1.591395 |
    | 22.01. |  5.0 | 0.2 | 0.0 |  4.8 |   3.97529 |      0.2 | 0.856995 | 0.032285 | 0.165124 | 0.018347 |  0.001043 | 0.350146 |  0.01939 | 0.369535 | 103.877822 | 38.974777 |  1.539731 |
    | 23.01. | 13.1 | 0.3 | 0.0 | 12.8 | 10.280792 |      0.3 | 2.570862 | 0.051654 | 0.446604 | 0.049623 | -0.001056 | 0.354338 | 0.048566 | 0.402904 | 114.106961 | 39.065987 |  1.678766 |
    | 24.01. | 14.6 | 0.6 | 0.0 | 14.0 | 10.691824 |      0.6 | 3.388788 | 0.080612 | 1.312483 | 0.145831 | -0.000016 | 0.398649 | 0.145816 | 0.544465 | 124.718173 | 39.979805 |  2.268604 |
    | 25.01. |  4.0 | 0.4 | 0.0 |  3.6 |  2.654168 |      0.4 | 1.035093 | 0.089261 | 2.203511 | 0.244835 |   0.01041 | 0.494365 | 0.255244 | 0.749609 |  127.28308 | 41.699362 |  3.123371 |
    | 26.01. |  0.8 | 0.4 | 0.0 |  0.4 |  0.292596 |      0.4 | 0.197379 | 0.089975 | 2.031824 | 0.225758 |  0.030028 |  0.59059 | 0.255786 | 0.846376 | 127.485702 | 43.170624 |  3.526568 |
    | 27.01. |  0.1 | 0.4 | 0.3 |  0.0 |       0.0 | 0.330285 | 0.088853 | 0.088853 | 0.962462 |  0.10694 |  0.046814 | 0.618589 | 0.153754 | 0.772343 | 127.166563 | 43.561311 |  3.218095 |
    | 28.01. |  3.3 | 0.5 | 0.0 |  2.8 |  2.039179 |      0.5 | 0.856684 | 0.095863 | 0.323089 | 0.035899 |  0.051271 | 0.602135 |  0.08717 | 0.689305 | 129.109879 | 43.333537 |  2.872103 |
    | 29.01. |  7.7 | 0.4 | 0.0 |  7.3 |  5.205195 |      0.4 | 2.211145 | 0.116341 | 0.458845 | 0.050983 |  0.048672 | 0.595852 | 0.099655 | 0.695507 | 134.198734 | 43.245202 |  2.897946 |
    | 30.01. | 10.3 | 0.3 | 0.0 | 10.0 |  6.865916 |      0.3 | 3.282676 | 0.148592 | 1.209309 | 0.134368 |  0.047665 |  0.64083 | 0.182032 | 0.822862 | 140.916058 | 43.861346 |  3.428592 |
    | 31.01. |  3.7 | 0.3 | 0.0 |  3.4 |  2.265509 |      0.3 | 1.294546 | 0.160055 | 2.045246 |  0.22725 |  0.054694 | 0.749345 | 0.281944 | 1.031289 | 143.021512 | 45.211941 |  4.297036 |
    | 01.02. | 15.3 | 0.5 | 0.0 | 14.8 |  9.451847 |      0.5 |  5.56716 | 0.219007 | 2.352851 | 0.261428 |  0.070103 | 0.890594 | 0.331531 | 1.222125 | 152.254352 | 46.744301 |  5.092188 |
    | 02.02. |  3.2 | 0.5 | 0.0 |  2.7 |  1.653735 |      0.5 |  1.27574 | 0.229475 | 2.694931 | 0.299437 |  0.087586 | 1.073779 | 0.387023 | 1.460802 | 153.678612 | 48.453038 |  6.086675 |
    | 03.02. |  2.7 | 0.3 | 0.0 |  2.4 |  1.453833 |      0.3 | 1.184887 |  0.23872 |   2.8738 | 0.319311 |  0.107081 | 1.285953 | 0.426392 | 1.712345 | 154.893724 | 50.147966 |  7.134771 |
    | 04.02. |  2.2 | 0.3 | 0.0 |  1.9 |  1.140653 |      0.3 | 1.005065 | 0.245719 | 1.698899 | 0.188767 |  0.126418 |   1.3513 | 0.315184 | 1.666484 | 155.788659 | 50.621983 |  6.943685 |
    | 05.02. |  8.0 | 0.4 | 0.0 |  7.6 |  4.461205 |      0.4 | 3.419425 | 0.280629 | 1.193925 | 0.132658 |  0.131826 |  1.34815 | 0.264484 | 1.612634 | 159.969234 | 50.599584 |  6.719308 |
    | 06.02. | 14.3 | 0.4 | 0.0 | 13.9 |  7.725949 |      0.4 | 6.525911 |  0.35186 | 1.984371 | 0.220486 |   0.13157 | 1.445249 | 0.352056 | 1.797305 | 167.343323 | 51.270276 |   7.48877 |
    | 07.02. |  6.3 | 0.3 | 0.0 |  6.0 |  3.168414 |      0.3 | 3.213866 |  0.38228 | 3.625292 |  0.40281 |  0.139222 | 1.770272 | 0.542033 | 2.312305 | 170.129457 | 53.264518 |  9.634604 |
    | 08.02. |  0.0 | 0.2 | 0.2 |  0.0 |       0.0 | 0.180959 | 0.376036 | 0.376036 | 4.053564 | 0.450396 |  0.161975 | 2.168109 | 0.612371 | 2.780479 | 169.572463 | 55.311948 |  11.58533 |
    | 09.02. |  5.9 | 0.1 | 0.0 |  5.8 |     2.993 |      0.1 | 3.212752 | 0.405752 | 2.522004 | 0.280223 |  0.185334 | 2.263913 | 0.465556 | 2.729469 |  172.15971 | 55.755373 | 11.372788 |
    | 10.02. |  9.2 | 0.1 | 0.0 |  9.1 |  4.520933 |      0.1 | 5.035298 | 0.456231 |  1.89217 | 0.210241 |  0.190393 | 2.231358 | 0.400634 | 2.631991 | 176.224413 | 55.606578 |  10.96663 |
    | 11.02. |  6.1 | 0.0 | 0.0 |  6.1 |  2.915155 |      0.0 | 3.673541 | 0.488695 | 3.060883 | 0.340098 |  0.188695 | 2.418601 | 0.528793 | 2.947394 | 178.650872 | 56.437555 | 12.280809 |
    | 12.02. |  0.1 | 0.1 | 0.0 |  0.0 |       0.0 |      0.1 | 0.482102 | 0.482102 |  3.56605 | 0.396228 |  0.198176 | 2.683026 | 0.594403 | 3.277429 | 178.168771 | 57.518754 | 13.655955 |
    | 13.02. |  0.0 | 0.1 | 0.1 |  0.0 |       0.0 |   0.0924 |  0.47444 |  0.47444 | 2.357162 | 0.261907 |  0.210511 | 2.659586 | 0.472418 | 3.132003 |  177.60193 | 57.426841 | 13.050014 |
    | 14.02. |  2.8 | 0.0 | 0.0 |  2.8 |  1.328614 |      0.0 | 1.957252 | 0.485866 | 0.994454 | 0.110495 |  0.209462 | 2.376212 | 0.319957 | 2.696169 | 178.444678 | 56.254545 | 11.234038 |
    | 15.02. | 10.6 | 0.2 | 0.0 | 10.4 |  4.774677 |      0.2 |  6.17191 | 0.546587 | 1.239676 | 0.137742 |  0.196088 | 2.205107 | 0.333829 | 2.538937 | 182.672769 | 55.485201 | 10.578903 |
    | 16.02. |  8.8 | 0.9 | 0.0 |  7.9 |  3.457239 |      0.9 | 5.033879 | 0.591118 |  2.97346 | 0.330384 |   0.18731 | 2.379056 | 0.517695 | 2.896751 |  185.53889 | 56.266915 | 12.069796 |
    | 17.02. |  7.2 | 0.9 | 0.0 |  6.3 |  2.661808 |      0.9 | 4.262707 | 0.624515 | 4.482914 | 0.498102 |  0.196229 | 2.837811 |  0.69433 | 3.532141 | 187.576183 | 58.108248 | 14.717255 |
    | 18.02. |  4.9 | 0.5 | 0.0 |  4.4 |  1.815109 |      0.5 | 3.229276 | 0.644385 |  4.32999 |  0.48111 |  0.217236 | 3.217024 | 0.698346 |  3.91537 | 188.746907 |  59.43845 | 16.314042 |
    | 19.02. |  1.8 | 0.9 | 0.0 |  0.9 |  0.368785 |      0.9 | 1.170957 | 0.639741 | 3.458453 | 0.384273 |  0.232413 | 3.328116 | 0.616685 | 3.944801 |  188.47595 | 59.801199 | 16.436671 |


    .. raw:: html

        <iframe
            src="grxjland_gr5j_ex1.html"
            width="100%"
            height="930px"
            frameborder=0
        ></iframe>

    .. _grxjland_gr5j_ex2:

    **Example 2**

    In the second example we start from empty storages, again we reproduce the results from the airGR package running
    the following code:

    .. code-block:: none

        library(airGR)
        data(L0123001)
        InputsModel <- CreateInputsModel(FUN_MOD = RunModel_GR5J, DatesR = BasinObs$DatesR,
            Precip = BasinObs$P, PotEvap = BasinObs$E)
        ## run period selection
        Ind_Run <- seq(which(format(BasinObs$DatesR, format = "%Y-%m-%d")=="1990-01-01"),
            which(format(BasinObs$DatesR, format = "%Y-%m-%d")=="1990-02-19"))
        IniStates <- CreateIniStates(FUN_MOD = RunModel_GR5J, InputsModel = InputsModel,
            ProdStore = 0, RoutStore = 0)
        ## preparation of the RunOptions object
        RunOptions <- CreateRunOptions(FUN_MOD = RunModel_GR5J,
            InputsModel = InputsModel,
            IndPeriod_WarmUp = 0L, IndPeriod_Run = Ind_Run, IniStates = IniStates)
        ## simulation
        Param <- c(X1 = 245.918, X2 = 1.027, X3 = 90.017, X4 = 2.198, X5 = 0.434)
        OutputsModel <- RunModel_GR5J(InputsModel = InputsModel,
            RunOptions = RunOptions, Param = Param)

   Set initial storage levels: empty production store and routing store. log.sequences empty


    >>> test.inits = ((states.s, 0),
    ...               (states.r, 0),
    ...               (logs.quh2, [0.0, 0.0, 0.0, 0.0, 0.0]))

    Run Integration test

    >>> test('grxjland_gr5j_ex2')
    |   date |    p |   e |  en |   pn |        ps |       es |       pr |     perc |       q9 |       q1 |         f |       qr |       qd |       qt |          s |         r |   outlet |
    ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |  0.0 | 0.3 | 0.3 |  0.0 |       0.0 |      0.0 |      0.0 |      0.0 |      0.0 |      0.0 | -0.445718 |      0.0 |      0.0 |      0.0 |        0.0 |       0.0 |      0.0 |
    | 02.01. |  9.3 | 0.4 | 0.0 |  8.9 |  8.896116 |      0.4 | 0.003884 |      0.0 | 0.000244 | 0.000027 | -0.445718 |      0.0 |      0.0 |      0.0 |   8.896116 |       0.0 |      0.0 |
    | 03.01. |  3.2 | 0.4 | 0.0 |  2.8 |  2.795064 |      0.4 | 0.004937 | 0.000001 | 0.001446 | 0.000161 | -0.445718 |      0.0 |      0.0 |      0.0 |  11.691179 |       0.0 |      0.0 |
    | 04.01. |  7.3 | 0.3 | 0.0 |  7.0 |   6.97286 |      0.3 | 0.027146 | 0.000006 | 0.004703 | 0.000523 | -0.445718 |      0.0 |      0.0 |      0.0 |  18.664033 |       0.0 |      0.0 |
    | 05.01. |  0.0 | 0.1 | 0.1 |  0.0 |       0.0 | 0.014598 | 0.000006 | 0.000006 | 0.010455 | 0.001162 | -0.445718 |      0.0 |      0.0 |      0.0 |   18.64943 |       0.0 |      0.0 |
    | 06.01. |  0.0 | 0.1 | 0.1 |  0.0 |       0.0 | 0.014587 | 0.000006 | 0.000006 | 0.011567 | 0.001285 | -0.445718 |      0.0 |      0.0 |      0.0 |  18.634837 |       0.0 |      0.0 |
    | 07.01. |  0.0 | 0.1 | 0.1 |  0.0 |       0.0 | 0.014576 | 0.000006 | 0.000006 | 0.003794 | 0.000422 | -0.445718 |      0.0 |      0.0 |      0.0 |  18.620255 |       0.0 |      0.0 |
    | 08.01. |  0.0 | 0.2 | 0.2 |  0.0 |       0.0 | 0.029118 | 0.000006 | 0.000006 | 0.000174 | 0.000019 | -0.445718 |      0.0 |      0.0 |      0.0 |  18.591131 |       0.0 |      0.0 |
    | 09.01. |  0.1 | 0.2 | 0.1 |  0.0 |       0.0 | 0.114543 | 0.000006 | 0.000006 | 0.000005 | 0.000001 | -0.445718 |      0.0 |      0.0 |      0.0 |  18.576582 |       0.0 |      0.0 |
    | 10.01. |  0.2 | 0.3 | 0.1 |  0.0 |       0.0 | 0.214532 | 0.000006 | 0.000006 | 0.000005 | 0.000001 | -0.445718 |      0.0 |      0.0 |      0.0 |  18.562045 |       0.0 |      0.0 |
    | 11.01. |  2.9 | 0.3 | 0.0 |  2.6 |  2.583029 |      0.3 | 0.016982 | 0.000011 | 0.001072 | 0.000119 | -0.445718 |      0.0 |      0.0 |      0.0 |  21.145063 |       0.0 |      0.0 |
    | 12.01. |  0.2 | 0.2 | 0.0 |  0.0 |       0.0 |      0.2 | 0.000011 | 0.000011 | 0.004972 | 0.000552 | -0.445718 |      0.0 |      0.0 |      0.0 |  21.145052 |       0.0 |      0.0 |
    | 13.01. |  0.0 | 0.2 | 0.2 |  0.0 |       0.0 | 0.032891 | 0.000011 | 0.000011 | 0.006797 | 0.000755 | -0.445718 |      0.0 |      0.0 |      0.0 |   21.11215 |       0.0 |      0.0 |
    | 14.01. |  0.0 | 0.2 | 0.2 |  0.0 |       0.0 | 0.032842 | 0.000011 | 0.000011 |  0.00236 | 0.000262 | -0.445718 |      0.0 |      0.0 |      0.0 |  21.079297 |       0.0 |      0.0 |
    | 15.01. |  0.0 | 0.2 | 0.2 |  0.0 |       0.0 | 0.032793 | 0.000011 | 0.000011 | 0.000115 | 0.000013 | -0.445718 |      0.0 |      0.0 |      0.0 |  21.046493 |       0.0 |      0.0 |
    | 16.01. |  3.3 | 0.3 | 0.0 |  3.0 |  2.974773 |      0.3 | 0.025248 | 0.000021 | 0.001596 | 0.000177 | -0.445718 |      0.0 |      0.0 |      0.0 |  24.021245 |       0.0 |      0.0 |
    | 17.01. |  4.6 | 0.3 | 0.0 |  4.3 |  4.251278 |      0.3 |  0.04877 | 0.000048 | 0.010457 | 0.001162 | -0.445718 |      0.0 |      0.0 |      0.0 |  28.272474 |       0.0 |      0.0 |
    | 18.01. |  0.8 | 0.2 | 0.0 |  0.6 |  0.591902 |      0.2 | 0.008151 | 0.000053 |  0.02488 | 0.002764 | -0.445718 |      0.0 |      0.0 |      0.0 |  28.864323 |       0.0 |      0.0 |
    | 19.01. |  1.8 | 0.2 | 0.0 |  1.6 |  1.576731 |      0.2 | 0.023339 |  0.00007 | 0.026852 | 0.002984 | -0.445718 |      0.0 |      0.0 |      0.0 |  30.440985 |       0.0 |      0.0 |
    | 20.01. |  1.1 | 0.3 | 0.0 |  0.8 |  0.787422 |      0.3 | 0.012657 | 0.000079 | 0.017793 | 0.001977 | -0.445718 |      0.0 |      0.0 |      0.0 |  31.228327 |       0.0 |      0.0 |
    | 21.01. |  0.0 | 0.2 | 0.2 |  0.0 |       0.0 | 0.047536 | 0.000079 | 0.000079 | 0.014473 | 0.001608 | -0.445718 |      0.0 |      0.0 |      0.0 |  31.180713 |       0.0 |      0.0 |
    | 22.01. |  5.0 | 0.2 | 0.0 |  4.8 |  4.710577 |      0.2 | 0.089582 | 0.000159 | 0.013995 | 0.001555 | -0.445718 |      0.0 |      0.0 |      0.0 |  35.891131 |       0.0 |      0.0 |
    | 23.01. | 13.1 | 0.3 | 0.0 | 12.8 | 12.421773 |      0.3 | 0.378929 | 0.000702 | 0.051945 | 0.005772 | -0.445718 |      0.0 |      0.0 |      0.0 |  48.312202 |       0.0 |      0.0 |
    | 24.01. | 14.6 | 0.6 | 0.0 | 14.0 | 13.296594 |      0.6 | 0.705773 | 0.002367 | 0.191123 | 0.021236 | -0.445718 |      0.0 |      0.0 |      0.0 |  61.606429 |       0.0 |      0.0 |
    | 25.01. |  4.0 | 0.4 | 0.0 |  3.6 |  3.361502 |      0.4 | 0.241585 | 0.003087 | 0.385621 | 0.042847 | -0.445718 |      0.0 |      0.0 |      0.0 |  64.964845 |       0.0 |      0.0 |
    | 26.01. |  0.8 | 0.4 | 0.0 |  0.4 |  0.371925 |      0.4 |  0.03125 | 0.003175 | 0.407932 | 0.045326 | -0.445718 |      0.0 |      0.0 |      0.0 |  65.333594 |       0.0 |      0.0 |
    | 27.01. |  0.1 | 0.4 | 0.3 |  0.0 |       0.0 | 0.238105 | 0.003141 | 0.003141 | 0.206032 | 0.022892 | -0.445718 |      0.0 |      0.0 |      0.0 |  65.192348 |       0.0 |      0.0 |
    | 28.01. |  3.3 | 0.5 | 0.0 |  2.8 |  2.595279 |      0.5 | 0.208538 | 0.003817 | 0.064345 | 0.007149 | -0.445718 |      0.0 |      0.0 |      0.0 |   67.78381 |       0.0 |      0.0 |
    | 29.01. |  7.7 | 0.4 | 0.0 |  7.3 |  6.688689 |      0.4 | 0.617419 | 0.006109 | 0.106884 | 0.011876 | -0.445718 |      0.0 |      0.0 |      0.0 |  74.466391 |       0.0 |      0.0 |
    | 30.01. | 10.3 | 0.3 | 0.0 | 10.0 |  8.967696 |      0.3 | 1.043084 |  0.01078 | 0.330205 | 0.036689 | -0.445718 |      0.0 |      0.0 |      0.0 |  83.423307 |       0.0 |      0.0 |
    | 31.01. |  3.7 | 0.3 | 0.0 |  3.4 |  2.994498 |      0.3 | 0.418352 |  0.01285 | 0.607286 | 0.067476 | -0.445718 |      0.0 |      0.0 |      0.0 |  86.404955 |  0.161568 |      0.0 |
    | 01.02. | 15.3 | 0.5 | 0.0 | 14.8 | 12.689278 |      0.5 | 2.136191 | 0.025469 | 0.760558 | 0.084506 | -0.443875 |      0.0 |      0.0 |      0.0 |  99.068764 |  0.478252 |      0.0 |
    | 02.02. |  3.2 | 0.5 | 0.0 |  2.7 |  2.251766 |      0.5 | 0.476694 |  0.02846 | 0.970514 | 0.107835 | -0.440262 |      0.0 |      0.0 |      0.0 |  101.29207 |  1.008504 |      0.0 |
    | 03.02. |  2.7 | 0.3 | 0.0 |  2.4 |  1.984783 |      0.3 | 0.446531 | 0.031314 | 1.086256 | 0.120695 | -0.434212 |      0.0 |      0.0 |      0.0 | 103.245539 |  1.660548 |      0.0 |
    | 04.02. |  2.2 | 0.3 | 0.0 |  1.9 |  1.560008 |      0.3 | 0.373691 | 0.033699 | 0.643145 | 0.071461 | -0.426773 |      0.0 |      0.0 |      0.0 | 104.771848 |   1.87692 |      0.0 |
    | 05.02. |  8.0 | 0.4 | 0.0 |  7.6 |  6.137731 |      0.4 | 1.506984 | 0.044715 | 0.461843 | 0.051316 | -0.424304 |      0.0 |      0.0 |      0.0 | 110.864864 |  1.914459 |      0.0 |
    | 06.02. | 14.3 | 0.4 | 0.0 | 13.9 | 10.788579 |      0.4 | 3.182385 | 0.070964 | 0.855079 | 0.095009 | -0.423876 |      0.0 |      0.0 |      0.0 | 121.582479 |  2.345662 | 0.000001 |
    | 07.02. |  6.3 | 0.3 | 0.0 |  6.0 |  4.478486 |      0.3 |  1.60628 | 0.084766 | 1.689209 |  0.18769 | -0.418956 | 0.000002 |      0.0 | 0.000002 | 125.976199 |  3.615913 |  0.00001 |
    | 08.02. |  0.0 | 0.2 | 0.2 |  0.0 |       0.0 | 0.152363 | 0.083973 | 0.083973 | 1.958962 | 0.217662 | -0.404464 | 0.000014 |      0.0 | 0.000014 | 125.739863 |  5.170396 | 0.000059 |
    | 09.02. |  5.9 | 0.1 | 0.0 |  5.8 |  4.231854 |      0.1 |  1.66688 | 0.098734 | 1.221688 | 0.135743 | -0.386729 |  0.00003 |      0.0 |  0.00003 | 129.872983 |  6.005326 | 0.000124 |
    | 10.02. |  9.2 | 0.1 | 0.0 |  9.1 |  6.433302 |      0.1 | 2.791906 | 0.125207 | 0.938816 | 0.104313 | -0.377204 | 0.000046 |      0.0 | 0.000046 | 136.181077 |  6.566892 | 0.000194 |
    | 11.02. |  6.1 | 0.0 | 0.0 |  6.1 |   4.17124 |      0.0 | 2.073646 | 0.144885 | 1.635352 | 0.181706 | -0.370797 | 0.000112 |      0.0 | 0.000112 | 140.207431 |  7.831335 | 0.000467 |
    | 12.02. |  0.1 | 0.1 | 0.0 |  0.0 |       0.0 |      0.1 | 0.144141 | 0.144141 | 1.963658 | 0.218184 | -0.356371 | 0.000285 |      0.0 | 0.000285 |  140.06329 |  9.438336 | 0.001188 |
    | 13.02. |  0.0 | 0.1 | 0.1 |  0.0 |       0.0 | 0.081457 | 0.142987 | 0.142987 | 1.277392 | 0.141932 | -0.338036 | 0.000458 |      0.0 | 0.000458 | 139.838846 | 10.377234 | 0.001909 |
    | 14.02. |  2.8 | 0.0 | 0.0 |  2.8 |  1.882347 |      0.0 | 1.069728 | 0.152075 | 0.471121 | 0.052347 | -0.327325 | 0.000491 |      0.0 | 0.000491 | 141.569118 | 10.520539 | 0.002045 |
    | 15.02. | 10.6 | 0.2 | 0.0 | 10.4 |  6.784199 |      0.2 | 3.806846 | 0.191045 | 0.642146 |  0.07135 |  -0.32569 | 0.000569 |      0.0 | 0.000569 | 148.162273 | 10.836427 | 0.002371 |
    | 16.02. |  8.8 | 0.9 | 0.0 |  7.9 |  4.935164 |      0.9 | 3.188349 | 0.223512 | 1.762613 | 0.195846 | -0.322086 | 0.001062 |      0.0 | 0.001062 | 152.873924 | 12.275892 | 0.004424 |
    | 17.02. |  7.2 | 0.9 | 0.0 |  6.3 |  3.803992 |      0.9 | 2.746819 | 0.250812 | 2.776902 | 0.308545 | -0.305663 | 0.002655 | 0.002882 | 0.005536 | 156.427105 | 14.744477 | 0.023068 |
    | 18.02. |  4.9 | 0.5 | 0.0 |  4.4 |  2.589936 |      0.5 |   2.0801 | 0.270036 |  2.74321 | 0.304801 | -0.277499 | 0.005744 | 0.027302 | 0.033046 | 158.747005 | 17.204444 | 0.137692 |
    | 19.02. |  1.8 | 0.9 | 0.0 |  0.9 |  0.523724 |      0.9 | 0.648465 | 0.272189 | 2.212948 | 0.245883 | -0.249433 | 0.009839 |      0.0 | 0.009839 |  158.99854 | 19.158119 | 0.040997 |

    .. raw:: html

        <iframe
            src="grxjland_gr5j_ex2.html"
            width="100%"
            height="930px"
            frameborder=0
        ></iframe>


 .. _grxjland_gr5j_ex3:

    **Example 3**

    In the third we start from empty storages and use a negative groundwater exchange coefficient X2.
    Agaim we reproduce the results from the airGR package running
    the following code:

    .. code-block:: none

        library(airGR)
        data(L0123001)
        InputsModel <- CreateInputsModel(FUN_MOD = RunModel_GR5J, DatesR = BasinObs$DatesR,
            Precip = BasinObs$P, PotEvap = BasinObs$E)
        ## run period selection
        Ind_Run <- seq(which(format(BasinObs$DatesR, format = "%Y-%m-%d")=="1990-01-01"),
            which(format(BasinObs$DatesR, format = "%Y-%m-%d")=="1990-02-19"))
        IniStates <- CreateIniStates(FUN_MOD = RunModel_GR5J, InputsModel = InputsModel,
            ProdStore = 0, RoutStore = 0)
        ## preparation of the RunOptions object
        RunOptions <- CreateRunOptions(FUN_MOD = RunModel_GR5J,
            InputsModel = InputsModel,
            IndPeriod_WarmUp = 0L, IndPeriod_Run = Ind_Run, IniStates = IniStates)
        ## simulation
        Param <- c(X1 = 245.918, X2 = -1.027, X3 = 90.017, X4 = 2.198, X5 = 0.434)
        OutputsModel <- RunModel_GR5J(InputsModel = InputsModel,
            RunOptions = RunOptions, Param = Param)


    Set negative control parameters X2:

    >>> x2(-1.027)

    Run Integration test

    >>> test('grxjland_gr5j_ex3')
    |   date |    p |   e |  en |   pn |        ps |       es |       pr |     perc |       q9 |       q1 |         f |       qr |       qd |       qt |          s |         r |   outlet |
    ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |  0.0 | 0.3 | 0.3 |  0.0 |       0.0 |      0.0 |      0.0 |      0.0 |      0.0 |      0.0 |  0.445718 |      0.0 | 0.445718 | 0.445718 |        0.0 |  0.445718 | 1.857158 |
    | 02.01. |  9.3 | 0.4 | 0.0 |  8.9 |  8.896116 |      0.4 | 0.003884 |      0.0 | 0.000244 | 0.000027 |  0.440633 |      0.0 |  0.44066 |  0.44066 |   8.896116 |  0.886595 | 1.836083 |
    | 03.01. |  3.2 | 0.4 | 0.0 |  2.8 |  2.795064 |      0.4 | 0.004937 | 0.000001 | 0.001446 | 0.000161 |  0.435603 |      0.0 | 0.435764 | 0.435764 |  11.691179 |  1.323644 | 1.815682 |
    | 04.01. |  7.3 | 0.3 | 0.0 |  7.0 |   6.97286 |      0.3 | 0.027146 | 0.000006 | 0.004703 | 0.000523 |  0.430617 |      0.0 | 0.431139 | 0.431139 |  18.664033 |  1.758964 | 1.796413 |
    | 05.01. |  0.0 | 0.1 | 0.1 |  0.0 |       0.0 | 0.014598 | 0.000006 | 0.000006 | 0.010455 | 0.001162 |   0.42565 |      0.0 | 0.426812 | 0.426812 |   18.64943 |  2.195069 | 1.778383 |
    | 06.01. |  0.0 | 0.1 | 0.1 |  0.0 |       0.0 | 0.014587 | 0.000006 | 0.000006 | 0.011567 | 0.001285 |  0.420675 |      0.0 |  0.42196 |  0.42196 |  18.634837 |  2.627309 | 1.758168 |
    | 07.01. |  0.0 | 0.1 | 0.1 |  0.0 |       0.0 | 0.014576 | 0.000006 | 0.000006 | 0.003794 | 0.000422 |  0.415743 | 0.000001 | 0.416165 | 0.416166 |  18.620255 |  3.046845 | 1.734024 |
    | 08.01. |  0.0 | 0.2 | 0.2 |  0.0 |       0.0 | 0.029118 | 0.000006 | 0.000006 | 0.000174 | 0.000019 |  0.410957 | 0.000002 | 0.410976 | 0.410978 |  18.591131 |  3.457974 | 1.712408 |
    | 09.01. |  0.1 | 0.2 | 0.1 |  0.0 |       0.0 | 0.114543 | 0.000006 | 0.000006 | 0.000005 | 0.000001 |  0.406266 | 0.000003 | 0.406267 |  0.40627 |  18.576582 |  3.864242 | 1.692792 |
    | 10.01. |  0.2 | 0.3 | 0.1 |  0.0 |       0.0 | 0.214532 | 0.000006 | 0.000006 | 0.000005 | 0.000001 |  0.401631 | 0.000005 | 0.401632 | 0.401637 |  18.562045 |  4.265873 | 1.673488 |
    | 11.01. |  2.9 | 0.3 | 0.0 |  2.6 |  2.583029 |      0.3 | 0.016982 | 0.000011 | 0.001072 | 0.000119 |  0.397049 | 0.000008 | 0.397168 | 0.397176 |  21.145063 |  4.663985 | 1.654901 |
    | 12.01. |  0.2 | 0.2 | 0.0 |  0.0 |       0.0 |      0.2 | 0.000011 | 0.000011 | 0.004972 | 0.000552 |  0.392507 | 0.000013 | 0.393059 | 0.393072 |  21.145052 |  5.061452 |   1.6378 |
    | 13.01. |  0.0 | 0.2 | 0.2 |  0.0 |       0.0 | 0.032891 | 0.000011 | 0.000011 | 0.006797 | 0.000755 |  0.387972 | 0.000018 | 0.388727 | 0.388746 |   21.11215 |  5.456202 | 1.619774 |
    | 14.01. |  0.0 | 0.2 | 0.2 |  0.0 |       0.0 | 0.032842 | 0.000011 | 0.000011 |  0.00236 | 0.000262 |  0.383468 | 0.000026 | 0.383731 | 0.383757 |  21.079297 |  5.842004 | 1.598986 |
    | 15.01. |  0.0 | 0.2 | 0.2 |  0.0 |       0.0 | 0.032793 | 0.000011 | 0.000011 | 0.000115 | 0.000013 |  0.379067 | 0.000035 |  0.37908 | 0.379115 |  21.046493 |  6.221151 | 1.579646 |
    | 16.01. |  3.3 | 0.3 | 0.0 |  3.0 |  2.974773 |      0.3 | 0.025248 | 0.000021 | 0.001596 | 0.000177 |  0.374741 | 0.000048 | 0.374918 | 0.374966 |  24.021245 |   6.59744 | 1.562358 |
    | 17.01. |  4.6 | 0.3 | 0.0 |  4.3 |  4.251278 |      0.3 |  0.04877 | 0.000048 | 0.010457 | 0.001162 |  0.370448 | 0.000063 |  0.37161 | 0.371673 |  28.272474 |  6.978282 | 1.548638 |
    | 18.01. |  0.8 | 0.2 | 0.0 |  0.6 |  0.591902 |      0.2 | 0.008151 | 0.000053 |  0.02488 | 0.002764 |  0.366103 | 0.000083 | 0.368868 |  0.36895 |  28.864323 |  7.369183 | 1.537293 |
    | 19.01. |  1.8 | 0.2 | 0.0 |  1.6 |  1.576731 |      0.2 | 0.023339 |  0.00007 | 0.026852 | 0.002984 |  0.361643 | 0.000107 | 0.364627 | 0.364734 |  30.440985 |  7.757571 | 1.519724 |
    | 20.01. |  1.1 | 0.3 | 0.0 |  0.8 |  0.787422 |      0.3 | 0.012657 | 0.000079 | 0.017793 | 0.001977 |  0.357212 | 0.000135 | 0.359189 | 0.359325 |  31.228327 |  8.132441 | 1.497186 |
    | 21.01. |  0.0 | 0.2 | 0.2 |  0.0 |       0.0 | 0.047536 | 0.000079 | 0.000079 | 0.014473 | 0.001608 |  0.352935 | 0.000169 | 0.354543 | 0.354712 |  31.180713 |   8.49968 | 1.477968 |
    | 22.01. |  5.0 | 0.2 | 0.0 |  4.8 |  4.710577 |      0.2 | 0.089582 | 0.000159 | 0.013995 | 0.001555 |  0.348746 | 0.000208 | 0.350301 | 0.350509 |  35.891131 |  8.862213 | 1.460453 |
    | 23.01. | 13.1 | 0.3 | 0.0 | 12.8 | 12.421773 |      0.3 | 0.378929 | 0.000702 | 0.051945 | 0.005772 |  0.344609 | 0.000259 | 0.350381 |  0.35064 |  48.312202 |  9.258508 |    1.461 |
    | 24.01. | 14.6 | 0.6 | 0.0 | 14.0 | 13.296594 |      0.6 | 0.705773 | 0.002367 | 0.191123 | 0.021236 |  0.340088 | 0.000342 | 0.361324 | 0.361666 |  61.606429 |  9.789377 | 1.506943 |
    | 25.01. |  4.0 | 0.4 | 0.0 |  3.6 |  3.361502 |      0.4 | 0.241585 | 0.003087 | 0.385621 | 0.042847 |  0.334031 | 0.000488 | 0.376878 | 0.377366 |  64.964845 | 10.508541 | 1.572359 |
    | 26.01. |  0.8 | 0.4 | 0.0 |  0.4 |  0.371925 |      0.4 |  0.03125 | 0.003175 | 0.407932 | 0.045326 |  0.325827 | 0.000684 | 0.371152 | 0.371836 |  65.333594 | 11.241616 | 1.549317 |
    | 27.01. |  0.1 | 0.4 | 0.3 |  0.0 |       0.0 | 0.238105 | 0.003141 | 0.003141 | 0.206032 | 0.022892 |  0.317463 | 0.000858 | 0.340355 | 0.341213 |  65.192348 | 11.764252 | 1.421722 |
    | 28.01. |  3.3 | 0.5 | 0.0 |  2.8 |  2.595279 |      0.5 | 0.208538 | 0.003817 | 0.064345 | 0.007149 |    0.3115 | 0.001004 |  0.31865 | 0.319653 |   67.78381 | 12.139093 | 1.331889 |
    | 29.01. |  7.7 | 0.4 | 0.0 |  7.3 |  6.688689 |      0.4 | 0.617419 | 0.006109 | 0.106884 | 0.011876 |  0.307224 | 0.001187 |   0.3191 | 0.320286 |  74.466391 | 12.552015 | 1.334526 |
    | 30.01. | 10.3 | 0.3 | 0.0 | 10.0 |  8.967696 |      0.3 | 1.043084 |  0.01078 | 0.330205 | 0.036689 |  0.302513 | 0.001517 | 0.339202 | 0.340719 |  83.423307 | 13.183216 | 1.419661 |
    | 31.01. |  3.7 | 0.3 | 0.0 |  3.4 |  2.994498 |      0.3 | 0.418352 |  0.01285 | 0.607286 | 0.067476 |  0.295311 | 0.002111 | 0.362787 | 0.364898 |  86.404955 | 14.083702 | 1.520408 |
    | 01.02. | 15.3 | 0.5 | 0.0 | 14.8 | 12.689278 |      0.5 | 2.136191 | 0.025469 | 0.760558 | 0.084506 |  0.285038 | 0.003017 | 0.369544 | 0.372561 |  99.068764 | 15.126282 | 1.552337 |
    | 02.02. |  3.2 | 0.5 | 0.0 |  2.7 |  2.251766 |      0.5 | 0.476694 |  0.02846 | 0.970514 | 0.107835 |  0.273143 | 0.004473 | 0.380978 | 0.385451 |  101.29207 | 16.365466 | 1.606044 |
    | 03.02. |  2.7 | 0.3 | 0.0 |  2.4 |  1.984783 |      0.3 | 0.446531 | 0.031314 | 1.086256 | 0.120695 |  0.259005 | 0.006629 |   0.3797 | 0.386329 | 103.245539 | 17.704099 | 1.609703 |
    | 04.02. |  2.2 | 0.3 | 0.0 |  1.9 |  1.560008 |      0.3 | 0.373691 | 0.033699 | 0.643145 | 0.071461 |  0.243733 | 0.008446 | 0.315193 | 0.323639 | 104.771848 | 18.582531 | 1.348498 |
    | 05.02. |  8.0 | 0.4 | 0.0 |  7.6 |  6.137731 |      0.4 | 1.506984 | 0.044715 | 0.461843 | 0.051316 |  0.233711 | 0.010125 | 0.285027 | 0.295152 | 110.864864 |  19.26796 | 1.229798 |
    | 06.02. | 14.3 | 0.4 | 0.0 | 13.9 | 10.788579 |      0.4 | 3.182385 | 0.070964 | 0.855079 | 0.095009 |  0.225891 | 0.013263 | 0.320899 | 0.334162 | 121.582479 | 20.335666 | 1.392344 |
    | 07.02. |  6.3 | 0.3 | 0.0 |  6.0 |  4.478486 |      0.3 |  1.60628 | 0.084766 | 1.689209 |  0.18769 |  0.213709 | 0.020662 | 0.401399 | 0.422061 | 125.976199 | 22.217923 | 1.758588 |
    | 08.02. |  0.0 | 0.2 | 0.2 |  0.0 |       0.0 | 0.152363 | 0.083973 | 0.083973 | 1.958962 | 0.217662 |  0.192235 | 0.032613 | 0.409897 |  0.44251 | 125.739863 | 24.336507 | 1.843791 |
    | 09.02. |  5.9 | 0.1 | 0.0 |  5.8 |  4.231854 |      0.1 |  1.66688 | 0.098734 | 1.221688 | 0.135743 |  0.168064 | 0.042729 | 0.303807 | 0.346536 | 129.872983 |  25.68353 | 1.443899 |
    | 10.02. |  9.2 | 0.1 | 0.0 |  9.1 |  6.433302 |      0.1 | 2.791906 | 0.125207 | 0.938816 | 0.104313 |  0.152696 | 0.052141 | 0.257009 | 0.309149 | 136.181077 | 26.722902 | 1.288122 |
    | 11.02. |  6.1 | 0.0 | 0.0 |  6.1 |   4.17124 |      0.0 | 2.073646 | 0.144885 | 1.635352 | 0.181706 |  0.140838 | 0.071135 | 0.322543 | 0.393678 | 140.207431 | 28.427956 | 1.640325 |
    | 12.02. |  0.1 | 0.1 | 0.0 |  0.0 |       0.0 |      0.1 | 0.144141 | 0.144141 | 1.963658 | 0.218184 |  0.121385 | 0.099886 | 0.339569 | 0.439455 |  140.06329 | 30.413113 | 1.831061 |
    | 13.02. |  0.0 | 0.1 | 0.1 |  0.0 |       0.0 | 0.081457 | 0.142987 | 0.142987 | 1.277392 | 0.141932 |  0.098736 | 0.122419 | 0.240669 | 0.363088 | 139.838846 | 31.666822 | 1.512865 |
    | 14.02. |  2.8 | 0.0 | 0.0 |  2.8 |  1.882347 |      0.0 | 1.069728 | 0.152075 | 0.471121 | 0.052347 |  0.084433 |  0.13092 | 0.136779 | 0.267699 | 141.569118 | 32.091456 | 1.115413 |
    | 15.02. | 10.6 | 0.2 | 0.0 | 10.4 |  6.784199 |      0.2 | 3.806846 | 0.191045 | 0.642146 |  0.07135 |  0.079588 | 0.143261 | 0.150938 | 0.294199 | 148.162273 | 32.669929 | 1.225828 |
    | 16.02. |  8.8 | 0.9 | 0.0 |  7.9 |  4.935164 |      0.9 | 3.188349 | 0.223512 | 1.762613 | 0.195846 |  0.072988 | 0.183772 | 0.268834 | 0.452606 | 152.873924 | 34.321758 | 1.885859 |
    | 17.02. |  7.2 | 0.9 | 0.0 |  6.3 |  3.803992 |      0.9 | 2.746819 | 0.250812 | 2.776902 | 0.308545 |  0.054143 | 0.264741 | 0.362687 | 0.627428 | 156.427105 | 36.888061 | 2.614285 |
    | 18.02. |  4.9 | 0.5 | 0.0 |  4.4 |  2.589936 |      0.5 |   2.0801 | 0.270036 |  2.74321 | 0.304801 |  0.024864 | 0.364867 | 0.329665 | 0.694532 | 158.747005 | 39.291268 | 2.893883 |
    | 19.02. |  1.8 | 0.9 | 0.0 |  0.9 |  0.523724 |      0.9 | 0.648465 | 0.272189 | 2.212948 | 0.245883 | -0.002554 | 0.455975 | 0.243329 | 0.699304 |  158.99854 | 41.045686 | 2.913766 |

    .. raw:: html

        <iframe
            src="grxjland_gr5j_ex3.html"
            width="100%"
            height="930px"
            frameborder=0
        ></iframe>

**References**

Coron, L., G. Thirel, O. Delaigue, C. Perrin & V. Andréassian (2017): The suite of lumped GR hydrological models in an R package. Environmental Modelling & Software 94, 166-171

Coron, L., O. Delaigue, G. Thirel, C. Perrin & C. Michel (2019): airGR: Suite of GR Hydrological Models for Precipitation-Runoff Modelling. R package version 1.3.2.42. URL: https://CRAN.R-project.org/package=airGR.

Le Moine, N. (2008): Le bassin versant de surface vu par le souterrain : une voie d'amélioration des performances et du réalisme des modèles pluie-débit ? PhD thesis (french), UPMC, Paris, France.
    
Perrin, C., C. Michel & V. Andréassian (2003): Improvement of a parsimonious model for streamflow simulation. Journal of Hydrology 279(1), 275-289

Pushpalatha, R., C. Perrin, N. Le Moine, T. Mathevet, and V. Andréassian (2011): A downward structural sensitivity analysis of hydrological models to improve low-flow simulation. Journal of Hydrology, 411(1-2), 66-76. doi: 10.1016/j.jhydrol.2011.09.034.

"""

# import...
# ...from HydPy
from hydpy.exe.modelimports import *
from hydpy.core import modeltools
# ...from  grxjland
from hydpy.models.grxjland import grxjland_model


class Model(modeltools.AdHocModel):
    """GR5J version of GRxJ-Land (|grxjland_gr5j|)."""
    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        grxjland_model.Calc_En_Pn_V1,
        grxjland_model.Calc_En_Pn_V1,
        grxjland_model.Calc_Ps_V1,
        grxjland_model.Calc_Es_Perc_S_V1,
        grxjland_model.Calc_Pr_V1,
        grxjland_model.Calc_UH2_V2,
        grxjland_model.Calc_RoutingStore_V2,
        grxjland_model.Calc_Qd_V1,
        grxjland_model.Calc_Qt_V1,
    )
    ADD_METHODS = ()
    OUTLET_METHODS = (
        grxjland_model.Pass_Q_V1,
    )
    SENDER_METHODS = ()


tester = Tester()
# cythonizer = Cythonizer()
# cythonizer.finalise()
