#!/usr/bin/python3
"""
    This module is the container of the generators of figures.
    The code is redundant, but it is necessary to make sure
    a future change in the default values won't affect old figures...
"""
import numpy as np
from numpy import pi
from memoisation import memoised, FunMem
import matplotlib.pyplot as plt
import functools
import discretizations
from simulator import simulation_cv_rate_linear, simulation_cv_rate_matrixlinear
from simulator import frequency_simulation
from simulator import matrixlinear_frequency_simulation
from simulator import eigenvalues_matrixlinear_frequency_simulation
from simulator import simulation_firstlevels

REAL_FIG = True

def fig_interactionsTimeSpace():
    from discretizations.space.FD_extra import FiniteDifferencesExtra
    from discretizations.space.quad_splines_fv import QuadSplinesFV
    from discretizations.space.FD_naive import FiniteDifferencesNaive
    from discretizations.time.backward_euler import BackwardEuler
    from cv_factor_pade import rho_Pade_c, rho_Pade_FD_extra, rho_Pade_FV
    from discretizations.time.PadeLowTildeGamma import PadeLowTildeGamma

    #time_dis, space_dis = BackwardEuler, FiniteDifferencesExtra
    time_dis, space_dis = BackwardEuler, QuadSplinesFV
    # time_dis, space_dis = PadeLowTildeGamma, FiniteDifferencesExtra
    # time_dis, space_dis = PadeLowTildeGamma, QuadSplinesFV

    setting = Builder()
    setting.M1 = 200
    setting.M2 = 200
    setting.D1 = .5
    setting.D2 = 1.
    setting.R = 0.1
    setting.DT = 1.
    N = 3000
    setting.LAMBDA_1 = 0.14
    setting.LAMBDA_2 = -0.5
    axis_freq = get_discrete_freq(N, setting.DT)

    def combined_Pade(LAMBDAS):
        local_setting = setting.copy()
        local_setting.LAMBDA_1 = LAMBDAS[0]
        local_setting.LAMBDA_2 = LAMBDAS[1]
        dis = local_setting.build(time_dis, space_dis)
        combined = dis.varrho_robin_robin_modified(w=axis_freq,
                    order_time=0, order_operators=float('inf'),
                    order_equations=float('inf')) + rho_Pade_c(builder=local_setting, w=axis_freq) \
                    - dis.varrho_robin_robin_modified(w=axis_freq,
                    order_time=0, order_operators=0,
                    order_equations=0)
        return np.abs(combined)

    def to_minimize_Pade(LAMBDAS):
        return np.max(combined_Pade(LAMBDAS))

    def combined_BE(LAMBDAS):
        local_setting = setting.copy()
        local_setting.LAMBDA_1 = LAMBDAS[0]
        local_setting.LAMBDA_2 = LAMBDAS[1]
        dis = local_setting.build(time_dis, space_dis)
        combined = dis.varrho_robin_robin_modified(w=axis_freq,
                    order_time=0, order_operators=float('inf'),
                    order_equations=float('inf')) + dis.varrho_robin_robin_modified(w=axis_freq,
                    order_time=float('inf'), order_operators=0.,
                    order_equations=0) - dis.varrho_robin_robin_modified(w=axis_freq,
                    order_time=0, order_operators=0,
                    order_equations=0)
        return combined

    def to_minimize_BE(LAMBDAS):
        return np.max(combined_BE(LAMBDAS))

    from scipy.optimize import minimize
    ret = minimize(method='Nelder-Mead', fun=to_minimize_BE, x0=np.array((0.15, -0.15)))

    setting.LAMBDA_1 = ret.x[0]
    setting.LAMBDA_2 = ret.x[1]

    dis = setting.build(time_dis, space_dis)
    plt.semilogx(axis_freq*setting.DT, dis.analytic_robin_robin_modified(w=axis_freq,
                    order_time=float('inf'), order_operators=0,
                    order_equations=0), label=r"$\rho^{\rm (Time, c)}$")
    # plt.semilogx(axis_freq*setting.DT, rho_Pade_c(builder=setting, w=axis_freq), label=r"$\rho^{\rm (Time, c)}$")
    plt.semilogx(axis_freq*setting.DT, dis.analytic_robin_robin_modified(w=axis_freq,
                    order_time=0., order_operators=float('inf'),
                    order_equations=float('inf')), label=r"$\rho^{\rm (c, Space)}$")

    plt.semilogx(axis_freq*setting.DT, np.abs(combined_BE(ret.x)), label=r"$\rho^{\rm (Time, Space)}_{\rm combined}$")

    plt.semilogx(axis_freq*setting.DT, dis.analytic_robin_robin_modified(w=axis_freq,
                    order_time=float('inf'), order_operators=float('inf'),
                    order_equations=float('inf')), "--", label=r"$\rho^{\rm (Time, Space)}$")
    # plt.semilogx(axis_freq*setting.DT, np.abs(rho_Pade_FD_extra(builder=setting, w=axis_freq)), "--", label=r"$\rho^{\rm (Time, Space)}$")

    plt.legend()
    plt.ylim(ymin=0., ymax=0.1)
    plt.xlabel(r"$\omega \Delta t$")
    plt.ylabel(r"Convergence rate estimation")
    plt.show()


def fig_optiRates():
    import matplotlib as mpl
    mpl.rc('text', usetex=True)
    mpl.rcParams['text.latex.preamble']=[r"\usepackage{amsmath}"]
    fig, axes = plt.subplots(2, 2, figsize=[6.4*1.4, 4.8*1.4], sharex=True, sharey=True)
    axes[0,0].grid()
    axes[1,0].grid()
    axes[0,1].grid()
    axes[1,1].grid()
    axes[1,1].set_ylim(bottom=0.095, top=0.3) # all axis are shared

    caracs = {}
    caracs["continuous"] = {'color':'#00AF80', 'width':0.7, 'nb_+':9}
    caracs["modified"] = {'color':'#0000FF', 'width':1.3, 'nb_+':12}
    caracs["discrete"] = {'color':'#000000', 'width':0.7, 'nb_+':15}


    fig.suptitle("Optimized convergence rates with different methods")
    fig.subplots_adjust(left=0.07, bottom=0.12, right=0.98, top=0.92, wspace=0.13, hspace=0.16)
    #####################################
    # PADE
    ####################################
    from discretizations.time.PadeLowTildeGamma import PadeLowTildeGamma
    from discretizations.space.FD_extra import FiniteDifferencesExtra
    from cv_factor_pade import rho_Pade_FD_corr0, rho_Pade_c, rho_Pade_FD_extra

    time_dis, space_dis = PadeLowTildeGamma, FiniteDifferencesExtra

    def rho_c_FD_extra(builder, axis_freq):
        dis = builder.build(time_dis, space_dis)
        return dis.analytic_robin_robin_modified(w=axis_freq,
                    order_time=0, order_operators=float('inf'),
                    order_equations=float('inf'))

    def rho_m_FD(builder, axis_freq):
        dis = builder.build(time_dis, space_dis)
        return dis.analytic_robin_robin_modified(w=axis_freq,
                    order_time=1, order_operators=float('inf'),
                    order_equations=float('inf'))

    optiRatesGeneral(axes[0,0], rho_c_FD_extra, rho_m_FD, rho_Pade_FD_extra, time_dis, space_dis, "Pade", caracs=caracs)

    ########################################
    # BE
    ###########################################
    from discretizations.time.backward_euler import BackwardEuler
    from discretizations.space.FD_extra import FiniteDifferencesExtra
    time_dis, space_dis = BackwardEuler, FiniteDifferencesExtra
    def rho_c_FD_extra(builder, axis_freq):
        dis = builder.build(time_dis, space_dis)
        return dis.analytic_robin_robin_modified(w=axis_freq,
                    order_time=0, order_operators=float('inf'),
                    order_equations=float('inf'))
    def rho_BE_FD_extra(builder, axis_freq):
        dis = builder.build(time_dis, space_dis)
        return dis.analytic_robin_robin_modified(w=axis_freq,
                    order_time=float('inf'), order_operators=float('inf'),
                    order_equations=float('inf'))

    def rho_m_FD(builder, axis_freq):
        dis = builder.build(time_dis, space_dis)
        return dis.analytic_robin_robin_modified(w=axis_freq,
                    order_time=1, order_operators=float('inf'),
                    order_equations=float('inf'))
    
    optiRatesGeneral(axes[0,1], rho_c_FD_extra, rho_m_FD, rho_BE_FD_extra, time_dis, space_dis, "Backward Euler", caracs=caracs)

    #############################################
    # FD
    #######################################

    from discretizations.time.backward_euler import BackwardEuler
    from discretizations.space.FD_extra import FiniteDifferencesExtra
    time_dis, space_dis = BackwardEuler, FiniteDifferencesExtra
    def rho_BE_c(builder, axis_freq):
        dis = builder.build(time_dis, space_dis)
        return dis.analytic_robin_robin_modified(w=axis_freq,
                    order_time=float('inf'), order_operators=0,
                    order_equations=0)
    def rho_BE_FD_extra(builder, axis_freq):
        dis = builder.build(time_dis, space_dis)
        return dis.analytic_robin_robin_modified(w=axis_freq,
                    order_time=float('inf'), order_operators=float('inf'),
                    order_equations=float('inf'))

    def rho_m_FD(builder, axis_freq):
        dis = builder.build(time_dis, space_dis)
        return dis.analytic_robin_robin_modified(w=axis_freq,
                    order_time=float('inf'), order_operators=1,
                    order_equations=1)
    
    optiRatesGeneral(axes[1,0], rho_BE_c, rho_m_FD, rho_BE_FD_extra, time_dis, space_dis, "Finite Differences", caracs=caracs)

    ###########################
    # FV
    ##########################

    from discretizations.time.backward_euler import BackwardEuler
    from discretizations.space.quad_splines_fv import QuadSplinesFV
    time_dis, space_dis = BackwardEuler, QuadSplinesFV
    def rho_BE_c(builder, axis_freq):
        dis = builder.build(time_dis, space_dis)
        return dis.analytic_robin_robin_modified(w=axis_freq,
                    order_time=float('inf'), order_operators=0,
                    order_equations=0)
    def rho_BE_FV(builder, axis_freq):
        dis = builder.build(time_dis, space_dis)
        return dis.analytic_robin_robin_modified(w=axis_freq,
                    order_time=float('inf'), order_operators=float('inf'),
                    order_equations=float('inf'))

    def rho_m_FV(builder, axis_freq):
        dis = builder.build(time_dis, space_dis)
        return dis.analytic_robin_robin_modified(w=axis_freq,
                    order_time=float('inf'), order_operators=1,
                    order_equations=2)
    
    optiRatesGeneral(axes[1,1], rho_BE_c, rho_m_FV, rho_BE_FV, time_dis, space_dis, "Finite Volumes", caracs=caracs)


    from matplotlib.lines import Line2D
    custom_lines = [Line2D([0], [0], color=caracs["continuous"]["color"], lw=caracs["continuous"]["width"]),
                    Line2D([0], [0], color=caracs["modified"]["color"], lw=caracs["modified"]["width"]),
                    Line2D([0], [0], color=caracs["discrete"]["color"], lw=caracs["discrete"]["width"]),
                    Line2D([0], [0], marker="^", markersize=6., linewidth=0.,
                        color=caracs["discrete"]["color"]) ]
    custom_labels = ["Continuous", "Modified", "Discrete", "Prediction"]
    fig.legend(custom_lines, custom_labels, loc=(0.2, 0.), ncol=5, handlelength=2)

    show_or_save("fig_optiRates")

def fig_optiRatesPade():
    fig, axes = plt.subplots(1, 2, figsize=[6.4*2, 4.8*1], sharey=True)
    from discretizations.time.PadeLowTildeGamma import PadeLowTildeGamma
    from discretizations.time.PadeSimpleGamma import PadeSimpleGamma
    from discretizations.space.FD_extra import FiniteDifferencesExtra
    from cv_factor_pade import rho_Pade_FD_corr0, rho_Pade_c, rho_Pade_FD_extra

    time_dis, space_dis = PadeLowTildeGamma, FiniteDifferencesExtra

    def lowTilde_gamma(z):
        b = 1+1/np.sqrt(2)
        return z - b*(z-1) - b/2 * (z-1)**2

    def simple_gamma(z):
        b = 1+1/np.sqrt(2)
        return z - b*(z-1)

    def rho_c_FD_extra(builder, axis_freq):
        dis = builder.build(time_dis, space_dis)
        return dis.analytic_robin_robin_modified(w=axis_freq,
                    order_time=0, order_operators=float('inf'),
                    order_equations=float('inf'))

    def rho_m_FD(builder, axis_freq):
        dis = builder.build(time_dis, space_dis)
        return dis.analytic_robin_robin_modified(w=axis_freq,
                    order_time=2, order_operators=float('inf'),
                    order_equations=float('inf'))

    def rho_Pade_FD_lowTilde(builder, axis_freq):
        return rho_Pade_FD_extra(builder, axis_freq, gamma=lowTilde_gamma)

    def rho_Pade_FD_simple(builder, axis_freq):
        return rho_Pade_FD_extra(builder, axis_freq, gamma=simple_gamma)

    caracs = {}
    caracs["continuous"] = {'color':'#00AF80', 'width':0.7, 'nb_+':9}
    caracs["modified"] = {'color':'#0000FF', 'width':1., 'nb_+':12}
    caracs["discrete"] = {'color':'#000000', 'width':.9, 'nb_+':15}

    optiRatesGeneral(axes[0], rho_c_FD_extra, rho_m_FD, rho_Pade_FD_lowTilde, PadeLowTildeGamma, space_dis, "PadeLowTildeGamma", caracs=caracs)

    optiRatesGeneral(axes[1], rho_c_FD_extra, rho_m_FD, rho_Pade_FD_simple, PadeSimpleGamma, space_dis, "PadeSimpleGamma", caracs=caracs)

    show_or_save("fig_optiRatesPade")

def fig_optiRatesBE():
    fig, axes = plt.subplots(1, 1, figsize=[6.4*1, 4.8*1])
    from discretizations.time.backward_euler import BackwardEuler
    from discretizations.space.FD_extra import FiniteDifferencesExtra
    time_dis, space_dis = BackwardEuler, FiniteDifferencesExtra
    def rho_c_FD_extra(builder, axis_freq):
        dis = builder.build(time_dis, space_dis)
        return dis.analytic_robin_robin_modified(w=axis_freq,
                    order_time=0, order_operators=float('inf'),
                    order_equations=float('inf'))
    def rho_BE_FD_extra(builder, axis_freq):
        dis = builder.build(time_dis, space_dis)
        return dis.analytic_robin_robin_modified(w=axis_freq,
                    order_time=float('inf'), order_operators=float('inf'),
                    order_equations=float('inf'))

    def rho_m_FD(builder, axis_freq):
        dis = builder.build(time_dis, space_dis)
        return dis.analytic_robin_robin_modified(w=axis_freq,
                    order_time=1, order_operators=float('inf'),
                    order_equations=float('inf'))
    
    caracs = {}
    caracs["continuous"] = {'color':'#00AF80', 'width':0.7, 'nb_+':9}
    caracs["modified"] = {'color':'#0000FF', 'width':1., 'nb_+':12}
    caracs["discrete"] = {'color':'#000000', 'width':.9, 'nb_+':15}

    optiRatesGeneral(axes, rho_c_FD_extra, rho_m_FD, rho_BE_FD_extra, time_dis, space_dis, "BE", caracs=caracs)
    show_or_save("fig_OptiRatesBE")


def fig_optiRatesFD():
    fig, axes = plt.subplots(1, 1, figsize=[6.4*1, 4.8*1])
    from discretizations.time.backward_euler import BackwardEuler
    from discretizations.space.FD_extra import FiniteDifferencesExtra
    time_dis, space_dis = BackwardEuler, FiniteDifferencesExtra
    def rho_BE_c(builder, axis_freq):
        dis = builder.build(time_dis, space_dis)
        return dis.analytic_robin_robin_modified(w=axis_freq,
                    order_time=float('inf'), order_operators=0,
                    order_equations=0)
    def rho_BE_FD_extra(builder, axis_freq):
        dis = builder.build(time_dis, space_dis)
        return dis.analytic_robin_robin_modified(w=axis_freq,
                    order_time=float('inf'), order_operators=float('inf'),
                    order_equations=float('inf'))

    def rho_m_FD(builder, axis_freq):
        dis = builder.build(time_dis, space_dis)
        return dis.analytic_robin_robin_modified(w=axis_freq,
                    order_time=float('inf'), order_operators=float('inf'),
                    order_equations=2)
    
    caracs = {}
    caracs["continuous"] = {'color':'#00AF80', 'width':0.7, 'nb_+':9}
    caracs["modified"] = {'color':'#0000FF', 'width':1., 'nb_+':12}
    caracs["discrete"] = {'color':'#000000', 'width':.9, 'nb_+':15}

    optiRatesGeneral(axes, rho_BE_c, rho_m_FD, rho_BE_FD_extra, time_dis, space_dis, "FD", caracs=caracs)
    show_or_save("fig_OptiRatesFD")


def fig_optiRatesFV():
    fig, axes = plt.subplots(1, 1, figsize=[6.4*1, 4.8*1])
    from discretizations.time.backward_euler import BackwardEuler
    from discretizations.space.quad_splines_fv import QuadSplinesFV
    time_dis, space_dis = BackwardEuler, QuadSplinesFV
    def rho_BE_c(builder, axis_freq):
        dis = builder.build(time_dis, space_dis)
        return dis.analytic_robin_robin_modified(w=axis_freq,
                    order_time=float('inf'), order_operators=0,
                    order_equations=0)
    def rho_BE_FV(builder, axis_freq):
        dis = builder.build(time_dis, space_dis)
        return dis.analytic_robin_robin_modified(w=axis_freq,
                    order_time=float('inf'), order_operators=float('inf'),
                    order_equations=float('inf'))

    def rho_m_FV(builder, axis_freq):
        dis = builder.build(time_dis, space_dis)
        return dis.analytic_robin_robin_modified(w=axis_freq,
                    order_time=float('inf'), order_operators=float('inf'),
                    order_equations=2)
    
    caracs = {}
    caracs["continuous"] = {'color':'#00AF80', 'width':0.7, 'nb_+':9}
    caracs["modified"] = {'color':'#0000FF', 'width':1., 'nb_+':12}
    caracs["discrete"] = {'color':'#000000', 'width':.9, 'nb_+':15}

    optiRatesGeneral(axes, rho_BE_c, rho_m_FV, rho_BE_FV, time_dis, space_dis, "FV", caracs=caracs)
    show_or_save("fig_OptiRatesFV")

def optiRatesGeneral(axes, continuous_rate, modified_rate, discrete_rate, time_dis, space_dis, name_method="Unknown discretization", caracs={}, **args_for_discretization):
    """
        Creates a figure comparing analysis methods for a discretization.
        the functions "rate" should be:
        def discrete_rate(builder, axis_freq):
            dis = builder.build(time_dis, space_dis)
            return dis.analytic_robin_robin_modified(w=axis_freq,
                        order_time=float('inf'), order_operators=float('inf'),
                        order_equations=float('inf'))
    """

    setting = Builder()
    setting.M1 = 200
    setting.M2 = 200
    setting.D1 = .5
    setting.D2 = 1.
    setting.R = 1e-2
    setting.DT = 1.
    N = 30000
    axis_freq = get_discrete_freq(N, setting.DT)

    axes.set_xlabel("$\\omega \\Delta t$")
    axes.set_ylabel(r"${\rho}_{RR}$")
    #axes.set_title("Optimized convergence rates with different methods (" + name_method + ")")
    axes.set_title(name_method)

    def rate_onesided(lam):
        builder = setting.copy()
        builder.LAMBDA_1 = lam
        builder.LAMBDA_2 = -lam
        return np.max(continuous_rate(builder, axis_freq))
    from scipy.optimize import minimize_scalar, minimize
    optimal_lam = minimize_scalar(fun=rate_onesided)
    x0_opti = (optimal_lam.x, -optimal_lam.x)

    for discrete_factor, names in zip((continuous_rate, modified_rate, discrete_rate), caracs):
        if names == "modified":
            freq_opti = axis_freq # get_discrete_freq(N//10, setting.DT*10.)
        else:
            freq_opti = axis_freq


        def rate_twosided(lam):
            builder = setting.copy()
            builder.LAMBDA_1 = lam[0]
            builder.LAMBDA_2 = lam[1]
            return np.max(discrete_factor(builder, freq_opti))

        optimal_lam = minimize(method='Nelder-Mead',
                fun=rate_twosided, x0=x0_opti)
        if names == "continuous":
            x0_opti = optimal_lam.x
        print(optimal_lam)
        setting.LAMBDA_1 = optimal_lam.x[0]
        setting.LAMBDA_2 = optimal_lam.x[1]

        builder = setting.copy()
        if REAL_FIG:
            alpha_w = memoised(Builder.frequency_cv_factor, builder,
                    time_dis, space_dis, N=N, number_samples=32, NUMBER_IT=2) # WAS 7 IN CACHE
            convergence_factor = np.abs((alpha_w[2] / alpha_w[1]))
        else:
            convergence_factor = discrete_rate(setting, axis_freq)


        axis_freq_predicted = np.exp(np.linspace(np.log(min(np.abs(axis_freq))), np.log(axis_freq[-1]), caracs[names]["nb_+"]))

        # LESS IMPORTANT CURVE : WHAT IS PREDICTED

        axes.semilogx(axis_freq * setting.DT, convergence_factor, linewidth=caracs[names]["width"], label= "$p_1, p_2 =$ ("+ str(optimal_lam.x[0])[:4] +", "+ str(optimal_lam.x[1])[:5] + ")", color=caracs[names]["color"]+"90")
        if names =="discrete":
            axes.semilogx(axis_freq_predicted * setting.DT, discrete_factor(setting, axis_freq_predicted), marker="^", markersize=6., linewidth=0., color=caracs[names]["color"])# , label="prediction")
        else:
            axes.semilogx(axis_freq_predicted * setting.DT, discrete_factor(setting, axis_freq_predicted), marker="^", markersize=6., linewidth=0., color=caracs[names]["color"])

        axes.semilogx(axis_freq * setting.DT, np.ones_like(axis_freq)*max(convergence_factor), linestyle="dashed", linewidth=caracs[names]["width"], color=caracs[names]["color"]+"90")


    axes.legend( loc=(0., 0.), ncol=1 )
    axes.set_xlim(left=1e-4, right=3.4)
    #axes.set_ylim(bottom=0)

def fig_validatePadeAnalysisFDRR():
    from discretizations.space.FD_naive import FiniteDifferencesNaive
    from discretizations.space.FD_corr import FiniteDifferencesCorr
    from discretizations.space.FD_extra import FiniteDifferencesExtra
    from discretizations.space.quad_splines_fv import QuadSplinesFV
    from discretizations.space.fourth_order_fv import FourthOrderFV
    from discretizations.time.backward_euler import BackwardEuler
    from discretizations.time.theta_method import ThetaMethod
    from discretizations.time.RK2 import RK2
    from discretizations.time.RK4 import RK4
    from discretizations.time.PadeLowTildeGamma import PadeLowTildeGamma
    from discretizations.PadeFDCorr import PadeFDCorr
    from cv_factor_pade import rho_Pade_FD_corr0
    from cv_factor_pade import rho_Pade_FD_extra
    from cv_factor_pade import rho_Pade_c
    # parameters of the schemes are given to the builder:
    builder = Builder()
    builder.LAMBDA_1 = 1.11 # optimal parameters for corr=0, N=3000
    builder.LAMBDA_2 = -0.76
    builder.M1 = 200
    builder.M2 = 200
    builder.D1 = 1.
    builder.D2 = 2.
    builder.R = 0.5
    N = 300
    dt = builder.DT
    h = builder.SIZE_DOMAIN_1 / (builder.M1-1)
    print("Courant parabolic number :", builder.D1*dt/h**2)

    time_scheme = PadeLowTildeGamma
        
    discretizations = {}

    axis_freq = get_discrete_freq(N, dt)
    fig, axes = plt.subplots(1, 1, figsize=[6.4, 4.8])

    dis_cont = builder.build(time_scheme, FiniteDifferencesExtra) # any discretisation would do 
    continuous = dis_cont.analytic_robin_robin_modified(w=axis_freq,
                    order_time=0, order_operators=0,
                    order_equations=0)
    #axes.semilogx(axis_freq * dt, continuous, label="$\\rho^{\\rm c, c}$")

    #for name in discretizations:
    #time_dis, space_dis = discretizations[name]
    dis = builder.build(PadeLowTildeGamma, FiniteDifferencesExtra)
    # dis = builder.build_scheme(PadeFDCorr)
    print(dis.__dict__)


    theorical_convergence_factor = \
            dis.analytic_robin_robin_modified(w=axis_freq,
                    order_time=0, order_operators=float('inf'),
                    order_equations=float('inf'))

    
    cv_rate = memoised(Builder.frequency_cv_rate, builder,
            PadeLowTildeGamma, FiniteDifferencesExtra, N=N, number_samples=8, NUMBER_IT=2) # WAS 7 IN CACHE

    axes.semilogx(axis_freq * dt, np.abs(cv_rate),
            label="observed $\\rho^{\\rm c, "+"Pade, FD Corr=1" + "}$")

    axes.semilogx(axis_freq * dt, theorical_convergence_factor,
            label="$\\rho^{\\rm c, "+"Pade, FD Corr=1" + "}$")

    # theorical_convergence_factor = \
    #         dis.analytic_robin_robin_modified(w=axis_freq,
    #                 order_time=4, order_operators=float('inf'),
    #                 order_equations=float('inf'))
    # axes.semilogx(axis_freq * dt, theorical_convergence_factor,
    #         label="$\\rho^{\\rm modified, "+ "Pade, FD Corr=1" + "}$")


    # axes.semilogx(axis_freq * dt, rho_Pade_FD_corr0(builder, axis_freq),
    #         label="$\\rho^{\\rm Pade, FD(corr=0)}$")
    axes.semilogx(axis_freq * dt, rho_Pade_FD_extra(builder, axis_freq),
            label="$\\rho^{\\rm Pade, FD(extra)}$")
    # axes.semilogx(axis_freq * dt, rho_Pade_c(builder, axis_freq),
    #         label="$\\rho^{\\rm Pade, c}$")

    ###########
    # for each discretization, a simulation
    ###########
    # for name in discretizations:
    #     time_dis, space_dis = discretizations[name]
    #     alpha_w = memoised(Builder.frequency_cv_factor, builder,
    #             time_dis, space_dis, N=N, number_samples=5, NUMBER_IT=4)
    #     k = 1
    #     #convergence_factor = np.abs(alpha_w[k+1] / alpha_w[k])
    #     axes.semilogx(axis_freq * dt, convergence_factor, "--", label=name)

    axes.set_xlabel("Frequency variable $\\omega \\delta t$")
    axes.set_ylabel("Convergence factor $\\rho$")
    axes.set_title("Validation of finite differences discrete analysis")
    axes.legend()
    show_or_save("fig_validatePadeAnalysisFDRR")


def fig_validatePadeAnalysisFVRR():
    from discretizations.space.quad_splines_fv import QuadSplinesFV
    from discretizations.time.PadeLowTildeGamma import PadeLowTildeGamma
    from cv_factor_pade import rho_Pade_c
    from cv_factor_pade import rho_Pade_FV
    # parameters of the schemes are given to the builder:
    builder = Builder()
    builder.LAMBDA_1 = 1.
    builder.LAMBDA_2 = -0.5
    builder.M1 = 200
    builder.M2 = 200
    builder.D1 = 1.
    builder.D2 = 2.
    builder.R = 0.
    #builder.DT = 1e-3
    N = 300
    dt = builder.DT
    h = builder.SIZE_DOMAIN_1 / (builder.M1-1)
    print("Courant parabolic number :", builder.D1*dt/h**2)

    time_scheme = PadeLowTildeGamma
        
    axis_freq = get_discrete_freq(N, dt)
    fig, axes = plt.subplots(1, 1, figsize=[6.4, 4.8])

    # dis_cont = builder.build(time_scheme, QuadSplinesFV) # any discretisation would do 
    # continuous = dis_cont.analytic_robin_robin_modified(w=axis_freq,
    #                 order_time=0, order_operators=0,
    #                 order_equations=0)

    dis = builder.build(time_scheme, QuadSplinesFV)

    theorical_convergence_factor = \
            dis.analytic_robin_robin_modified(w=axis_freq,
                    order_time=0, order_operators=float('inf'),
                    order_equations=float('inf'))

    cv_rate_simulated = memoised(Builder.frequency_cv_rate, builder, time_scheme,
            QuadSplinesFV, N=N, number_samples=50, NUMBER_IT=2) # WAS 7 IN CACHE

    axes.semilogx(axis_freq * dt, theorical_convergence_factor,
            label="$\\rho^{\\rm FV, "+"c" + "}$")

    axes.semilogx(axis_freq * dt, rho_Pade_c(builder, axis_freq),
            label="$\\rho^{\\rm c, "+"Pade" + "}$")
 
    axes.semilogx(axis_freq * dt, np.abs(rho_Pade_FV(builder, axis_freq)),
            label="$\\rho^{\\rm FV, "+"Pade" + "}$")

    axes.semilogx(axis_freq * dt, np.abs(cv_rate_simulated), "--",
            label="observed $\\rho^{\\rm c, "+"Pade, FV" + "}$")


    axes.set_xlabel("Frequency variable $\\omega \\delta t$")
    axes.set_ylabel("Convergence factor $\\rho$")
    axes.set_title("Validation of Padé+ finite volumes discrete analysis")
    axes.legend()
    show_or_save("fig_validatePadeAnalysisFVRR")

def fig_validate_matrixlinear():
    from discretizations.space.FD_naive import FiniteDifferencesNaive
    from discretizations.space.FD_corr import FiniteDifferencesCorr
    from discretizations.space.FD_extra import FiniteDifferencesExtra
    from discretizations.space.quad_splines_fv import QuadSplinesFV
    from discretizations.space.fourth_order_fv import FourthOrderFV
    from discretizations.time.backward_euler import BackwardEuler
    from discretizations.time.theta_method import ThetaMethod
    from discretizations.time.RK2 import RK2
    from discretizations.time.RK4 import RK4
    from discretizations.time.PadeLowTildeGamma import PadeLowTildeGamma
    from discretizations.PadeFDCorr import PadeFDCorr
    from cv_factor_pade import rho_Pade_FD_corr0
    from cv_factor_pade import rho_Pade_FD_corr1
    from cv_factor_pade import rho_Pade_FD_extra
    from cv_factor_pade import rho_Pade_c
    # parameters of the schemes are given to the builder:
    builder = Builder()
    builder.LAMBDA_1 = 1.11 # optimal parameters for corr=0, N=3000
    builder.LAMBDA_2 = -0.76
    builder.M1 = 200
    builder.M2 = 200
    builder.D1 = 1.
    builder.D2 = 2.
    builder.R = 0.5
    N = 3000
    dt = builder.DT/10
    h = builder.SIZE_DOMAIN_1 / (builder.M1-1)
    print("Courant parabolic number :", builder.D1*dt/h**2)

    time_scheme = PadeLowTildeGamma
        
    discretizations = {}

    #discretizations["FV2"] = (time_scheme, QuadSplinesFV)
    #discretizations["FV4"] = (time_scheme, FourthOrderFV)
    #discretizations["FD(corr=0)"] = (time_scheme, FiniteDifferencesNaive)
    # discretizations["FD(extra)"] = (time_scheme, FiniteDifferencesExtra)

    axis_freq = get_discrete_freq(N, dt)
    fig, axes = plt.subplots(1, 1, figsize=[6.4, 4.8])

    dis_cont = builder.build(time_scheme, FiniteDifferencesNaive) # any discretisation would do 
    continuous = dis_cont.analytic_robin_robin_modified(w=axis_freq,
                    order_time=0, order_operators=0,
                    order_equations=0)
    #axes.semilogx(axis_freq * dt, continuous, label="$\\rho^{\\rm c, c}$")

    #for name in discretizations:
    #time_dis, space_dis = discretizations[name]
    dis = builder.build(time_dis, space_dis)
    #dis = builder.build_scheme(PadeFDCorr)

    theorical_convergence_factor = \
            dis.analytic_robin_robin_modified(w=axis_freq,
                    order_time=0, order_operators=float('inf'),
                    order_equations=float('inf'))

    u, phi = memoised(Builder.frequency_cv_factor_spacetime_scheme, builder,
            PadeFDCorr, ignore_cached=False, linear=False, N=N, number_samples=3, NUMBER_IT=4) # WAS 7 IN CACHE

    def det_uj_over_u1(j, u, phi):
        """
            for j=2 or 3, returns the ration of the determinants
            of U_k^j over U_k^1.
            with D1, D2 the eigenvalues of the transition matrix,
            the result of this function:
            -for j=1, is D1+D2
            - for j=2, is D2^2 + D1^2 + D1*D2
        """
        return (u[1] * phi[1+j] - phi[1] * u[1+j]) / (u[1] * phi[2] - phi[1] * u[2])

    R2 = det_uj_over_u1(2, u, phi)
    R3 = det_uj_over_u1(3, u, phi)
    assert not np.isnan(R2).any()
    assert not np.isnan(R3).any()

    #D1 and D2 are our two eigenvalues of interest.
    from numpy.lib import scimath
    D1 = (R2 + scimath.sqrt(4 * R3 - 3*R2*R2))/2
    D2 = (R2 - scimath.sqrt(4 * R3 - 3*R2*R2))/2

    axes.semilogx(axis_freq * dt, np.abs(D1),
            label="observed $\\rho^{\\rm c, "+"Pade, FD Corr=1" + "}$")
    axes.semilogx(axis_freq * dt, np.abs(D2),
            label="observed $\\rho^{\\rm c, "+"Pade, FD Corr=1" + "}$")

    axes.semilogx(axis_freq * dt, theorical_convergence_factor,
            label="$\\rho^{\\rm c, "+"Pade, FD Corr=1" + "}$")

    # theorical_convergence_factor = \
    #         dis.analytic_robin_robin_modified(w=axis_freq,
    #                 order_time=4, order_operators=float('inf'),
    #                 order_equations=float('inf'))
    # axes.semilogx(axis_freq * dt, theorical_convergence_factor,
    #         label="$\\rho^{\\rm modified, "+ "Pade, FD Corr=1" + "}$")


    axes.semilogx(axis_freq * dt, rho_Pade_FD_corr1(builder, axis_freq)[0],
            label="$\\rho^{\\rm Pade, FD(corr=1)}$")
    axes.semilogx(axis_freq * dt, rho_Pade_FD_corr1(builder, axis_freq)[1],
            label="$\\rho^{\\rm Pade, FD(corr=1)}$")
    # axes.semilogx(axis_freq * dt, rho_Pade_FD_extra(builder, axis_freq),
    #         label="$\\rho^{\\rm Pade, FD(extra)}$")
    # axes.semilogx(axis_freq * dt, rho_Pade_c(builder, axis_freq),
    #         label="$\\rho^{\\rm Pade, c}$")

    ###########
    # for each discretization, a simulation
    ###########
    for name in discretizations:
        time_dis, space_dis = discretizations[name]
        alpha_w = memoised(Builder.frequency_cv_factor, builder,
                time_dis, space_dis, N=N, number_samples=5, NUMBER_IT=4)
        k = 1
        convergence_factor = np.abs(alpha_w[k+1] / alpha_w[k])
        axes.semilogx(axis_freq * dt, convergence_factor, "--", label=name)
        # k = 2
        # convergence_factor = np.abs(alpha_w[k+1] / alpha_w[k])
        # axes.semilogx(axis_freq * dt, convergence_factor, "--", label=name)
        # k = 3
        # convergence_factor = np.abs(alpha_w[k+1] / alpha_w[k])
        # axes.semilogx(axis_freq * dt, convergence_factor, "--", label=name)

    axes.set_xlabel("Frequency variable $\\omega \\delta t$")
    axes.set_ylabel("Convergence factor $\\rho$")
    axes.set_title("Validation of finite differences discrete analysis")
    axes.legend()
    show_or_save("fig_validatePadeAnalysisFDRR")

def fig_validate_validation():
    from discretizations.space.FD_extra import FiniteDifferencesExtra
    from discretizations.time.PadeLowTildeGamma import PadeLowTildeGamma
    from cv_factor_pade import rho_Pade_FD_extra
    # parameters of the schemes are given to the builder:
    builder = Builder()
    builder.LAMBDA_1 = 1.11 # optimal parameters for corr=0, N=3000
    builder.LAMBDA_2 = -0.76
    builder.M1 = 200
    builder.M2 = 200
    builder.D1 = 1.
    builder.D2 = 2.
    builder.R = 0.5
    N = 100
    dt = builder.DT
    h = builder.SIZE_DOMAIN_1 / (builder.M1-1)
    print("Courant parabolic number :", builder.D1*dt/h**2)

    time_scheme = PadeLowTildeGamma
        
    discretizations = {}

    axis_freq = get_discrete_freq(N, dt)
    fig, axes = plt.subplots(1, 1, figsize=[6.4, 4.8])

    dis_cont = builder.build(time_scheme, FiniteDifferencesExtra) # any discretisation would do 

    dis = builder.build(time_scheme, FiniteDifferencesExtra)

    # u, phi = memoised(Builder.frequency_cv_factor, builder, time_scheme, FiniteDifferencesExtra,
    #         ignore_cached=False, linear=False, N=N, number_samples=3000, NUMBER_IT=4) # WAS 7 IN CACHE

    # def det_uj_over_u1(j, u, phi):
    #     """
    #         for j=2 or 3, returns the ration of the determinants
    #         of U_k^j over U_k^1.
    #         with D1, D2 the eigenvalues of the transition matrix,
    #         the result of this function:
    #         -for j=1, is D1+D2
    #         - for j=2, is D2^2 + D1^2 + D1*D2
    #     """
    #     return (u[1] * phi[1+j] - phi[1] * u[1+j]) / (u[1] * phi[2] - phi[1] * u[2])

    # R2 = det_uj_over_u1(2, u, phi)
    # R3 = det_uj_over_u1(3, u, phi)
    # assert not np.isnan(R2).any()
    # assert not np.isnan(R3).any()

    # #D1 and D2 are our two eigenvalues of interest.
    # from numpy.lib import scimath
    # D1 = (R2 + scimath.sqrt(4 * R3 - 3*R2*R2))/2
    # D2 = (R2 - scimath.sqrt(4 * R3 - 3*R2*R2))/2
    D1, D2 =  memoised(Builder.frequency_eigenvalues, builder, time_scheme, FiniteDifferencesExtra,
            ignore_cached=False, N=N, number_samples=64, NUMBER_IT=4) # WAS 7 IN CACHE


    # axes.loglog(axis_freq * dt, np.mean(np.abs(np.real(D1).T), axis=1), "+",
    #         label="observed first eigenvalue")
    # axes.semilogx(axis_freq * dt, np.mean(np.abs(np.real(D2).T), axis=1), "--",
    #         label="observed second eigenvalue")
    axes.loglog(axis_freq * dt, np.mean(np.abs((D1).T), axis=1), "+",
            label="observed first eigenvalue")
    axes.semilogx(axis_freq * dt, np.mean(np.abs((D2).T), axis=1), "--",
            label="observed second eigenvalue")

    axes.semilogx(axis_freq * dt, rho_Pade_FD_extra(builder, axis_freq),
            label="$\\rho^{\\rm Pade, FD(extra)}$")

    axes.set_xlabel("Frequency variable $\\omega \\delta t$")
    axes.set_ylabel("Convergence factor $\\rho$")
    axes.set_title("Validation of finite differences discrete analysis")
    axes.legend()


    show_or_save("fig_validate_validation")

def fig_validate_validate_validation():
    A0 = np.random.rand(2)
    F = np.random.rand(2, 2)
    D = np.array(((1e-5, 0), (0, 3.234567))) # very ill-conditionned
    u = np.array(((F @ D @ A0)[0], (F @ D @D@ A0)[0], (F @ D@D@D @ A0)[0], (F @ D@D@D@D @ A0)[0], (F @ D@D@D@D @D@ A0)[0]))
    phi = np.array(((F @ D @ A0)[1], (F @ D @D@ A0)[1], (F @ D@D@D @ A0)[1], (F @ D@D@D@D @ A0)[1], (F @ D@D@D@D @D@ A0)[1]))
    import scipy
    from scipy import linalg
    def det_uj_over_u1(j, u, phi):
        """
            for j=2 or 3, returns the ration of the determinants
            of U_k^j over U_k^1.
            with D1, D2 the eigenvalues of the transition matrix,
            the result of this function:
            -for j=1, is D1+D2
            - for j=2, is D2^2 + D1^2 + D1*D2
        """
        u1 = np.array(((u[1], phi[1]),(u[2],phi[2])))
        uj = np.array(((u[1], phi[1]),(u[1+j],phi[1+j])))
        return scipy.linalg.det(uj) / scipy.linalg.det(u1)

    R2 = det_uj_over_u1(2, u, phi)
    R3 = det_uj_over_u1(3, u, phi)
    assert not np.isnan(R2).any()
    assert not np.isnan(R3).any()
    print("R2, R3:", R2,R3)
    print("under the sqrt:", 4 * R3 - 3*R2*R2)

    #D1 and D2 are our two eigenvalues of interest.
    from numpy.lib import scimath
    D1 = (R2 + scimath.sqrt(4 * R3 - 3*R2*R2))/2
    D2 = (R2 - scimath.sqrt(4 * R3 - 3*R2*R2))/2
    print(D1, D2)



def fig_optimized_rho():
    from cv_factor_pade import rho_Pade_FD_corr0, rho_Pade_c, rho_Pade_FD_extra
    discrete_factor = rho_Pade_c
    setting = Builder()
    setting.M1 = 200
    setting.M2 = 200
    setting.D1 = 1.
    setting.D2 = 2.
    setting.R = 0.5
    setting.DT /= 100
    N = 3000
    axis_freq = get_discrete_freq(N, setting.DT)
    def convergence_factor(lam):
        builder = setting.copy()
        builder.LAMBDA_1 = lam[0]
        builder.LAMBDA_2 = lam[1]
        return np.max(discrete_factor(builder, axis_freq))

    def convergence_factor(lam):
        builder = setting.copy()
        builder.LAMBDA_1 = lam
        builder.LAMBDA_2 = -lam
        return np.max(discrete_factor(builder, axis_freq))

    from scipy.optimize import minimize_scalar, minimize
    optimal_lam = minimize_scalar(fun=convergence_factor)
    print(optimal_lam)
    setting.LAMBDA_1 = optimal_lam.x
    setting.LAMBDA_2 = -optimal_lam.x
    plt.semilogx(axis_freq * setting.DT, discrete_factor(setting, axis_freq),
            label="$\\rho^{\\rm Pade, FD(corr=0)}$")

    show_or_save("fig_optimized_rho")

def fig_compare_discrete_modif():
    import matplotlib as mpl
    mpl.rc('text', usetex=True)
    mpl.rcParams['text.latex.preamble']=[r"\usepackage{amsmath}"]
    from discretizations.time.PadeLowTildeGamma import PadeLowTildeGamma as Pade
    from discretizations.time.backward_euler import BackwardEuler as BE
    from discretizations.space.FD_naive import FiniteDifferencesNaive as FD
    from discretizations.space.FD_extra import FiniteDifferencesExtra as FD
    from discretizations.space.quad_splines_fv import QuadSplinesFV as FV
    from cv_factor_pade import rho_Pade_FD_corr0, rho_Pade_c, rho_Pade_FD_extra
    fig, axes = plt.subplots(2, 2, figsize=[6.4, 4.4], sharex=False, sharey=True)
    plt.subplots_adjust(left=.11, bottom=.28, right=.99, top=.92, wspace=0.19, hspace=0.34)
    COLOR_CONT = '#FF3333FF'
    COLOR_CONT_FD = '#AA0000FF'
    COLOR_MODIF = '#000000FF'

    for r, axes in ((0, axes[0,:]), (.1, axes[1,:])):
        setting = Builder()
        setting.R = r

        setting.LAMBDA_1 = 1.
        setting.LAMBDA_2 = -1.
        setting.M1 = 200
        setting.M2 = 200
        setting.D1 = 1.
        setting.D2 = 1.
        dt = setting.DT
        # N = 30
        # axis_freq = get_discrete_freq(N, setting.DT)
        axis_freq = np.exp(np.linspace(-5, np.log(pi), 10000))/dt

        #########################################################
        # LEFT CANVA: TIME COMPARISON
        #########################################################

        space_dis = FD
        dis = setting.build(Pade, space_dis)

        cont_time = dis.analytic_robin_robin_modified(w=axis_freq,
                order_time=0, order_equations=0, order_operators=0) #continuous in time
        modif_time = dis.analytic_robin_robin_modified(w=axis_freq,
                order_time=2, order_equations=0, order_operators=0) # modified in time

        b = 1+1/np.sqrt(2)
        def gamma_order2(z):
            return z - b*(z-1) - b/2 * (z-1)**2

        def gamma_order1(z):
            return z - b*(z-1)

        ######################
        # TIME SCHEME : GAMMA ORDER 2:
        ######################
        axis = axes[1]

        full_discrete = rho_Pade_c(setting, w=axis_freq, gamma=gamma_order2) # disccrete in time
        lineg2, = axis.semilogx(axis_freq*dt, np.abs(full_discrete - modif_time)/np.abs(full_discrete), linewidth='1.1',
                color=COLOR_MODIF, linestyle='solid')
        axis.semilogx(axis_freq*dt, np.abs(full_discrete - cont_time)/np.abs(full_discrete), linewidth='1.1',
                color=COLOR_CONT, linestyle='solid')

        ######################
        # TIME SCHEME : GAMMA ORDER 1:
        ######################

        full_discrete = rho_Pade_c(setting, w=axis_freq, gamma=gamma_order1) # disccrete in time

        lineg1, = axis.semilogx(axis_freq*dt, np.abs(full_discrete - modif_time)/np.abs(full_discrete), linewidth='1.1',
                color=COLOR_MODIF, linestyle='dashed')
        axis.semilogx(axis_freq*dt, np.abs(full_discrete - cont_time)/np.abs(full_discrete), linewidth='1.1',
                color=COLOR_CONT, linestyle='dashed')

        ########################
        # TIME SCHEME : Backward Euler
        #########################
        dis = setting.build(BE, space_dis)

        modif_time = dis.analytic_robin_robin_modified(w=axis_freq,
                order_time=2, order_equations=0, order_operators=0) # modified in time
        full_discrete = dis.analytic_robin_robin_modified(w=axis_freq,
                order_time=float('inf'), order_equations=0, order_operators=0) # discrete in time

        linebe, = axis.semilogx(axis_freq*dt, np.abs(full_discrete - modif_time)/np.abs(full_discrete),
                color=COLOR_MODIF, linestyle=':', linewidth="2.3")
        axis.semilogx(axis_freq*dt, np.abs(full_discrete - cont_time)/np.abs(full_discrete),
                color=COLOR_CONT, linestyle=':', linewidth="2.3")

        axis.grid(True,color='k', linestyle='dotted', linewidth=0.25)
        axis.set_xlim(left=0.9e-2, right=.7)
        #axis.set_ylim(top=0.1, bottom=0.) #sharey activated : see axis.set_xlim
        Title = r'Semi-discrete in time' #Title = r'$d\rho_{\rm RR}^{\rm (\cdot,c)}$'
        #x_legend= r'$\left| \rho_{\rm RR}^{\rm (\cdot,c)} - \rho_{\rm RR}^{\rm (Discrete,c)}\right|/\left|\rho_{\rm RR}^{\rm (Discrete,c)}\right| $'
        if r == 0:
            axis.set_title(Title)
            axis.set_xticklabels([])
        else:
            axis.set_xlabel(r'$\omega\Delta t$')

        #########################################################
        # RIGHT CANVA: SPACE COMPARISON
        #########################################################
        time_dis = BE # we don't really care, since everything is continuous in time now

        ######################
        # SPACE SCHEME : FV
        ######################
        dis = setting.build(time_dis, FV)

        cont_space = dis.analytic_robin_robin_modified(w=axis_freq,
                order_time=0, order_equations=0, order_operators=float('inf')) #continuous in time

        modif_space = dis.analytic_robin_robin_modified(w=axis_freq,
                order_time=0, order_equations=2, order_operators=float('inf')) # modified in time

        full_discrete = dis.analytic_robin_robin_modified(w=axis_freq,
                order_time=0, order_equations=float('inf'), order_operators=float('inf'))

        axis = axes[0]

        axis.semilogx(axis_freq*dt, np.abs(full_discrete - modif_space)/np.abs(full_discrete), linewidth='2.',
                color=COLOR_MODIF, linestyle='solid')
        axis.semilogx(axis_freq*dt, np.abs(full_discrete - cont_space)/np.abs(full_discrete), linewidth='2.',
                color=COLOR_CONT, linestyle='solid')

        ######################
        # SPACE SCHEME : FD
        ######################
        dis = setting.build(time_dis, FD)

        cont_space = dis.analytic_robin_robin_modified(w=axis_freq,
                order_time=0, order_equations=0, order_operators=float('inf')) #continuous in time

        modif_space = dis.analytic_robin_robin_modified(w=axis_freq,
                order_time=0, order_equations=2, order_operators=float('inf')) # modified in time

        full_discrete = dis.analytic_robin_robin_modified(w=axis_freq,
                order_time=0, order_equations=float('inf'), order_operators=float('inf'))

        axis.semilogx(axis_freq*dt, np.abs(full_discrete - modif_space)/np.abs(full_discrete), linewidth='2.',
                color=COLOR_MODIF, linestyle='dashed')
        axis.semilogx(axis_freq*dt, np.abs(full_discrete - cont_space)/np.abs(full_discrete), linewidth='2.',
                color=COLOR_CONT_FD, linestyle='dashed')

        axis.grid(True,color='k', linestyle='dotted', linewidth=0.25)
        axis.set_xlim(left=2e-2, right=3)
        axis.set_ylim(top=0.03, bottom=0.)
        Title = r'Semi-discrete in space' #r'$d\rho_{\rm RR}^{\rm (c, \cdot)}$'
        axis.set_ylabel(r'$r=' + str(r) + r'\;{\rm s}^{-1}$')
        if r == 0:
            #axis.legend()
            axis.set_title(Title)
            axis.set_xticklabels([])
        else:
            axis.set_xlabel(r'$\omega$')


    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    custom_lines = [
                    Patch(facecolor=COLOR_MODIF),
                    Patch(facecolor=COLOR_CONT),
                    Line2D([0],[0],color="w"),
                    Line2D([0], [0], lw=2., color='black'),
                    Line2D([0], [0], linestyle='dashed', lw=2., color='black'),
                    Line2D([0],[0],color="w"),
                    Line2D([0], [0], lw=1.2, color='black'),
                    Line2D([0], [0], linestyle='dashed', lw=1.2, color='black'),
                    Line2D([0], [0], linestyle='dotted', lw=1.6, color='black'),
                    ]

    custom_labels = [
            r'$(\delta \rho)_\mathbf{m}^{\rm (\cdot, \cdot)}$',
            r'$(\delta \rho)_\mathbf{c}^{\rm (\cdot, \cdot)}$',
            r"",
            r"$(\delta\rho)^{\rm (c, \mathbf{FV})}$", r"$(\delta\rho)^{\rm (c, \mathbf{FD})}$",
            r"",
            r"$(\delta\rho)^{\rm (\mathbf{P2}, c)}$" + ", " + r"$\gamma = z - \beta (z-1)$" + r"$- \beta(\beta-1)^2(z-1)^2$",
            r"$(\delta\rho)^{\rm (\mathbf{P2}, c)}$" + ", " + r"$\gamma = z - \beta (z-1)$",
            r"$(\delta\rho)^{\rm (\mathbf{BE}, c)}$",]
    fig.legend(custom_lines, custom_labels, loc=(0.10, 0.), ncol=3)
    fig.tight_layout()   
    fig.subplots_adjust(bottom=.28, wspace=.2)

    show_or_save("fig_compare_discrete_modif")

def fig_operators_FD():
    operators_disc_cont(corrective_term=False)
    show_or_save("fig_operators_FD")

def fig_operators_FD_corr():
    operators_disc_cont(corrective_term=True)
    show_or_save("fig_operators_FD_corr")

def operators_disc_cont(corrective_term=True):
    from discretizations.time.backward_euler import BackwardEuler as BE
    from discretizations.space.FD_naive import FiniteDifferencesNaive as FD_naive
    from discretizations.space.FD_corr import FiniteDifferencesCorr as FD_corr
    fig, axes = plt.subplots(1, 2, figsize=[6.4, 2.4], sharex=False, sharey=True)
    axes[0].set_ylabel(r'${\rho}$')
    plt.subplots_adjust(left=.11, bottom=.24, right=.99, top=.85, wspace=0.19, hspace=0.15)
    COLOR_CONT = '#FF0000FF'
    COLOR_CONT_FD = '#555555FF'
    COLOR_DIS = '#000000FF'

    for r, ax in ((0, axes[0]), (1., axes[1])):
        setting = Builder()
        setting.R = r

        setting.LAMBDA_1 = 1e9 # optimal parameters for corr=0, N=3000
        setting.LAMBDA_2 = 0.
        setting.M1 = 200
        setting.M2 = 200
        setting.D1 = .5
        setting.D2 = 1.
        dt = setting.DT/100
        # N = 30
        # axis_freq = get_discrete_freq(N, setting.DT)
        axis_freq = np.exp(np.linspace(-10, np.log(pi), 10000))/dt

        #########################################################
        # LEFT CANVA: TIME COMPARISON
        #########################################################

        if corrective_term:
            space_dis = FD_corr
        else:
            space_dis = FD_naive
        dis = setting.build(BE, space_dis)

        cont_operators = dis.analytic_robin_robin_modified(w=axis_freq,
                order_time=0, order_equations=0, order_operators=0) #continuous in time
        discrete_operators = dis.analytic_robin_robin_modified(w=axis_freq,
                order_time=0, order_equations=0, order_operators=float('inf')) # discrete


        ax.semilogx(axis_freq, cont_operators,
                color=COLOR_CONT, linewidth="1.8", label="Continuous")
        ax.semilogx(axis_freq, discrete_operators,
                color=COLOR_DIS, linestyle='--', linewidth="1.8", label="Discrete")

        ax.grid(True, color='k', linestyle='dotted', linewidth=0.25) 
        #ax[0].set_ylim(top=0.1, bottom=0.) #sharey activated : see ax[1].set_xlim
        ax.set_title(r'$r=' + str(r) + r'\;{\rm s}^{-1}$')
        Title = r'$d\rho_{\rm RR}^{\rm (\cdot,c)}$'
        #x_legend= r'$\left| \rho_{\rm RR}^{\rm (\cdot,c)} - \rho_{\rm RR}^{\rm (Discrete,c)}\right|/\left|\rho_{\rm RR}^{\rm (Discrete,c)}\right| $'
        ax.set_ylabel(r'${\rho}$')
        ax.set_xlabel(r'$\omega$')
    axes[0].legend()
    show_or_save("fig_FD_disc_modif")

def fig_FD_disc_cont():
    from discretizations.time.backward_euler import BackwardEuler as BE
    from discretizations.space.FD_naive import FiniteDifferencesNaive as FD_naive
    from discretizations.space.FD_corr import FiniteDifferencesCorr as FD_corr
    fig, axes = plt.subplots(1, 2, figsize=[6.4, 2.4], sharex=False, sharey=True)
    plt.subplots_adjust(left=.11, bottom=.24, right=.99, top=.85, wspace=0.19, hspace=0.15)
    COLOR_CONT = '#FF0000FF'
    COLOR_CONT_FD = '#555555FF'
    COLOR_DIS = '#000000FF'

    for r, ax in ((0, axes[0]), (1., axes[1])):
        setting = Builder()
        setting.R = r

        setting.LAMBDA_1 = 1e9 # optimal parameters for corr=0, N=3000
        setting.LAMBDA_2 = 0.
        setting.M1 = 200
        setting.M2 = 200
        setting.D1 = .5
        setting.D2 = 1.
        dt = setting.DT/1000000
        # N = 30
        # axis_freq = get_discrete_freq(N, setting.DT)
        axis_freq = np.exp(np.linspace(-17, np.log(pi), 10000))/dt

        #########################################################
        # LEFT CANVA: TIME COMPARISON
        #########################################################

        dis = setting.build(BE, FD_naive)

        cont_operators = dis.analytic_robin_robin_modified(w=axis_freq,
                order_time=0, order_equations=0, order_operators=0) #continuous in time
        discrete_operators = dis.analytic_robin_robin_modified(w=axis_freq,
                order_time=0, order_equations=float('inf'), order_operators=0)


        ax.semilogx(axis_freq, cont_operators,
                color=COLOR_CONT, linewidth="1.8", label="Continuous")
        ax.semilogx(axis_freq, discrete_operators,
                color=COLOR_DIS, linestyle='--', linewidth="1.8", label="Discrete")

        ax.grid(True, color='k', linestyle='dotted', linewidth=0.25) 
        #ax[0].set_ylim(top=0.1, bottom=0.) #sharey activated : see ax[1].set_xlim
        ax.set_title(r'$r=' + str(r) + r'\;{\rm s}^{-1}$')
        Title = r'$d\rho_{\rm RR}^{\rm (\cdot,c)}$'
        #x_legend= r'$\left| \rho_{\rm RR}^{\rm (\cdot,c)} - \rho_{\rm RR}^{\rm (Discrete,c)}\right|/\left|\rho_{\rm RR}^{\rm (Discrete,c)}\right| $'
        ax.set_ylabel(r'${\rho}$')
        ax.set_xlabel(r'$\omega$')
    axes[0].legend()
    show_or_save("fig_FD_disc_cont")

def fig_optimized_rho_BE_FV():
    from cv_factor_pade import rho_Pade_FD_corr0, rho_Pade_c, rho_Pade_FD_extra
    from discretizations.time.backward_euler import BackwardEuler
    from discretizations.time.RK2 import RK2
    from discretizations.space.fourth_order_fv import FourthOrderFV
    time_dis = BackwardEuler
    space_dis = FourthOrderFV
    setting = Builder()
    setting.R = .0
    N = 3000
    axis_freq = get_discrete_freq(N, setting.DT)
    def convergence_factor(lam):
        builder = setting.copy()
        builder.LAMBDA_1 = lam[0]
        builder.LAMBDA_2 = lam[1]
        dis = builder.build(time_dis, space_dis)
        return dis.analytic_robin_robin_modified(w=axis_freq,
            order_time=float('inf'), order_equations=float('inf'), order_operators=float('inf'))

    def to_minimize(lam):
        return np.max(np.abs(convergence_factor(lam)))

    from scipy.optimize import minimize_scalar, minimize
    optimal_lam = minimize(fun=to_minimize, x0=(.5, -.5))
    print(optimal_lam)
    plt.semilogx(axis_freq * setting.DT, convergence_factor(optimal_lam.x),
            label="$\\rho^{\\rm Pade, FD(corr=0)}$")

    show_or_save("fig_optimized_rho_BE_FV")

def fig_impact_DT_pade_DN():
    from cv_factor_pade import rho_Pade_FD_corr0, rho_Pade_c, rho_Pade_FD_extra
    setting = Builder()
    setting.R = .0
    setting.D2 = 2.
    N = 300
    axis_freq = get_discrete_freq(N, setting.DT)

    plt.semilogx(axis_freq * setting.DT, rho_Pade_c(setting, axis_freq),
            label="$\\rho^{\\rm Pade, FD(corr=0)}$, dt1")
    setting.R += .1
    axis_freq = get_discrete_freq(N, setting.DT)
    plt.semilogx(axis_freq * setting.DT, rho_Pade_c(setting, axis_freq),
            "--", label="$\\rho^{\\rm Pade, FD(corr=0)}$, dt2")
    setting.R += 1.
    axis_freq = get_discrete_freq(N, setting.DT)
    plt.semilogx(axis_freq * setting.DT, rho_Pade_c(setting, axis_freq),
            "k-.", label="$\\rho^{\\rm Pade, FD(corr=0)}$, dt3")

    show_or_save("fig_optimized_rho")


def fig_compareSettingsDirichletNeumann():
    from discretizations.space.FD_naive import FiniteDifferencesNaive
    from discretizations.space.FD_corr import FiniteDifferencesCorr
    from discretizations.space.FD_extra import FiniteDifferencesExtra
    from discretizations.space.quad_splines_fv import QuadSplinesFV
    from discretizations.space.fourth_order_fv import FourthOrderFV
    from discretizations.time.backward_euler import BackwardEuler
    from discretizations.time.theta_method import ThetaMethod
    from discretizations.time.RK2 import RK2
    from discretizations.time.RK4 import RK4
    from discretizations.time.PadeLowTildeGamma import PadeLowTildeGamma
    # parameters of the schemes are given to the builder:
    builder = Builder()
    builder.LAMBDA_1 = 1e9  # extremely high lambda is a Dirichlet condition
    builder.LAMBDA_2 = 0. # lambda=0 is a Neumann condition
    builder.D1 = 1.
    builder.D2 = 2.
    builder.R = 0.4
    dt = builder.DT
    assert builder.R * builder.DT < 1
        
    discretizations = {}
    time_scheme = PadeLowTildeGamma

    discretizations["FV2"] = (time_scheme, QuadSplinesFV)
    discretizations["FV4"] = (time_scheme, FourthOrderFV)
    discretizations["FD, extra"] = (time_scheme, FiniteDifferencesExtra)
    discretizations["FD, corr=0"] = (time_scheme, FiniteDifferencesNaive)
    #discretizations["FD, corr=1"] = (time_scheme, FiniteDifferencesCorr)

    convergence_factors = {}
    theorical_convergence_factors = {}

    N = 300
    axis_freq = get_discrete_freq(N, builder.DT)

    kwargs_label_simu = {'label':"Validation by simulation"}
    fig, axes = plt.subplots(1, 2, figsize=[6.4 * 1.7, 4.8], sharey=True)
    ###########
    # for each discretization, a simulation
    ###########
    for name in discretizations:
        time_dis, space_dis = discretizations[name]
        alpha_w = memoised(Builder.frequency_cv_factor, builder, time_dis, space_dis, N=N, number_samples=5)
        k = 1
        convergence_factors[name] = alpha_w[k+1] / alpha_w[k]

        dis = builder.build(time_dis, space_dis)
        theorical_convergence_factors[name] = \
                dis.analytic_robin_robin_modified(w=axis_freq,
                        order_time=0, order_operators=float('inf'),
                        order_equations=float('inf'))
        # continuous = dis.analytic_robin_robin_modified(w=axis_freq,
        #                 order_time=0, order_operators=float('inf'),
        #                 order_equations=float('inf'))
        # plt.plot(axis_freq * dt, continuous, "--", label="Continuous Theorical " + name)
        #axes[0].semilogx(axis_freq * dt, convergence_factors[name], "k--", **kwargs_label_simu)
        axes[0].semilogx(axis_freq * dt, convergence_factors[name], label=name)
        if kwargs_label_simu: # We only want the legend to be present once
            kwargs_label_simu = {}
        #axes[0].semilogx(axis_freq * dt, theorical_convergence_factors[name], label=name+ " theorical")
    w, rho_theoric = wAndRhoPadeRR(builder)
    axes[0].semilogx(w*builder.DT, rho_theoric, "k--", label="theoric")

    axes[0].set_xlabel("Frequency variable $\\omega \\delta t$")
    axes[0].set_ylabel("Convergence factor $\\rho$")
    axes[0].set_title("Various space discretizations with " + time_scheme.__name__)

    axes[1].set_xlabel("Frequency variable $\\omega \\delta t$")
    axes[1].set_ylabel("Convergence factor $\\rho$")
    axes[1].set_title("Various time discretizations with Finite Differences, Corr=0")

    space_scheme = FiniteDifferencesNaive
    discretizations = {}

    discretizations["BackwardEuler"] = (BackwardEuler, space_scheme)
    discretizations["ThetaMethod"] = (ThetaMethod, space_scheme)
    # discretizations["RK2"] = (RK2, space_scheme)
    # discretizations["RK4"] = (RK4, space_scheme)
    discretizations["PadeLowTildeGamma"] = (PadeLowTildeGamma, space_scheme)

    kwargs_label_simu = {'label':"Validation by simulation"}

    for name in discretizations:
        time_dis, space_dis = discretizations[name]
        alpha_w = memoised(Builder.frequency_cv_factor, builder, time_dis, space_dis, N=N, number_samples=5)
        k = 1
        convergence_factors[name] = alpha_w[k+1] / alpha_w[k]

        dis = builder.build(time_dis, space_dis)
        theorical_convergence_factors[name] = \
                dis.analytic_robin_robin_modified(w=axis_freq,
                        order_time=0, order_operators=float('inf'),
                        order_equations=float('inf'))
        # continuous = dis.analytic_robin_robin_modified(w=axis_freq,
        #                 order_time=0, order_operators=float('inf'),
        #                 order_equations=float('inf'))
        # plt.plot(axis_freq * dt, continuous, "--", label="Continuous Theorical " + name)
        axes[1].semilogx(axis_freq * dt, convergence_factors[name], label=name)

    axes[0].legend()
    axes[1].legend()
    show_or_save("fig_compareSettingsDirichletNeumann")

def fig_PadeFDInteraction():
    from discretizations.space.FD_naive import FiniteDifferencesNaive
    from discretizations.space.FD_corr import FiniteDifferencesCorr
    from discretizations.space.FD_extra import FiniteDifferencesExtra
    from discretizations.space.quad_splines_fv import QuadSplinesFV
    from discretizations.space.fourth_order_fv import FourthOrderFV
    from discretizations.time.backward_euler import BackwardEuler
    from discretizations.time.PadeLowTildeGamma import PadeLowTildeGamma
    from cv_factor_pade import rho_Pade_FD_corr0, rho_Pade_c, rho_Pade_FD_extra
    # parameters of the schemes are given to the builder:
    builder = Builder()
    builder.LAMBDA_1 = 1e9  # extremely high lambda is a Dirichlet condition
    builder.LAMBDA_2 = 0. # lambda=0 is a Neumann condition
    builder.D1 = 1.
    builder.D2 = 2.
    builder.R = 0.01
    dt = builder.DT
    assert builder.R * builder.DT < 1
        
    discretizations = {}
    time_scheme = PadeLowTildeGamma

    # discretizations["FDextra"] = (time_scheme, FiniteDifferencesExtra)
    discretizations["FDnaive"] = (time_scheme, FiniteDifferencesNaive)
    # discretizations["FDcorr"] = (time_scheme, FiniteDifferencesCorr)
    # discretizations["FV"] = (time_scheme, QuadSplinesFV)
    def LowTilde_gamma(z):
        b = 1+1/np.sqrt(2)
        return z - b*(z-1) - b/2 * (z-1)**2
    def simple_gamma(z):
        b = 1+1/np.sqrt(2)
        return z - b*(z-1)

    for name in discretizations:
        time_dis, space_dis = discretizations[name]

        for dt in (1e1, 1e0, 1e-1, 1e-2, 1e-3):
            builder.DT = dt
            dis = builder.build(time_dis, space_dis)
            axis_freq = get_discrete_freq(1000/dt, builder.DT)
            theorical_convergence_factors = rho_Pade_FD_corr0(builder, axis_freq, gamma=simple_gamma)

            axes.semilogx(axis_freq, theorical_convergence_factors, label="dt is "+str(dt))

    axes.legend()
    show_or_save("fig_compareSettingsDirichletNeumann")

def fig_DNInteraction():
    import matplotlib as mpl
    mpl.rc('text', usetex=True)
    mpl.rcParams['text.latex.preamble']=[r"\usepackage{amsmath}"]
    from discretizations.space.FD_naive import FiniteDifferencesNaive
    from discretizations.space.FD_corr import FiniteDifferencesCorr
    from discretizations.space.FD_extra import FiniteDifferencesExtra
    from discretizations.space.quad_splines_fv import QuadSplinesFV
    from discretizations.space.fourth_order_fv import FourthOrderFV
    from discretizations.time.backward_euler import BackwardEuler
    from discretizations.time.PadeLowTildeGamma import PadeLowTildeGamma
    from cv_factor_pade import rho_Pade_FD_corr0, rho_Pade_c, rho_Pade_FD_extra
    # parameters of the schemes are given to the builder:
    builder = Builder()
    builder.LAMBDA_1 = 1e9  # extremely high lambda is a Dirichlet condition
    builder.LAMBDA_2 = 0. # lambda=0 is a Neumann condition
    # builder.LAMBDA_1 = 1.11 # optimal parameters for corr=0, N=3000
    # builder.LAMBDA_2 = -0.76
    builder.D1 = 1.
    builder.D2 = 2.
    builder.R = 0.
    fig, axes = plt.subplots(2, 3, sharex=True, sharey=True,figsize=(8,4.2))    
    plt.subplots_adjust(left=.04, bottom=.10, right=.99, top=.92, wspace=0.05, hspace=0.4)
    dt = builder.DT
    REACTION_COEFF = 0.1
        
    discretizations = {}
    time_scheme = BackwardEuler

    theorical_convergence_factors = {}
    theorical_convergence_factors["BEFV"] = {}
    theorical_convergence_factors["BEFD"] = {}
    theorical_convergence_factors["BEFD_R"] = {}
    theorical_convergence_factors["SimplePade"] = {}
    theorical_convergence_factors["LowTildePade"] = {}
    theorical_convergence_factors["LowTildePade_R"] = {}

    def low_tilde_gamma(z):
        b = 1+1/np.sqrt(2)
        return z - b*(z-1) - b/2 * (z-1)**2
    def simple_gamma(z):
        b = 1+1/np.sqrt(2)
        return z - b*(z-1)

    all_dt = (1e-3, 1e-2, 1e-1, 1e0, 1e1)
    style = {all_dt[4] : {'col':'k', 'ls':'solid', 'lw':1.4, 'legend':r"$\Gamma=10$"},
            all_dt[3] : {'col':'.1', 'ls':'dashed', 'lw':1.55, 'legend':r"$\Gamma=1$"},
            all_dt[2] : {'col':'.5', 'ls':'solid', 'lw':1.7, 'legend':r"$\Gamma=10^{-1}$"},
            all_dt[1] : {'col':'.5', 'ls':'dashed', 'lw':1.9, 'legend':r"$\Gamma=10^{-2}$"},
            all_dt[0] : {'col':'r', 'ls':'solid', 'lw':1.2, 'legend':r"$\Gamma=\nu_1\frac{\Delta t}{h^2}=10^{-3}$"}}

    for dt in all_dt:
        builder.DT = dt
        assert REACTION_COEFF * builder.DT <= 1
        axis_freq = get_discrete_freq(1000/dt, builder.DT)

        dis = builder.build(BackwardEuler, FiniteDifferencesNaive)
        theorical_convergence_factors["BEFD"][dt] = dis.analytic_robin_robin_modified(w=axis_freq,
                        order_time=float('inf'), order_operators=float('inf'),
                        order_equations=float('inf'))

        dis.R = REACTION_COEFF
        theorical_convergence_factors["BEFD_R"][dt] = dis.analytic_robin_robin_modified(w=axis_freq,
                        order_time=float('inf'), order_operators=float('inf'),
                        order_equations=float('inf'))

        dis = builder.build(BackwardEuler, QuadSplinesFV)
        theorical_convergence_factors["BEFV"][dt] = dis.analytic_robin_robin_modified(w=axis_freq,
                        order_time=float('inf'), order_operators=float('inf'),
                        order_equations=float('inf'))

        theorical_convergence_factors["SimplePade"][dt] = rho_Pade_FD_corr0(builder, axis_freq, gamma=simple_gamma)

        builder.R = REACTION_COEFF
        theorical_convergence_factors["LowTildePade_R"][dt] = rho_Pade_FD_corr0(builder, axis_freq, gamma=low_tilde_gamma)
        builder.R = 0.

        theorical_convergence_factors["LowTildePade"][dt] = rho_Pade_FD_corr0(builder, axis_freq, gamma=low_tilde_gamma)

        
        col = style[dt]['col']
        ls = style[dt]['ls']
        lw = style[dt]['lw']
        legend = style[dt]['legend']
        axes[0,0].semilogx(axis_freq, theorical_convergence_factors["BEFV"][dt], linestyle=ls, color=col, linewidth=lw)
        axes[0,1].semilogx(axis_freq, theorical_convergence_factors["BEFD"][dt], linestyle=ls, color=col, label=legend, linewidth=lw)
        axes[0,2].semilogx(axis_freq, theorical_convergence_factors["BEFD_R"][dt], linestyle=ls, color=col, linewidth=lw)
        axes[1,0].semilogx(axis_freq, theorical_convergence_factors["SimplePade"][dt], linestyle=ls, color=col, linewidth=lw)
        axes[1,1].semilogx(axis_freq, theorical_convergence_factors["LowTildePade"][dt], linestyle=ls, color=col, linewidth=lw)
        axes[1,2].semilogx(axis_freq, theorical_convergence_factors["LowTildePade_R"][dt], linestyle=ls, color=col, linewidth=lw)

    axes[0,0].set_title(r"${\rho}^{(BE, FV)}_{DN}$", fontsize=10)
    axes[0,1].set_title(r"${\rho}^{(BE, FD)}_{DN}$", fontsize=10)
    axes[0,2].set_title(r"${\rho}^{(BE, FD)}_{DN} (r=0.1 s^{-1})$", fontsize=10)
    axes[1,0].set_title(r"${\rho}^{(P2, FD)}_{DN}, \gamma_{\rm extr}$", fontsize=10)
    axes[1,1].set_title(r"${\rho}^{(P2, FD)}_{DN}, \gamma_{\rm init}$", fontsize=10)
    axes[1,2].set_title(r"${\rho}^{(P2, FD)}_{DN}, \gamma_{\rm imit} (r=0.1 s^{-1})$", fontsize=10)

    for i in (0,1,2):
        axes[1,i].set_xlabel(r"$\omega$", fontsize=12)

    letter_fig = {(0,0): '(a)', 
            (0,1): '(b)', 
            (0,2): '(c)', 
            (1,0): '(d)', 
            (1,1): '(e)', 
            (1,2): '(f)', }
    for i,j in ((0,0), (1,0), (0,1), (1,1), (0,2), (1,2)):
        txt = axes[i,j].annotate(letter_fig[(i,j)],xy=(0.03,0.075), xycoords='axes fraction',color='k',fontsize=10)
        txt.set_bbox(dict(facecolor='white',alpha=1.))  
        axes[i,j].grid(color='k', linestyle=':', linewidth=0.25)
    axes[0,1].legend(loc="upper right",prop={'size':7}, handlelength=2)
    fig.tight_layout()   
    show_or_save("fig_interactionsDN")

def robin_parameters_discrete_space(builder, N, dt, scheme="FD"):
    from discretizations.space.FD_naive import FiniteDifferencesNaive
    from discretizations.time.backward_euler import BackwardEuler # silent class
    from discretizations.space.quad_splines_fv import QuadSplinesFV
    if scheme == "FD":
        space_dis = FiniteDifferencesNaive
    elif scheme == "FV":
        space_dis = QuadSplinesFV
    else:
        raise

    from scipy.optimize import minimize_scalar, minimize
    axis_freq = get_discrete_freq(N, dt)
    def to_minimize_onesided(p):
        dis = builder.build(BackwardEuler, space_dis)
        dis.LAMBDA_1 = p
        dis.LAMBDA_2 = -p
        return np.max(np.abs(dis.analytic_robin_robin_modified(w=axis_freq,
                order_time=0, order_operators=float('inf'), order_equations=float('inf'))))

    def to_minimize_twosided(parameters):
        dis = builder.build(BackwardEuler, space_dis)
        dis.LAMBDA_1 = parameters[0]
        dis.LAMBDA_2 = parameters[1]
        return np.max(np.abs(dis.analytic_robin_robin_modified(w=axis_freq,
                order_time=0, order_operators=float('inf'), order_equations=float('inf'))))

    res_onesided = minimize_scalar(fun=to_minimize_onesided)
    p_opti = res_onesided.x
    res_twosided = minimize(fun=to_minimize_twosided,
            x0=np.array((p_opti, -p_opti)), method='Nelder-Mead')
    return res_twosided

def fig_RRInteraction():
    import matplotlib as mpl
    mpl.rc('text', usetex=True)
    mpl.rcParams['text.latex.preamble']=[r"\usepackage{amsmath}"]
    from discretizations.space.FD_naive import FiniteDifferencesNaive
    from discretizations.space.FD_corr import FiniteDifferencesCorr
    from discretizations.space.FD_extra import FiniteDifferencesExtra
    from discretizations.space.quad_splines_fv import QuadSplinesFV
    from discretizations.space.fourth_order_fv import FourthOrderFV
    from discretizations.time.backward_euler import BackwardEuler
    from discretizations.time.PadeLowTildeGamma import PadeLowTildeGamma
    from cv_factor_pade import rho_Pade_FD_corr0, rho_Pade_c, rho_Pade_FD_extra
    # parameters of the schemes are given to the builder:
    builder = Builder()
    builder.D1 = 1.
    builder.D2 = 2.
    fig, axes = plt.subplots(2, 3, sharex=True, sharey=True,figsize=(8,4.2))    
    plt.subplots_adjust(left=.04, bottom=.10, right=.99, top=.92, wspace=0.05, hspace=0.4)
    axes[0,0].set_ylim(top=0.6, bottom=0.) #sharey activated : see ax[1].set_xlim
    dt = builder.DT
    REACTION_COEFF = 0.1 # for cases with reaction != 0
    all_dt = (1e1, 1e0, 1e-1, 1e-2, 1e-3)
    style = {all_dt[0] : {'col':'k', 'ls':'solid', 'lw':1.4, 'legend':r"$\Gamma=10$"},
            all_dt[1] : {'col':'.1', 'ls':'dashed', 'lw':1.55, 'legend':r"$\Gamma=1$"},
            all_dt[2] : {'col':'.5', 'ls':'solid', 'lw':1.7, 'legend':r"$\Gamma=10^{-1}$"},
            all_dt[3] : {'col':'.5', 'ls':'dashed', 'lw':1.9, 'legend':r"$\Gamma=10^{-2}$"},
            all_dt[4] : {'col':'r', 'ls':'solid', 'lw':1., 'legend':r"$\Gamma=\nu_1\frac{\Delta t}{h^2}=10^{-3}$"}}
        
    discretizations = {}
    time_scheme = BackwardEuler

    theorical_convergence_factors = {}
    theorical_convergence_factors["BEFV"] = {}
    theorical_convergence_factors["BEFD"] = {}
    theorical_convergence_factors["BEFD_R"] = {}
    theorical_convergence_factors["SimplePade"] = {}
    theorical_convergence_factors["LowTildePade"] = {}
    theorical_convergence_factors["LowTildePade_R"] = {}

    ############## OPTIMISATION #####################
    dtmin = 1e-3
    builder.R = 0.
    builder.DT = dtmin
    #optimisation for FD:
    res_twosided = memoised(robin_parameters_discrete_space, builder=builder, N=1000/dtmin, dt=dtmin)
    theorical_convergence_factors["BEFD"]["robin"] = res_twosided.x
    #optimisation for FD with Reaction:

    builder.R = REACTION_COEFF
    theorical_convergence_factors["BEFD_R"]["robin"] =memoised(robin_parameters_discrete_space, builder=builder, N=1000/dtmin, dt=dtmin).x

    #optimisation for FV:
    builder.R = 0.
    theorical_convergence_factors["BEFV"]["robin"] = memoised(robin_parameters_discrete_space, builder=builder, N=1000/dtmin, dt=dtmin, scheme="FV").x

    #optimisation for FD with r:

    def low_tilde_gamma(z):
        b = 1+1/np.sqrt(2)
        return z - b*(z-1) - b/2 * (z-1)**2
    def simple_gamma(z):
        b = 1+1/np.sqrt(2)
        return z - b*(z-1)

    for dt in all_dt:
        builder.DT = dt
        assert REACTION_COEFF * builder.DT <= 1
        axis_freq = get_discrete_freq(5000/dt, builder.DT)

        dis = builder.build(BackwardEuler, FiniteDifferencesNaive)
        dis.LAMBDA_1, dis.LAMBDA_2 = theorical_convergence_factors["BEFD"]["robin"]
        theorical_convergence_factors["BEFD"][dt] = dis.analytic_robin_robin_modified(w=axis_freq,
                        order_time=float('inf'), order_operators=float('inf'),
                        order_equations=float('inf'))

        col = style[dt]['col']
        ls = style[dt]['ls']
        lw = style[dt]['lw']
        legend = style[dt]['legend']

        dis.R = REACTION_COEFF
        dis.LAMBDA_1, dis.LAMBDA_2 = theorical_convergence_factors["BEFD_R"]["robin"]
        theorical_convergence_factors["BEFD_R"][dt] = dis.analytic_robin_robin_modified(w=axis_freq,
                        order_time=float('inf'), order_operators=float('inf'),
                        order_equations=float('inf'))

        dis = builder.build(BackwardEuler, QuadSplinesFV)
        dis.LAMBDA_1, dis.LAMBDA_2 = theorical_convergence_factors["BEFV"]["robin"]
        theorical_convergence_factors["BEFV"][dt] = dis.analytic_robin_robin_modified(w=axis_freq,
                        order_time=float('inf'), order_operators=float('inf'),
                        order_equations=float('inf'))

        builder.LAMBDA_1, builder.LAMBDA_2 = theorical_convergence_factors["BEFD"]["robin"]
        theorical_convergence_factors["SimplePade"][dt] = rho_Pade_FD_corr0(builder, axis_freq, gamma=simple_gamma)

        builder.R = REACTION_COEFF
        builder.LAMBDA_1, builder.LAMBDA_2 = theorical_convergence_factors["BEFD_R"]["robin"]
        theorical_convergence_factors["LowTildePade_R"][dt] = rho_Pade_FD_corr0(builder, axis_freq, gamma=low_tilde_gamma)
        builder.R = 0.

        builder.LAMBDA_1, builder.LAMBDA_2 = theorical_convergence_factors["BEFD"]["robin"]
        theorical_convergence_factors["LowTildePade"][dt] = rho_Pade_FD_corr0(builder, axis_freq, gamma=low_tilde_gamma)

        axes[0,0].semilogx(axis_freq, theorical_convergence_factors["BEFV"][dt], linestyle=ls, color=col, linewidth=lw)
        axes[0,1].semilogx(axis_freq, theorical_convergence_factors["BEFD"][dt], linestyle=ls, color=col, linewidth=lw)
        axes[0,2].semilogx(axis_freq, theorical_convergence_factors["BEFD_R"][dt], linestyle=ls, color=col, label=legend, linewidth=lw)
        axes[1,0].semilogx(axis_freq, theorical_convergence_factors["SimplePade"][dt], linestyle=ls, color=col, linewidth=lw)
        axes[1,1].semilogx(axis_freq, theorical_convergence_factors["LowTildePade"][dt], linestyle=ls, color=col, linewidth=lw)
        axes[1,2].semilogx(axis_freq, theorical_convergence_factors["LowTildePade_R"][dt], linestyle=ls, color=col, linewidth=lw)

    axes[0,0].set_title(r"${\rho}^{(BE, FV)}_{RR}$", fontsize=10)
    axes[0,1].set_title(r"${\rho}^{(BE, FD)}_{RR}$", fontsize=10)
    axes[0,2].set_title(r"${\rho}^{(BE, FD)}_{RR} (r=0.1 s^{-1})$", fontsize=10)
    axes[1,0].set_title(r"${\rho}^{(P2, FD)}_{RR}, \gamma_{\rm extr}$", fontsize=10)
    axes[1,1].set_title(r"${\rho}^{(P2, FD)}_{RR}, \gamma_{\rm imit}$", fontsize=10)
    axes[1,2].set_title(r"${\rho}^{(P2, FD)}_{RR}, \gamma_{\rm imit}$ $(r=0.1 s^{-1})$", fontsize=10)

    for i in (0,1,2):
        axes[1,i].set_xlabel(r"$\omega$", fontsize=12)
    letter_fig = {(0,0): '(a)', 
            (0,1): '(b)', 
            (0,2): '(c)', 
            (1,0): '(d)', 
            (1,1): '(e)', 
            (1,2): '(f)', }

    for i,j in ((0,0), (1,0), (0,1), (1,1), (0,2), (1,2)):
        txt = axes[i,j].annotate(letter_fig[(i,j)],xy=(0.03,0.075), xycoords='axes fraction',color='k',fontsize=10)
        axes[0,0].set_xlim(3.1415/1000,9e2)
        txt.set_bbox(dict(facecolor='white',alpha=1.))  
        axes[i,j].grid(color='k', linestyle=':', linewidth=0.25)
    handles, labels = axes[0,2].get_legend_handles_labels()
    # sort both labels and handles by labels
    labels, handles = list(reversed(labels)), list(reversed(handles))
    axes[0,2].legend(handles, labels, loc="upper right",prop={'size':7}, handlelength=2)

    fig.tight_layout()
    show_or_save("fig_interactionsRR")


def fig_rootsManfrediFD():
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=[9.6, 2.])
    plt.subplots_adjust(left=.07, bottom=.28, right=.97, top=.85)
    builder = Builder()

    ###########################
    # equation: (\Gamma_{a,j} = a*dt*nu/h^2, \Gamma_{b,j} = b*dt*nu/h^2)
    #        (z-1+r\Delta t + z r^2 \Delta t b)\lambda_i^2 + 
    #        \left(\Gamma_a - 2z\Gamma_b(1+r\Delta t b)\right) \lambda \left(\lambda-1\right)^2 + 
    #        2\Gamma_b^2 \left(\lambda-1\right)^4 = 0
    # rewrite it for wolframAlpha: f* x^2 + g*x(x-1)^2 + (x-1)^4 = 0
    # where x = \lambda
    # where f = (z-1+r\Delta t + z*r^2 \Delta t b) / (2\Gamma_b^2)
    # and g = (\Gamma_a - 2z\Gamma_b) / (2\Gamma_b^2)
    ##########################"
    a = 1+np.sqrt(2)
    b = 1+1/np.sqrt(2)
    dt= builder.DT
    r = builder.R
    nu_1 = builder.D1
    nu_2 = builder.D2
    L1 = builder.LAMBDA_1
    L2 = builder.LAMBDA_2
    h = builder.SIZE_DOMAIN_1 / (builder.M1-1)

    def get_z(w):
        return np.exp(-1j*w*dt)

    def Gamma(ab, nu):
        return ab*dt*nu/h**2

    def get_f_g(w, nu):
        z = get_z(w)
        Gamma_a, Gamma_b = Gamma(a, nu), Gamma(b, nu)
        return (z - 1 + r*dt + z*r**2*dt*b) / (2*Gamma_b**2), \
                (Gamma_a - 2*z*Gamma_b*(1 + r*dt*b)) / (2*Gamma_b**2)

    def square_root_interior(f, g):
        return np.sqrt(-(4*(g-4)*(f-2*g+6) - (g-4)**3 - 8*(g-4))/(2*np.sqrt(g**2 - 4*f)) \
                - f + (g-4)**2/2 + 2*g - 8)/2

    def lambda_pp(w, nu):
        f, g = get_f_g(w, nu)
        return 1 - g/4 + 1j*np.sqrt(4*f - g**2)/4 + square_root_interior(f, g)

    def lambda_pm(w, nu):
        f, g = get_f_g(w, nu)
        return 1 - g/4 + 1j* np.sqrt(4*f - g**2)/4 - square_root_interior(f, g)

    def lambda_mp(w, nu):
        f, g = get_f_g(w, nu)
        return 1 - g/4 - 1j* (np.sqrt(4*f - g**2)/4 + square_root_interior(f, g))

    def lambda_mm(w, nu):
        f, g = get_f_g(w, nu)
        return 1 - g/4 - 1j* (np.sqrt(4*f - g**2)/4 - square_root_interior(f, g))

    N = 30000
    w = get_discrete_freq(N, dt)

    sigma_1 = np.log(lambda_pm(w, nu_1)) / h
    sigma_2 = np.log(lambda_mp(w, nu_1)) / h
    sigma_3 = np.log(lambda_pp(w, nu_1)) / h
    sigma_4 = np.log(lambda_mm(w, nu_1)) / h

    axes[0].semilogx(w, np.real(sigma_1), label="$\\sigma_1$")

    axes[0].semilogx(w, np.real(sigma_2), label="$\\sigma_2$")
    axes[0].semilogx(w, np.real(sigma_3), label="$\\sigma_3$")
    axes[0].semilogx(w, np.real(sigma_4), label="$\\sigma_4$")

    axes[0].semilogx(w, np.abs(np.real(np.sqrt((r+1j*w)/nu_1))), "k--", label="$\\sigma_j$ continuous")
    axes[0].semilogx(w, np.abs(np.real(-np.sqrt((r+1j*w)/nu_1))), "k--")
    axes[0].set_xlabel("$\\Delta t\\omega$")
    axes[0].set_ylabel("$\\mathfrak{R}(\\sigma)$")
    axes[0].set_title("Real part $\\mathfrak{R}(\\sigma)$")
    axes[0].grid(True, color='k', linestyle='dotted', linewidth=0.25) 

    axes[1].semilogx(w, np.imag(sigma_1), label="$\\sigma_1$")

    axes[1].semilogx(w, np.imag(sigma_2), label="$\\sigma_2$")
    axes[1].semilogx(w, np.imag(sigma_3), label="$\\sigma_3$")
    axes[1].semilogx(w, np.imag(sigma_4), label="$\\sigma_4$")

    axes[1].semilogx(w, np.imag(np.sqrt((r+1j*w)/nu_1)), "k--", label="$\\sigma_j$ continuous")
    axes[1].semilogx(w, np.imag(-np.sqrt((r+1j*w)/nu_1)), "k--")
    axes[1].set_xlabel("$\\Delta t\\omega$")
    axes[1].set_ylabel("$Im(\\sigma)$")
    axes[1].set_title("Imaginary part $Im(\\sigma)$")
    axes[1].grid(True, color='k', linestyle='dotted', linewidth=0.25) 

    plt.legend()
    show_or_save("fig_rootsManfrediFD")

def wAndRhoPadeRR(builder, gamma=None):
    a = 1+np.sqrt(2)
    b = 1+1/np.sqrt(2)
    dt= builder.DT
    r = builder.R
    nu_1 = builder.D1
    nu_2 = builder.D2
    L1 = builder.LAMBDA_1
    L2 = builder.LAMBDA_2

    def get_z_s(w):
        z = np.exp(-1j*w*dt)
        return z, (z - 1)/(z*dt)

    if gamma is None:
        def gamma(w):
            z, _ = get_z_s(w)
            return z - b*(z-1) - b/2 * (z-1)**2

    def square_root_interior(w):
        z, s = get_z_s(w)
        return 1j*np.sqrt(-1*(1+(a*dt*s)**2 - (a**2+1)*dt*s))

    def sigma_plus(w, nu):
        z, s = get_z_s(w)
        return np.sqrt(1+a*dt*s +a**2*dt*r + square_root_interior(w))/(a*np.sqrt(dt*nu))

    def sigma_minus(w, nu):
        z, s = get_z_s(w)
        return np.sqrt(1+a*dt*s +a**2*dt*r - square_root_interior(w))/(a*np.sqrt(dt*nu))

    N = 300
    w = get_discrete_freq(N, dt)

    sigma_1 = sigma_minus(w, nu_1)
    sigma_2 = - sigma_minus(w, nu_2)
    sigma_3 = sigma_plus(w, nu_1)
    sigma_4 = -sigma_plus(w, nu_2)
    assert (np.real(sigma_1) > 0).all()
    assert (np.real(sigma_2) < 0).all()
    assert (np.real(sigma_3) > 0).all()
    assert (np.real(sigma_4) < 0).all()

    z, s = get_z_s(w)
    mu_1 = z*(1 + r*dt*b - b*dt*nu_1*sigma_1**2)
    mu_2 = z*(1 + r*dt*b - b*dt*nu_2*sigma_2**2)
    mu_3 = z*(1 + r*dt*b - b*dt*nu_1*sigma_3**2)
    mu_4 = z*(1 + r*dt*b - b*dt*nu_2*sigma_4**2)
    assert (np.linalg.norm(mu_1 - mu_2) < 1e-10) # mu_1 == mu_2
    assert (np.linalg.norm(mu_3 - mu_4) < 1e-10) # mu_3 == mu_4
    gamma_t = (mu_1 - gamma(w))/(mu_1 - mu_3)

    varrho = ((L1 + nu_2*sigma_2)/(L2 + nu_2*sigma_2) * (1 - gamma_t) + \
             (L1 + nu_2*sigma_4)/(L2 + nu_2*sigma_4) * gamma_t) * \
             ((L2 + nu_1*sigma_1)/(L1 + nu_1*sigma_1) * (1 - gamma_t) + \
             (L2 + nu_1*sigma_3)/(L1 + nu_1*sigma_3) * gamma_t)

    return w, np.abs(varrho)

def fig_rhoDNPadeModif():
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 1, figsize=[6.4, 2.4], sharex=False, sharey=True)
    plt.subplots_adjust(left=.11, bottom=.24, right=.99, top=.85, wspace=0.19, hspace=0.15)
    ax   = axes
    wmax = np.pi
    wmin = wmax / 200
    ax.set_xlim(wmin,wmax)
    ax.set_ylim(0.5,1.0)
    ax.grid(True,color='k', linestyle='dotted', linewidth=0.25)
    ax.set_xticklabels(ax.get_xticks(),fontsize=12)
#    ax.set_yticklabels(ax.get_yticks(),fontsize=12)  
    ax.set_title(r'$r=' + str(0) + r'\;{\rm s}^{-1}$')


    builder = Builder()
    builder.R = 0.
    builder.D1 = .5

    b = 1+1/np.sqrt(2)

    def get_z_s(w):
        z = np.exp(-1j*w*builder.DT)
        return z, (z - 1)/(z*builder.DT)

    def gamma_highTilde(w):
        z, _ = get_z_s(w)
        return z - b*(z-1)

    def gamma_lowTilde(w):
        z, _ = get_z_s(w)
        return z - b*(z-1) - b * (b-1)**2 * (z-1)**2

    w, varrho = wAndRhoPadeRR(builder, gamma=gamma_highTilde)
    ax.semilogx(w*builder.DT, np.abs(varrho ) ,linewidth=2.,color='k', linestyle='solid' ,label=r'$\gamma$: interpolation')   
    w, varrho = wAndRhoPadeRR(builder, gamma=gamma_lowTilde)

    ax.semilogx( w*builder.DT, np.abs(varrho ) ,linewidth=2.,color='k', linestyle='dashed' ,label=r'$\gamma$: imitate scheme')

    rho_continuous = np.sqrt(builder.D1/builder.D2) * np.ones_like(w)


    ax.semilogx(w*builder.DT, rho_continuous ,linewidth=2., color='r', linestyle='dashed', label=r'$\sqrt{\frac{\nu_1}{\nu_2}}$') 
    ax.semilogx(w*builder.DT, rho_continuous ,linewidth=2., color='k', linestyle='dotted', label=r'Equivalent PDE') 

    ax.legend(loc=2,prop={'size':9},ncol=1,handlelength=2)
    ax.set_xlabel(r"$\omega\Delta t$")
    ax.set_ylabel(r"${\rho}$")

    show_or_save("fig_rhoDNPadeModif")

def fig_rhoDNPadepres():
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=[6.4, 2.4], sharex=False, sharey=True)
    plt.subplots_adjust(left=.11, bottom=.24, right=.99, top=.85, wspace=0.19, hspace=0.15)
    wmax = np.pi
    wmin = wmax / 200
    for ax in axes:
        ax.set_xlim(wmin,wmax)
        ax.set_ylim(0.54,1.0)
        ax.grid(True,color='k', linestyle='dotted', linewidth=0.25)
        ax.set_xlabel (r'$\omega\Delta t$')
        ax.set_xticklabels(ax.get_xticks(),fontsize=12)
    #    ax.set_yticklabels(ax.get_yticks(),fontsize=12)  

    axes[0].set_title(r'$r=' + str(0.) + r'\;{\rm s}^{-1}$')
    axes[0].set_ylabel(r'${\rho}$')
    axes[1].set_title(r'$r=' + str(1.) + r'\;{\rm s}^{-1}$')


    builder = Builder()
    builder.R = 0.
    builder.D1 = .5

    b = 1+1/np.sqrt(2)

    def get_z_s(w):
        z = np.exp(-1j*w*builder.DT)
        return z, (z - 1)/(z*builder.DT)

    def gamma_highTilde(w):
        z, _ = get_z_s(w)
        return z - b*(z-1)

    def gamma_lowTilde(w):
        z, _ = get_z_s(w)
        return z - b*(z-1) - b * (b-1)**2 * (z-1)**2

    w, varrho = wAndRhoPadeRR(builder, gamma=gamma_highTilde)
    axes[0].semilogx(w*builder.DT, np.abs(varrho ) ,linewidth=2.,color='k', linestyle='solid' ,label=r'$\gamma = z - \beta (z-1)$')   
    w, varrho = wAndRhoPadeRR(builder, gamma=gamma_lowTilde)

    axes[0].semilogx( w*builder.DT, np.abs(varrho ) ,linewidth=2.,color='k', linestyle='dashed' ,label=r'$\gamma = z - \beta (z-1) - \beta(\beta-1)^2 (z-1)^2$')       

    builder.R = 1.

    w, varrho = wAndRhoPadeRR(builder, gamma=gamma_highTilde)
    axes[1].semilogx( w*builder.DT, np.abs(varrho ) ,linewidth=2.,color='k', linestyle='solid' ,label=r'$\gamma$: interpolation')   

    w, varrho = wAndRhoPadeRR(builder, gamma=gamma_lowTilde)
    axes[1].semilogx(w*builder.DT, np.abs(varrho ) ,linewidth=2.,color='k', linestyle='dashed' ,label=r'$\gamma$: imitate scheme')    

    rho_continuous = np.sqrt(builder.D1/builder.D2) * np.ones_like(w)
    axes[0].semilogx(w*builder.DT, rho_continuous ,linewidth=2.,color='r', linestyle='dashed' ,label=r'$\sqrt{\frac{\nu_1}{\nu_2}}$') 
    axes[1].semilogx(w*builder.DT, rho_continuous ,linewidth=2.,color='r', linestyle='dashed' ,label=r'$\sqrt{\frac{\nu_1}{\nu_2}}$') 
    axes[1].legend(loc=2,prop={'size':9},ncol=1,handlelength=2)

    show_or_save("fig_rhoDNPadepres")

def fig_rhoDNPade():
    import matplotlib as mpl
    mpl.rc('text', usetex=True)
    mpl.rcParams['text.latex.preamble']=[r"\usepackage{amsmath}"]
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 1, sharex=False, sharey=True,figsize=(7,3))
    #plt.subplots_adjust(bottom=.18, top=.85)
    ax   = axes
    wmax = np.pi
    wmin = wmax / 200
    ax.set_xlim(wmin,wmax)
    ax.set_ylim(0.53,1.05)
    ax.grid(True,color='k', linestyle='dotted', linewidth=0.25)
    ax.set_xlabel (r'$\omega$', fontsize=18)
    ax.set_xticklabels(ax.get_xticks(),fontsize=12)
#    ax.set_yticklabels(ax.get_yticks(),fontsize=12)  
    ax.set_title(r"$\rho_{\rm DN}^{\rm (P2,c)}$",fontsize=16) 


    builder = Builder()
    builder.R = 0.
    builder.D1 = .5

    b = 1+1/np.sqrt(2)

    def get_z_s(w):
        z = np.exp(-1j*w*builder.DT)
        return z, (z - 1)/(z*builder.DT)

    def gamma_highTilde(w):
        z, _ = get_z_s(w)
        return z - b*(z-1)

    def gamma_lowTilde(w):
        z, _ = get_z_s(w)
        return z - b*(z-1) - b * (b-1)**2 * (z-1)**2

    w, varrho = wAndRhoPadeRR(builder, gamma=gamma_highTilde)
    ax.semilogx(w*builder.DT, np.abs(varrho ) ,linewidth=2.,color='k', linestyle='solid' ,label=r'$r=0\;{\rm s}^{-1}, \gamma = z - \beta (z-1)$')   
    w, varrho = wAndRhoPadeRR(builder, gamma=gamma_lowTilde)

    ax.semilogx( w*builder.DT, np.abs(varrho ) ,linewidth=2.,color='k', linestyle='dashed' ,label=r'$r=0\;{\rm s}^{-1}, \gamma = z - \beta (z-1) - \beta(\beta-1)^2 (z-1)^2$')       

    builder.R = .1

    w, varrho = wAndRhoPadeRR(builder, gamma=gamma_highTilde)
    ax.semilogx( w*builder.DT, np.abs(varrho ) ,linewidth=2.,color='0.5', linestyle='solid' ,label=r'$r=0.1\;{\rm s}^{-1}, \gamma = z - \beta (z-1)$')   

    w, varrho = wAndRhoPadeRR(builder, gamma=gamma_lowTilde)
    ax.semilogx(w*builder.DT, np.abs(varrho ) ,linewidth=2.,color='0.5', linestyle='dashed' ,label=r'$r=0.1\;{\rm s}^{-1}, \gamma = z - \beta (z-1) - \beta (\beta-1)^2 (z-1)^2$')    

    rho_continuous = np.sqrt(builder.D1/builder.D2) * np.ones_like(w)
    ax.semilogx(w*builder.DT, rho_continuous ,linewidth=2.,color='r', linestyle='dashed' ,label=r'$\sqrt{\frac{\nu_1}{\nu_2}}$') 
    ax.set_xlabel(r"$\omega\Delta t$")
    ax.legend(loc=2,prop={'size':9},ncol=1,handlelength=2)
    fig.tight_layout()

    show_or_save("fig_rhoDNPade")

def fig_gammaTilde():
    import matplotlib.pyplot as plt
    dt=1.
    a = 1+np.sqrt(2)
    b = 1+1/np.sqrt(2)
    r=.0
    assert r == 0.
    def mu_plus(w):
        z = np.exp(-1j*w*dt)
        s = (z - 1)/z
        return z*(1/np.sqrt(2) * (1-s) + \
                1j*(-b/a**2)*np.sqrt((1+a**2*s**2 - 2*dt*a**2*r/z - (a**2+1)*s)/(-1)))
    def mu_minus(w):
        z = np.exp(-1j*w*dt)
        s = (z - 1)/z
        return z*(1/np.sqrt(2) * (1-s) - \
                1j*(-b/a**2)*np.sqrt((1+a**2*s**2 - 2*dt*a**2*r/z - (a**2+1)*s)/(-1)))

    def gamma(w):
        z = np.exp(-1j*w*dt)
        return z - b*(z-1) - b/2 * (z-1)**2
    w = np.linspace(0,pi, 1000)
    plt.plot(w, np.real((mu_minus(w) - gamma(w))/(mu_plus(w) - mu_minus(w))), label="Real part of $\\tilde{\\gamma}$")
    plt.plot(w, np.imag((mu_minus(w) - gamma(w))/(mu_plus(w) - mu_minus(w))), label="Imaginary part of $\\tilde{\\gamma}$")
    # plt.plot(w, np.abs(1-(mu_minus(w) - gamma(w))/(mu_plus(w) - mu_minus(w))), label="modulus of gamma")
    plt.title("Value of $\\tilde{\\gamma}$")
    plt.grid()
    plt.legend()
    show_or_save("fig_gammaTilde")

def fig_rootsManfredi():
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=[9.6, 2.])
    plt.subplots_adjust(left=.07, bottom=.28, right=.97, top=.85)


    dt=1.
    a = 1+np.sqrt(2)
    r=.5
    nu_1 = 1.
    nu_2 = 2.
    #assert r == 0.
    def get_z_s(w):
        z = np.exp(-1j*w*dt)
        return z, (z - 1)/(z*dt)

    def square_root_interior(w):
        z, s = get_z_s(w)
        return 1j*np.sqrt(-1*(1+(a*dt*s)**2 - (a**2+1)*dt*s))

    def sigma_plus(w, nu):
        z, s = get_z_s(w)
        return np.sqrt(1+a*dt*s + a**2*dt*r + square_root_interior(w))/(a*np.sqrt(dt*nu))

    def sigma_minus(w, nu):
        z, s = get_z_s(w)
        return np.sqrt(1+a*dt*s + a**2*dt*r - square_root_interior(w))/(a*np.sqrt(dt*nu))

    w = np.exp(np.linspace(-8, np.log(pi), 1000))[:-1]
    ref =(np.real(sigma_minus(w, nu_1)))

    axes[0].semilogx(w, (np.real(sigma_minus(w, nu_1))), label="$\\sigma_1$")

    axes[0].semilogx(w, np.abs(np.real(-sigma_minus(w, nu_2))), label="$\\sigma_2$")
    axes[0].semilogx(w, (np.real(sigma_plus(w, nu_1))), label="$\\sigma_3$")
    axes[0].semilogx(w, np.abs(np.real(-sigma_plus(w, nu_2))), label="$\\sigma_4$")

    axes[0].loglog(w, np.abs(np.real(np.sqrt((r+1j*w)/nu_1))), "k--", label="$\\sigma_j$ continuous")
    axes[0].semilogx(w, np.abs(np.real(-np.sqrt((r+1j*w)/nu_2))), "k--")

    #axes[0].loglog(w, np.abs(np.real(np.sqrt((r+1j*w + (4+3*np.sqrt(2))* (w*1j)**3 * dt**2/6)/nu_1) - ref)), label="$\\sigma_j$ modified")
    #axes[0].semilogx(w, np.abs(np.real(-np.sqrt((r+1j*w+ (4+3*np.sqrt(2))* (w*1j)**3 * dt**2/6)/nu_2))), "k--")



    axes[0].set_xlabel("$\\Delta t\\omega$")
    axes[0].set_ylabel("$\\mathfrak{R}(\\sigma)$")
    axes[0].set_title("Real part $|\\mathfrak{R}(\\sigma)|$")
    axes[0].grid()

    axes[1].loglog(w, np.abs(np.imag(sigma_minus(w, nu_1))), label="$\\sigma_1$")

    axes[1].loglog(w, np.abs(np.imag(-sigma_minus(w, nu_2))), label="$\\sigma_2$")
    axes[1].loglog(w, np.abs(np.imag(sigma_plus(w, nu_1))), label="$\\sigma_3$")
    axes[1].loglog(w, np.abs(np.imag(-sigma_plus(w, nu_2))), label="$\\sigma_4$")

    axes[1].loglog(w, np.abs(np.imag(np.sqrt((r+1j*w)/nu_1))), "k--", label="$\\sigma_j$ continuous")
    axes[1].loglog(w, np.abs(np.imag(-np.sqrt((r+1j*w)/nu_2))), "k--")
    axes[1].set_xlabel("$\\Delta t\\omega$")
    axes[1].set_ylabel("$Im(\\sigma)$")
    axes[1].set_title("Imaginary part $|Im(\\sigma)|$")
    axes[1].grid()

    plt.legend()
    show_or_save("fig_rootsManfredi")


######################################################
# Utilities for analysing, representing discretizations
######################################################

class Builder():
    """
        interface between the discretization classes and the plotting functions.
        The main functions is build: given a space and a time discretizations,
        it returns a class which can be used with all the available functions.

        The use of anonymous classes forbids to use a persistent cache.
        To shunt this problem, function @frequency_cv_factor allows to
        specify the time and space discretizations at the last time, so
        the function @frequency_cv_factor can be stored in cache.

        To use this class, instanciate builder = Builder(),
        choose appropriate arguments of builder:
        builder.DT = 0.1
        builder.LAMBDA_2 = -0.3
        and then build all the schemes you want with theses parameters:
        dis_1 = builder.build(BackwardEuler, FiniteDifferencesNaive)
        dis_2 = builder.build(ThetaMethod, QuadSplinesFV)
        The comparison is thus then quite easy
    """
    def __init__(self): # changing defaults will result in needing to recompute all cache
        self.COURANT_NUMBER = 1.
        self.M1 = 200
        self.M2 = 200
        self.SIZE_DOMAIN_1 = 200
        self.SIZE_DOMAIN_2 = 200
        self.D1 = 1.
        self.D2 = 1.
        self.DT = self.COURANT_NUMBER * (self.SIZE_DOMAIN_1 / self.M1)**2 / self.D1
        self.A = 0.
        self.R = 0.
        self.LAMBDA_1 = 1e9
        self.LAMBDA_2 = 0.

    def build_scheme(self, scheme):
        """
            To use with a space-time discretization
        """
        return scheme(A=self.A, C=self.R,
                              D1=self.D1, D2=self.D2,
                              M1=self.M1, M2=self.M2,
                              SIZE_DOMAIN_1=self.SIZE_DOMAIN_1,
                              SIZE_DOMAIN_2=self.SIZE_DOMAIN_2,
                              LAMBDA_1=self.LAMBDA_1,
                              LAMBDA_2=self.LAMBDA_2,
                              DT=self.DT)

    def build(self, time_discretization, space_discretization):
        """
            Given two abstract classes of a time and space discretization,
            build a scheme.
        """
        class AnonymousScheme(time_discretization, space_discretization):
            def __init__(self, *args, **kwargs):
                space_discretization.__init__(self, *args, **kwargs)
                time_discretization.__init__(self, *args, **kwargs)

        return AnonymousScheme(A=self.A, C=self.R,
                              D1=self.D1, D2=self.D2,
                              M1=self.M1, M2=self.M2,
                              SIZE_DOMAIN_1=self.SIZE_DOMAIN_1,
                              SIZE_DOMAIN_2=self.SIZE_DOMAIN_2,
                              LAMBDA_1=self.LAMBDA_1,
                              LAMBDA_2=self.LAMBDA_2,
                              DT=self.DT)

    def frequency_cv_factor_spacetime_scheme(self, discretization, linear=True, **kwargs):
        discretization = self.build_scheme(discretization)
        if linear:
            return frequency_simulation(discretization, **kwargs)
        else:
            raise NotImplementedError("Just a linear regression in 2D")
            return matrixlinear_frequency_simulation(discretization, **kwargs)

    def frequency_cv_rate(self, time_discretization, space_discretization, linear=True, **kwargs):
        discretization = self.build(time_discretization, space_discretization)
        if linear:
            return simulation_cv_rate_linear(discretization, **kwargs)
        else:
            return simulation_cv_rate_matrixlinear(discretization, **kwargs)

    def simulation_firstlevels(self, time_discretization, space_discretization, **kwargs):
        discretization = self.build(time_discretization, space_discretization)
        return simulation_firstlevels(discretization, **kwargs)

    def frequency_cv_factor(self, time_discretization, space_discretization, linear=True, **kwargs):
        discretization = self.build(time_discretization, space_discretization)
        if linear:
            return frequency_simulation(discretization, **kwargs)
        else:
            return matrixlinear_frequency_simulation(discretization, **kwargs)

    def frequency_eigenvalues(self, time_discretization, space_discretization, **kwargs):
        discretization = self.build(time_discretization, space_discretization)
        return eigenvalues_matrixlinear_frequency_simulation(discretization, **kwargs)

    def robin_robin_theorical_cv_factor(self, time_discretization, space_discretization, *args, **kwargs):
        discretization = self.build(time_discretization, space_discretization)
        return discretization.analytic_robin_robin_modified(*args, **kwargs)

    def copy(self):
        ret = Builder()
        ret.__dict__ = self.__dict__.copy()
        return ret

    """
        __eq__ and __hash__ are implemented, so that a discretization
        can be stored as key in a dict
        (it is useful for memoisation)
    """

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __hash__(self):
        return hash(repr(sorted(self.__dict__.items())))

    def __repr__(self):
        return repr(sorted(self.__dict__.items()))

DEFAULT = Builder()


def get_discrete_freq(N, dt, avoid_zero=True):
    """
        Computation of the frequency axis.
        Z transform gives omega = 2 pi k T / (N).
    """
    N = N + 1 # actually, the results of the simulator contains one more point
    if N % 2 == 0: # even
        all_k = np.linspace(-N/2, N/2 - 1, N)
    else: #odd
        all_k = np.linspace(-(N-1)/2, (N-1)/2, N)
    # Usually, we don't want the zero frequency so we use instead 1/T:
    if avoid_zero:
        all_k[int(N//2)] = .5
    return 2 * np.pi*all_k / N / dt

#############################################
# Utilities for saving, visualizing, calling functions
#############################################


def set_save_to_png():
    global SAVE_TO_PNG
    SAVE_TO_PNG = True
    assert not SAVE_TO_PDF and not SAVE_TO_PGF

def set_save_to_pdf():
    global SAVE_TO_PDF
    SAVE_TO_PDF = True
    assert not SAVE_TO_PGF and not SAVE_TO_PNG

def set_save_to_pgf():
    global SAVE_TO_PGF
    SAVE_TO_PGF = True
    assert not SAVE_TO_PDF and not SAVE_TO_PNG

SAVE_TO_PNG = False
SAVE_TO_PGF = False
SAVE_TO_PDF = False
def show_or_save(name_func):
    """
    By using this function instead plt.show(),
    the user has the possibiliy to use ./figsave name_func
    name_func must be the name of your function
    as a string, e.g. "fig_comparisonData"
    """
    name_fig = name_func[4:]
    directory = "figures_out/"
    if SAVE_TO_PNG:
        print("exporting to directory " + directory)
        import os
        os.makedirs(directory, exist_ok=True)
        plt.savefig(directory + name_fig + '.png')
    elif SAVE_TO_PGF:
        print("exporting to directory " + directory)
        import os
        os.makedirs(directory, exist_ok=True)
        plt.savefig(directory + name_fig + '.pgf')
    elif SAVE_TO_PDF:
        print("exporting to directory " + directory)
        import os
        os.makedirs(directory, exist_ok=True)
        plt.savefig(directory + name_fig + '.pdf')
    else:
        try:
            import matplotlib as mpl
            import os
            os.makedirs(directory, exist_ok=True)
            mpl.rcParams['savefig.directory'] = directory
            fig = plt.get_current_fig_manager()
            fig.canvas.set_window_title(name_fig) 
        except:
            print("cannot set default directory or name")
        plt.show()

"""
    The dictionnary all_figures contains all the functions
    of this module that begins with "fig_".
    When you want to add a figure,
    follow the following rule:
        if the figure is going to be labelled as "fig:foo"
        then the function that generates it should
                                        be named (fig_foo())
    The dictionnary is filling itself: don't try to
    manually add a function.
"""
all_figures = {}

##################################################################################
# Filling the dictionnary all_figures with the functions beginning with "fig_":  #
##################################################################################
# First take all globals defined in this module:
for key, glob in globals().copy().items():
    # Then select the names beginning with fig.
    # Note that we don't check if it is a function,
    # So that a user can give a callable (for example, with functools.partial)
    if key[:3] == "fig":
        all_figures[key] = glob
