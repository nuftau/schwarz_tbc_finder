#!/usr/bin/python3
"""
    This module is the container of the generators of figures.
    The code is redundant, but it is necessary to make sure
    a future change in the default values won't affect old figures...
"""
import bisect
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.animation import FuncAnimation
from memoisation import memoised
from atm1DStratified import Atm1dStratified
from ocean1DStratified import Ocean1dStratified
from universal_functions import Businger_et_al_1971 as businger
from utils_linalg import solve_linear
import figures_unstable
from fortran.visu import import_data
from validation_oce1D import fig_comodoParamsConstantCooling
from validation_oce1D import fig_comodoParamsWindInduced
from validation_oce1D import fig_windInduced, fig_constantCooling
from validation_oce1D import fig_animForcedOcean
from schwarz_coupler import NumericalSetting, schwarz_coupling, projection

mpl.rc('text', usetex=True)
mpl.rcParams['text.latex.preamble']=r"\usepackage{amsmath, amsfonts}"
mpl.rcParams["axes.grid"] = True
mpl.rcParams["grid.linestyle"] = ':'
mpl.rcParams["grid.alpha"] = '0.7'
mpl.rcParams["grid.linewidth"] = '0.5'

DEFAULT_z_levels = np.linspace(0, 1500, 41)
DEFAULT_z_levels_stratified = np.linspace(0, 400, 65)
IFS_z_levels = np.flipud(np.array((1600.04, 1459.58, 1328.43,
    1206.21, 1092.54, 987.00, 889.17, 798.62, 714.94, 637.70,
    566.49, 500.91, 440.58, 385.14, 334.22, 287.51, 244.68,
    205.44, 169.50, 136.62, 106.54, 79.04, 53.92, 30.96,
    10.00))) - 10. # Not really IFS levels, since the list here
# is actually z_half. So the correct way would be to add 0
# and to take the middle of all space step here

IFS_z_levels_stratified = np.flipud(np.array((500.91, 440.58, 385.14,
    334.22, 287.51, 244.68,
    205.44, 169.50, 136.62, 106.54, 79.04, 53.92, 30.96,
    10.00))) - 10. # less levels in the stratified case

def simulation_coupling(dt_oce, dt_atm, T, store_all: bool,
        sf_scheme_a: str, sf_scheme_o: str):
    f = 1e-4 # Coriolis parameter
    time = np.linspace(0, T) # number of time steps is not important
    alpha, N0, rho0, cp = 0.0002, 0.01, 1024., 3985.
    Qswmax = 200.
    srflx = np.maximum(np.cos(2.*np.pi*(time/86400.)), 0. ) * \
            Qswmax / (rho0*cp)
    # TODO look at the sign of Qlw: it should be <0 !!
    Qsw, Qlw = -srflx * rho0*cp, np.ones_like(srflx) * 100.
    z_levels_oce = np.linspace(-50., 0., 51)
    z_levels_atm = IFS_z_levels_stratified
    simulator_oce = Ocean1dStratified(z_levels=z_levels_oce,
            dt=dt_oce, u_geostrophy=0., f=f, alpha=alpha,
            N0=N0)
    mu_m = 6.7e-2 # value of mu_m taken in bulk.py
    K_mol_a = simulator_oce.K_mol / mu_m
    simulator_atm = Atm1dStratified(z_levels=z_levels_atm,
            dt=dt_atm, u_geostrophy=8., K_mol=K_mol_a, f=f)
    delta_sl_o = z_levels_oce[-2]/2
    numer_setting = NumericalSetting(T=T,
            sf_scheme_a=sf_scheme_a, sf_scheme_o=sf_scheme_o,
            delta_sl_a=z_levels_atm[1]/2,
            delta_sl_o=delta_sl_o,
            Q_lw=Qlw,
            Q_sw=Qsw)
    states_atm, states_oce = schwarz_coupling(simulator_oce,
            simulator_atm, numer_setting, store_all=store_all)
    za = simulator_atm.z_half[:-1]
    zo = simulator_oce.z_half[:-1]
    return states_atm, states_oce, za, zo

def fig_coupling():
    dt_oce = 90. # oceanic time step
    dt_atm = 30. # atmosphere time step
    T = 10000 # length of the time window

    states_atm, states_oce, z_half_atm, z_half_oce = \
        memoised(simulation_coupling, dt_oce, dt_atm, T, False)
    fig, axes = plt.subplots(1, 3)
    axes[0].plot(np.real(states_oce[0].last_tstep["u"]), z_half_oce, "r")
    axes[0].plot(np.real(states_atm[1].last_tstep["u"]), z_half_atm, "r")
    axes[0].plot(np.real(states_oce[1].last_tstep["u"]), z_half_oce, "b")
    axes[0].plot(np.real(states_atm[2].last_tstep["u"]), z_half_atm, "b")
    axes[0].plot(np.real(states_oce[2].last_tstep["u"]), z_half_oce, "g")
    axes[0].plot(np.real(states_atm[3].last_tstep["u"]), z_half_atm, "g")

    axes[1].plot((states_oce[0].last_tstep["theta"]), z_half_oce, "r")
    axes[1].plot((states_atm[1].last_tstep["theta"]), z_half_atm, "r")
    axes[1].plot((states_oce[1].last_tstep["theta"]), z_half_oce, "b")
    axes[1].plot((states_atm[2].last_tstep["theta"]), z_half_atm, "b")
    axes[1].plot((states_oce[2].last_tstep["theta"]), z_half_oce, "g")
    axes[1].plot((states_atm[3].last_tstep["theta"]), z_half_atm, "g")
    show_or_save("fig_coupling")

def fig_colormapCoupling():
    dt_oce = 90. # oceanic time step
    dt_atm = 30. # atmosphere time step
    T = 100000 # length of the time window
    states_atm, states_oce, za, zo = \
        memoised(simulation_coupling, dt_oce, dt_atm, T, True,
                sf_scheme_a="FD pure", sf_scheme_o="FD pure")
    state_atm = states_atm[-1]
    state_oce = states_oce[-1]
    fig, axes = plt.subplots(2, 2)
    all_ua = np.real(np.array(state_atm.other["all_u"]))
    all_ta = np.array(state_atm.other["all_theta"])
    uo = np.real(np.array(state_oce.other["all_u"]))
    to = np.array(state_oce.other["all_theta"])
    N_oce = int(T/dt_oce)
    ua = np.zeros((N_oce+1, all_ua.shape[1]))
    ta = np.zeros((N_oce+1, all_ta.shape[1]))
    for i in range(all_ua.shape[1]):
        ua[:, i] = projection(all_ua[:, i], N_oce)
        ta[:, i] = projection(all_ta[:, i], N_oce)

    N_threshold = N_oce//2
    ########## pcolormesh
    x = np.linspace(T/2, T, N_oce+1 - N_threshold)  # len = 10
    Xa, Ya = np.meshgrid(za, x)
    Xo, Yo = np.meshgrid(zo, x)
    vmin = min(np.min(ua), np.min(uo))
    vmax = max(np.max(ua), np.max(uo))

    axes[0, 0].pcolormesh(Ya, Xa, ua[N_threshold+1:, :-1], vmin=vmin,
            vmax=vmax, shading='auto')
    axes[1, 0].pcolormesh(Yo, Xo, uo[N_threshold:, 1:], vmin=vmin,
            vmax=vmax, shading='auto')
    axes[0, 0].set_title("wind, current")

    vmin = min(np.min(ta), np.min(to))
    vmax = max(np.max(ta), np.max(to))
    axes[0, 1].pcolormesh(Ya, Xa, ta[N_threshold+1:, :-1], vmin=vmin,
            vmax=vmax, shading='auto')
    axes[1, 1].pcolormesh(Yo, Xo, to[N_threshold:, 1:], vmin=vmin,
            vmax=vmax, shading='auto')
    axes[0, 1].set_title("Temperature")
    for i in (0, 1):
        for j in (0, 1):
            axes[i,j].set_yscale("symlog", linthresh=0.1)

    show_or_save("fig_colormapCoupling")

def fig_animCoupling():
    dt_oce = 90. # oceanic time step
    dt_atm = 30. # atmosphere time step
    T = 300000 # length of the time window
    states_atm, states_oce, za, zo = \
        memoised(simulation_coupling, dt_oce, dt_atm, T, True,
                sf_scheme_a="FV free", sf_scheme_o="FV free")
    states_atmFD, states_oceFD, _, _ = \
        memoised(simulation_coupling, dt_oce, dt_atm, T, True,
                sf_scheme_a="FD2", sf_scheme_o="FD2")
    state_atm = states_atm[-1]
    state_oce = states_oce[-1]
    state_atmFD = states_atmFD[-1]
    state_oceFD = states_oceFD[-1]
    fig, axes = plt.subplots(2, 2)
    all_ua = np.real(np.array(state_atm.other["all_u"]))
    all_uo = np.real(np.array(state_oce.other["all_u"]))
    all_ta = np.array(state_atm.other["all_theta"])
    all_to = np.array(state_oce.other["all_theta"])
    all_uaFD = np.real(np.array(state_atmFD.other["all_u"]))
    all_uoFD = np.real(np.array(state_oceFD.other["all_u"]))
    all_taFD = np.array(state_atmFD.other["all_theta"])
    all_toFD = np.array(state_oceFD.other["all_theta"])
    line_ua, = axes[0, 0].plot(all_ua[-1], za)
    line_ta, = axes[0, 1].plot(all_ta[-1], za)
    line_uo, = axes[1, 0].plot(all_uo[-1], zo)
    line_to, = axes[1, 1].plot(all_to[-1], zo)
    line_uaFD, = axes[0, 0].plot(all_uaFD[-1], za)
    line_taFD, = axes[0, 1].plot(all_taFD[-1], za)
    line_uoFD, = axes[1, 0].plot(all_uoFD[-1], zo)
    line_toFD, = axes[1, 1].plot(all_toFD[-1], zo)
    axes[0,0].set_yscale("symlog", linthresh=1.)
    axes[0,1].set_yscale("symlog", linthresh=1.)
    axes[1,0].set_yscale("symlog", linthresh=0.1)
    axes[1,1].set_yscale("symlog", linthresh=0.1)

    def init():
        axes[1, 1].set_xlim(260., 290.)
        axes[0, 1].set_xlim(260., 290.)
        axes[0, 0].set_xlim(-4., 15.)
        axes[1, 0].set_xlim(-4., 15.)
        axes[0, 0].set_ylim(za[0], za[-1])
        axes[0, 1].set_ylim(za[0], za[-1])
        axes[1, 0].set_ylim(zo[0], zo[-1])
        axes[1, 1].set_ylim(zo[0], zo[-1])
        return line_ua, line_ta, line_uo, line_to, \
            line_uaFD, line_taFD, line_uoFD, line_toFD
    N_oce = int(T/dt_oce)

    uaFD = np.zeros((N_oce+1, all_ua.shape[1]))
    taFD = np.zeros((N_oce+1, all_ta.shape[1]))
    ua = np.zeros((N_oce+1, all_ua.shape[1]))
    ta = np.zeros((N_oce+1, all_ta.shape[1]))
    for i in range(all_ua.shape[1]):
        ua[:, i] = projection(all_ua[:, i], N_oce)
        ta[:, i] = projection(all_ta[:, i], N_oce)
        uaFD[:, i] = projection(all_uaFD[:, i], N_oce)
        taFD[:, i] = projection(all_taFD[:, i], N_oce)
    def update(frame):
        line_ua.set_data(ua[frame], za)
        line_ta.set_data(ta[frame], za)
        line_uo.set_data(all_uo[frame], zo)
        line_to.set_data(all_to[frame], zo)

        line_uaFD.set_data(uaFD[frame], za)
        line_taFD.set_data(taFD[frame], za)
        line_uoFD.set_data(all_uoFD[frame], zo)
        line_toFD.set_data(all_toFD[frame], zo)
        return line_ua, line_ta, line_uo, line_to, \
            line_uaFD, line_taFD, line_uoFD, line_toFD
    ani = FuncAnimation(fig, update,
            frames=range(0, N_oce, 10),
                    init_func=init, blit=True)

    show_or_save("fig_animCoupling")

def fig_launchOcean():
    PLOT_FOR = True
    dt = 30.
    f = 0.
    T0, alpha, N0 = 16., 0.0002, 0.01
    z_levels = np.linspace(-50., 0., 51)
    simulator_oce = Ocean1dStratified(z_levels=z_levels,
            dt=dt, u_geostrophy=0., f=f, alpha=alpha,
            N0=N0)

    N_FOR = nb_steps = 3600
    N = N_FOR + 1
    time = dt * np.arange(N+1)
    rho0, cp, Qswmax = 1024., 3985., 0.
    srflx = np.maximum(np.cos(2.*np.pi*(time/86400. - 0.5)), 0. ) * \
            Qswmax / (rho0*cp)
    Qsw, Qlw = srflx * rho0*cp, np.zeros_like(srflx)
    u_0 = np.zeros(simulator_oce.M)
    phi_0 = np.zeros(simulator_oce.M+1)
    theta_0 = T0 - N0**2 * np.abs(simulator_oce.z_half[:-1]) / alpha / 9.81
    dz_theta_0 = np.ones(simulator_oce.M+1) * N0**2 / alpha / 9.81
    wind_10m = np.ones(N+1) * 2. + 0j
    temp_10m = np.ones(N+1) * 240

    ret = simulator_oce.FV(u_t0=u_0, phi_t0=phi_0, theta_t0=theta_0,
            dz_theta_t0=dz_theta_0, Q_sw=Qsw, Q_lw=Qlw,
            u_star=np.ones(N+1)*0.01,
            t_star=np.ones(N+1)*1e-6,
            delta_sl_a=10.,
            u_delta=0., t_delta=240.,
            wind_10m=wind_10m,
            temp_10m=temp_10m, sf_scheme="FV test")
    u_current, phi, theta, dz_theta, SL = [ret[x] for x in \
            ("u", "phi", "theta", "dz_theta", "SL")]

    zFV, uFV, thetaFV = simulator_oce.reconstruct_FV(u_current,
            phi, theta, dz_theta, SL, ignore_loglaw=True)

    #### Getting fortran part ####
    name_file = "fortran/t_final_tke.out"
    ret_for, z_for = import_data(name_file)

    #### Plotting both #####
    fig, ax = plt.subplots(1, 1)
    if PLOT_FOR:
        ax.plot(ret_for, z_for, label="Fortran")
    ax.plot(thetaFV, zFV, "--", label="Python")
    ax.legend()
    show_or_save("fig_launchOcean")


def fig_colorplots_FDlowres():
    """
        plots several (2D) variables on a colorplot.
    """
    figures_unstable.colorplot(IFS_z_levels_stratified, False,
            "FD pure", IFS_z_levels_stratified[1]/2, 1)
    show_or_save("fig_colorplots_FDlowres")

def fig_colorplots_FDhighres():
    """
        plots several (2D) variables on a colorplot.
    """
    z_levels= np.linspace(0, IFS_z_levels_stratified[-1], 351)
    figures_unstable.colorplot(z_levels, False, "FD pure",
            z_levels[1]/2, 3)
    show_or_save("fig_colorplots_FDhighres")

def fig_colorplots_FVhighres():
    """
        plots several (2D) variables on a colorplot.
    """
    z_levels= np.linspace(0, IFS_z_levels_stratified[-1], 351)
    figures_unstable.colorplot(z_levels, True, "FV free",
            IFS_z_levels_stratified[1]/2, 35)
    show_or_save("fig_colorplots_FVhighres")

def fig_colorplots_FVlowres():
    """
        plots several (2D) variables on a colorplot.
    """
    figures_unstable.colorplot(IFS_z_levels_stratified, True,
            "FV free", IFS_z_levels_stratified[1]/2, 3)
    show_or_save("fig_colorplots_FVlowres")

def fig_colorplots_FV2highres():
    """
        plots several (2D) variables on a colorplot.
    """
    z_levels= np.linspace(0, IFS_z_levels_stratified[-1], 351)
    figures_unstable.colorplot(z_levels, True, "FV2",
            z_levels[1], 35)
    show_or_save("fig_colorplots_FVhighres")

def fig_colorplots_FV2lowres():
    """
        plots several (2D) variables on a colorplot.
    """
    z_levels= IFS_z_levels_stratified
    z_levels_FV2 = np.concatenate(([0., z_levels[1]/2], z_levels[1:]))
    figures_unstable.colorplot(z_levels_FV2, True,
            "FV2", z_levels_FV2[1], 3)
    show_or_save("fig_colorplots_FVlowres")


def fig_consistency_comparisonUnstable():
    """
        Integrates for 1 day a 1D ekman equation
        with TKE turbulence scheme.
    """
    z_levels = DEFAULT_z_levels_stratified
    z_levels = IFS_z_levels_stratified
    z_levels_FV2 = np.concatenate(([0., z_levels[1]/2], z_levels[1:]))
    # z_levels_les= np.linspace(0, 400, 651)
    z_levels_les= np.linspace(0, z_levels[-1], 351)
    dt = 50.
    N = int(3*24*3600/dt) # 28*3600/10=3240

    fig, axes = plt.subplots(1,5, figsize=(7.5, 3.5))
    fig.subplots_adjust(left=0.08, bottom=0.14, wspace=0.7, right=0.99)
    col_FDpure = "g"
    col_FV1 = "b"
    col_FVfree = "r"
    def style(col, linestyle='solid', **kwargs):
        return {"color": col, "linestyle": linestyle,
                "linewidth":1.5, **kwargs}
    # High resolution:
    plot_FDStratified(axes, "FD pure", N=N, dt=dt, z_levels=z_levels_les, stable=False,
            name="FD, M=350", style=style(col_FDpure))
    # plot_FVStratified(axes, "FV1", delta_sl=z_levels_les[1]/2,
    #         N=N, dt=dt, z_levels=z_levels_les, stable=False,
    #         name="FV1, M=350", style=style(col_FV1))
    plot_FVStratified(axes, "FV2", delta_sl=z_levels_les[1],
            N=N, dt=dt, z_levels=z_levels_les, stable=False,
            name="FV2, M=350", style=style("c"))
    # plot_FVStratified(axes, "FV pure", delta_sl=z_levels_les[1]/2,
    #         N=N, dt=dt, z_levels=z_levels_les, stable=False,
    #         name="FV pure, M=350", style=style("m"))
    plot_FVStratified(axes, "FV free", delta_sl=z_levels[1]/2,
            N=N, dt=dt, z_levels=z_levels_les, stable=False,
            name="FV free, M=350", style=style(col_FVfree))

    # Low resolution:
    plot_FDStratified(axes, "FD pure", N=N, dt=dt, z_levels=z_levels,
            name="FD, M="+str(z_levels.shape[0]),
            style=style(col_FDpure, "dotted"), stable=False)
    # plot_FVStratified(axes, "FV1", delta_sl=z_levels[1]/2,
    #         N=N, dt=dt, z_levels=z_levels, stable=False,
    #         name=None, style=style(col_FV1, "dotted"))
    plot_FVStratified(axes, "FV2", delta_sl=z_levels[1]/2,
            N=N, dt=dt, z_levels=z_levels_FV2, stable=False,
            name=None, style=style("c", "dotted"))
    # plot_FVStratified(axes, "FV pure", delta_sl=z_levels[1]/2,
    #         N=N, dt=dt, z_levels=z_levels, stable=False,
    #         name=None, style=style("m", "dotted"))
    plot_FVStratified(axes, "FV free", delta_sl=z_levels[1]/2,
            N=N, dt=dt, z_levels=z_levels, stable=False,
            name=None, style=style(col_FVfree, "dotted"))

    axes[0].set_xlabel(r"wind speed ($|u|, m.s^{-1}$)")
    axes[0].set_ylabel("height (m)")
    axes[1].set_xlabel(r"Potential Temperature ($\theta$, K)")
    axes[1].set_ylabel("height (m)")
    axes[2].set_xlabel("energy (J)")
    axes[2].set_ylabel("height (m)")
    axes[2].legend(loc="upper right")
    axes[3].set_ylim(top=0.28, bottom=0.16)
    axes[3].set_ylabel("friction velocity (u*, $m.s^{-1}$)")
    axes[3].set_xlabel("time (s)")
    axes[4].set_xlabel("mixing length (m)")
    axes[4].set_ylabel("height (m)")
    show_or_save("fig_consistency_comparisonUnstable")

def fig_consistency_comparisonStratified():
    """
        Integrates for 1 day a 1D ekman equation
        with TKE turbulence scheme.
    """
    z_levels = DEFAULT_z_levels_stratified
    z_levels = IFS_z_levels_stratified
    z_levels_FV2 = np.concatenate(([0., z_levels[1]/2], z_levels[1:]))
    # z_levels_les= np.linspace(0, 400, 651)
    z_levels_les= np.linspace(0, z_levels[-1], 351)
    dt = 10.
    N = 5*650 # 28*3600/10=3240

    fig, axes = plt.subplots(1,5, figsize=(7.5, 3.5))
    fig.subplots_adjust(left=0.08, bottom=0.14, wspace=0.7, right=0.99)
    col_FDpure = "g"
    col_FV1 = "b"
    col_FVfree = "r"
    def style(col, linestyle='solid', **kwargs):
        return {"color": col, "linestyle": linestyle,
                "linewidth":1.5, **kwargs}

    # High resolution:
    plot_FDStratified(axes, "FD pure", N=N, dt=dt, z_levels=z_levels_les,
            name="FD, M=350", style=style(col_FDpure))
    plot_FVStratified(axes, "FV1", delta_sl=z_levels_les[1]/2,
            N=N, dt=dt, z_levels=z_levels_les,
            name="FV1, M=350", style=style(col_FV1))
    plot_FVStratified(axes, "FV2", delta_sl=z_levels_les[1],
            N=N, dt=dt, z_levels=z_levels_les,
            name="FV2, M=350", style=style("c"))
    # plot_FVStratified(axes, "FV pure", delta_sl=z_levels_les[1]/2,
    #         N=N, dt=dt, z_levels=z_levels_les,
    #         name="FV pure, M=350", style=style("m"))
    plot_FVStratified(axes, "FV free", delta_sl=z_levels[1]/2,
            N=N, dt=dt, z_levels=z_levels_les,
            name="FV free, M=350", style=style(col_FVfree))

    # Low resolution:
    plot_FDStratified(axes, "FD pure", N=N, dt=dt, z_levels=z_levels,
            name="FD, M="+str(z_levels.shape[0]), style=style(col_FDpure, "dotted"))
    plot_FVStratified(axes, "FV1", delta_sl=z_levels[1]/2,
            N=N, dt=dt, z_levels=z_levels,
            name=None, style=style(col_FV1, "dotted"))
    plot_FVStratified(axes, "FV2", delta_sl=z_levels[1]/2,
            N=N, dt=dt, z_levels=z_levels_FV2,
            name=None, style=style("c", "dotted"))
    # plot_FVStratified(axes, "FV pure", delta_sl=z_levels[1]/2,
    #         N=N, dt=dt, z_levels=z_levels,
    #         name=None, style=style("m", "dotted"))
    plot_FVStratified(axes, "FV free", delta_sl=z_levels[1]/2,
            N=N, dt=dt, z_levels=z_levels,
            name=None, style=style(col_FVfree, "dotted"))

    axes[0].set_xlabel(r"wind speed ($|u|, m.s^{-1}$)")
    axes[0].set_ylabel("height (m)")
    axes[1].set_xlabel(r"Potential Temperature ($\theta$, K)")
    axes[1].set_ylabel("height (m)")
    axes[2].set_xlabel("energy (J)")
    axes[2].set_ylabel("height (m)")
    axes[2].legend(loc="upper right")
    axes[3].set_ylim(top=0.28, bottom=0.16)
    axes[3].set_ylabel("friction velocity (u*, $m.s^{-1}$)")
    axes[3].set_xlabel("time (s)")
    axes[4].set_xlabel("mixing length (m)")
    axes[4].set_ylabel("height (m)")
    show_or_save("fig_consistency_comparisonStratified")

def compute_with_sfStratified(sf_scheme, z_levels, dt=10., N=3240,
        stable=True, delta_sl=None, z_constant=None):
    """
    return z_fv, u_fv, theta_fv, z_tke, TKE, ustar
    """
    if delta_sl is None:
        print("warning: no delta_sl entered")
        delta_sl = z_levels[1]/2
    if z_constant is None:
        z_constant = 2*delta_sl

    M = z_levels.shape[0] - 1
    simulator = Atm1dStratified(z_levels=z_levels,
            dt=dt, u_geostrophy=8.,
            K_mol=1e-4, f=1.39e-4)
    T0 = 265.
    u_0 = 8*np.ones(M) + 0j
    phi_0 = np.zeros(M+1) + 0j
    t_0, dz_theta_0 = simulator.initialize_theta(Neutral_case=False)
    forcing = 1j*simulator.f*simulator.u_g*np.ones((N+1, M))
    if stable:
        SST = np.concatenate(([265],
            [265 - 0.25*(dt*(n-1))/3600. for n in range(1, N+1)]))
    else: # diurnal cycle:
        SST = np.concatenate(([265],
            [265 + 2.*np.sin((dt*(n-1))/3600. * np.pi / 12.)\
                    for n in range(1, N+1)]))

    z_tke = np.copy(simulator.z_full)
    k = bisect.bisect_right(z_levels[1:], delta_sl)
    z_tke[k] = delta_sl #
    u_deltasl = 8. # first guess before the iterations
    t_deltasl = T0 # first guess before the iterations
    Q_sw, Q_lw, delta_sl_o = np.zeros(N+1), np.zeros(N+1), 0.
    u_o, t_o = np.zeros(N+1), SST
    if sf_scheme in {"FV1 free", "FV2 free", "FV free", "FV2"}:
        u_i, phi_i, t_i, dz_theta_i, u_delta_i, t_delta_i = \
                simulator.initialization(u_0, phi_0, t_0, dz_theta_0,
                        delta_sl, u_o[0], t_o[0], Q_sw[0], Q_lw[0],
                        z_constant, delta_sl_o)
    else:
        u_i, phi_i, t_i, dz_theta_i, u_delta_i, t_delta_i = \
                u_0, phi_0, t_0, dz_theta_0, u_deltasl, t_deltasl

    ret = simulator.FV(u_t0=u_i, phi_t0=phi_i, theta_t0=t_i,
                    delta_sl_o=0.,
                    dz_theta_t0=dz_theta_i, Q_sw=Q_sw, Q_lw=Q_lw,
                    u_o=u_o, SST=SST, sf_scheme=sf_scheme,
                    u_delta=u_delta_i, t_delta=t_delta_i,
                    forcing=forcing, delta_sl=delta_sl)
    u, phi, tke_full, ustar, temperature, dz_theta, l_eps, SL = \
            [ret[x] for x in ("u", "phi", "tke", "all_u_star",
                "theta", "dz_theta", "l_eps", "SL")]

    z_fv, u_fv, theta_fv = simulator.reconstruct_FV(u, phi, temperature,
            dz_theta, SL=SL)
    z_tke = simulator.z_full
    return z_fv, u_fv, theta_fv, z_tke, tke_full, ustar, l_eps

def compute_with_sfNeutral(sf_scheme, z_levels, dt, N, delta_sl):
    """
    return z_fv, u_fv, theta_fv, z_tke, TKE, ustar
    """
    M = z_levels.shape[0] - 1
    simulator = Atm1dStratified(z_levels=z_levels,
            dt=dt, u_geostrophy=10.,
            K_mol=1e-4, f=1e-4)
    u_0 = 10.*np.ones(M)
    phi_0 = np.zeros(M+1)
    forcing = 1j*simulator.f*simulator.u_g*np.ones((N+1, M))
    SST = np.ones(N+1)*265.
    z_tke = np.copy(simulator.z_full)
    k = bisect.bisect_right(z_levels[1:], delta_sl)
    z_tke[k] = delta_sl #
    u_deltasl = 10. # first guess before the iterations
    if sf_scheme in {"FV1 free", "FV2 free", "FV free", "FV2"}:
        zk = z_levels[k]
        h_tilde = z_levels[k+1] - delta_sl
        h_kp12 = z_levels[k+1] - z_levels[k]
        z_0M = 1e-1
        u_constant = 10.
        K_mol, kappa = simulator.K_mol, simulator.kappa
        for _ in range(15):
            u_star = kappa / np.log(1+delta_sl/z_0M) * np.abs(u_deltasl)
            z_0M = K_mol / kappa / u_star

            phi_0[k] = u_deltasl / (z_0M+delta_sl) / \
                    np.log(1+delta_sl/z_0M)
            # u_tilde + h_tilde (phi_0 / 6 + phi_1 / 3) = u_constant
            # (subgrid reconstruction at the top of the volume)
            u_tilde = u_constant - h_tilde/6 * phi_0[k]
            u_deltasl = u_tilde - h_tilde / 3 * phi_0[k]

        neutral_tau_sl = (delta_sl / (h_kp12))* \
                (1+z_0M/delta_sl - 1/np.log(1+delta_sl/z_0M) \
                + (zk - (zk+z_0M)*np.log(1+zk/z_0M)) \
                / (delta_sl * np.log(1+delta_sl/z_0M)))

        alpha_sl = h_tilde/h_kp12 + neutral_tau_sl
        u_0[k] = alpha_sl * u_tilde - neutral_tau_sl*h_tilde*phi_0[k]/3

    t_0, dz_theta_0 = 265 * np.ones(M), np.zeros(M+1)
    ret = simulator.FV(u_t0=u_0, phi_t0=phi_0, theta_t0=t_0,
                    delta_sl_o=0.,
                    dz_theta_t0=dz_theta_0,
                    Q_sw=np.zeros(N+1), Q_lw=np.zeros(N+1),
                    u_o=np.zeros(N+1), Neutral_case=True,
                    SST=SST, sf_scheme=sf_scheme, u_delta=u_deltasl,
                    forcing=forcing, delta_sl=delta_sl)
    u, phi, tke_full, u_star, temperature, dz_theta, SL = \
            [ret[x] for x in ("u", "phi", "tke", "all_u_star",
                "theta", "dz_theta", "SL")]

    z_fv, u_fv, theta_fv = simulator.reconstruct_FV(u, phi, temperature,
            dz_theta, SL=SL)
    z_tke = simulator.z_full
    return z_fv, u_fv, theta_fv, z_tke, tke_full, ustar

def plot_FVStratified(axes, sf_scheme, dt=10., N=3240,
        z_levels=DEFAULT_z_levels_stratified,
        stable: bool=True, delta_sl=None,
        name=None, style={}):

    z_fv, u_fv, theta_fv, z_tke, TKE, ustar, l_eps = \
            compute_with_sfStratified(sf_scheme, z_levels, dt, N,
                    stable, delta_sl)
    axes[0].semilogy(np.abs(u_fv), z_fv, **style)
    axes[1].semilogy(theta_fv, z_fv, **style)
    axes[2].semilogy(TKE, z_tke, **style, label=name)
    axes[3].plot(dt*np.array(range(len(ustar))), ustar, **style)
    k = bisect.bisect_right(z_levels[1:], delta_sl)
    z_leps = np.copy(z_levels)
    z_leps[k] = delta_sl
    axes[4].semilogy(l_eps, z_leps, **style)

def plot_FDStratified(axes, sf_scheme, dt=10., N=3240,
        z_levels=DEFAULT_z_levels_stratified, stable: bool=True,
        name=None, style={}):
    if name is None:
        name = sf_scheme
    M = z_levels.shape[0] - 1
    simulator = Atm1dStratified(z_levels=z_levels,
            dt=dt, u_geostrophy=8.,
            K_mol=1e-4, f=1.39e-4)
    u_0 = 8*np.ones(M)
    forcing = 1j*simulator.f*simulator.u_g*np.ones((N+1, M))
    if stable:
        SST = np.concatenate(([265],
            [265 - 0.25*(dt*(n-1))/3600. for n in range(1, N+1)]))
    else: # diurnal cycle:
        SST = np.concatenate(([265],
            [265 + 2.*np.sin((dt*(n-1))/3600. * np.pi / 12.)\
                    for n in range(1, N+1)]))
    theta, _ = simulator.initialize_theta(Neutral_case=False)
    ret = simulator.FD(u_t0=u_0, u_o=np.zeros(N+1),
            theta_t0=theta, Q_sw=np.zeros(N+1),
            delta_sl_o=0.,
            SST=SST, Q_lw=np.zeros(N+1),
            sf_scheme=sf_scheme, forcing=forcing)
    u, TKE, ustar, temperature, l_eps = [ret[x] for x in \
            ("u", "tke", "all_u_star", "theta", "l_eps")]
    z_tke = np.copy(simulator.z_full)
    z_tke[0] = 0.1

    axes[0].semilogy(np.abs(u), simulator.z_half[:-1], **style)
    axes[1].semilogy(temperature, simulator.z_half[:-1], **style)
    axes[2].semilogy(TKE, z_tke, **style, label=name)
    axes[3].plot(dt*np.array(range(len(ustar))), ustar, **style)
    axes[4].semilogy(l_eps, z_tke, **style)

def plot_FD(axes, sf_scheme, dt=60., N=1680,
        z_levels=DEFAULT_z_levels, name=None, style={}):
    if name is None:
        name = sf_scheme
    M = z_levels.shape[0] - 1
    simulator = Atm1dStratified(z_levels=z_levels,
            dt=dt, u_geostrophy=10., K_mol=1e-4, f=1e-4)

    u_0 = 10*np.ones(M)
    forcing = 1j*simulator.f * simulator.u_g*np.ones((N+1, M))
    SST = 265. * np.ones(N+1) # Neutral SST with theta=const=265.
    ret = simulator.FD(u_t0=u_0,
            u_o=np.zeros(N+1),
            delta_sl_o=0.,
            theta_t0=265*np.ones(M), Q_sw=np.zeros(N+1),
            SST=SST, Q_lw=np.zeros(N+1), Neutral_case=True,
            sf_scheme=sf_scheme, forcing=forcing)
    u, TKE, ustar = [ret[x] for x in ("u", "tke", "all_u_star")]
    z_tke = np.copy(simulator.z_full)

    z_tke = np.copy(simulator.z_full)
    z_tke[0] = z_levels[1]/2 if sf_scheme != "FD2" else 0.1

    axes[0].plot(np.real(u), simulator.z_half[:-1], **style)
    axes[1].plot(np.imag(u), simulator.z_half[:-1], **style)
    axes[2].plot(TKE, z_tke, **style, label=name)
    axes[3].plot(dt*np.array(range(len(ustar))), ustar, **style)

def plot_FV(axes, sf_scheme, delta_sl, dt=60., N=1680,
        z_levels=DEFAULT_z_levels, name=None, style={}):
    z_fv, u_fv, theta_fv, z_tke, TKE, ustar = \
            compute_with_sfNeutral(sf_scheme, z_levels, dt, N,
                    delta_sl)

    axes[0].semilogy(np.real(u_fv), z_fv, **style)
    axes[1].semilogy(np.imag(u_fv), z_fv, **style)
    axes[2].semilogy(TKE, z_tke, **style, label=name)
    axes[3].plot(dt*np.array(range(len(ustar))), ustar, **style)

def fig_consistency_comparison():
    """
        Integrates for 1 day a 1D ekman equation
        with TKE turbulence scheme.
    """
    z_levels= np.linspace(0, 1500, 41)
    z_levels= IFS_z_levels
    z_levels_les= np.linspace(0, IFS_z_levels[-1], 401)
    z_levels_FV2 = np.concatenate(([0., z_levels[1]/2], z_levels[1:]))
    # for FV with FV interpretation of sf scheme,
    # the first grid level is divided by 2 so that
    # delta_{sl} is the same in all the schemes.
    dt = 60.
    N = 1680 # 28*60=1680

    fig, axes = plt.subplots(1,4, figsize=(7.5, 3.5))
    fig.subplots_adjust(left=0.08, bottom=0.14, wspace=0.7, right=0.99)
    col_FDpure = "g"
    col_FV1 = "b"
    col_FVfree = "r"
    def style(col, linestyle='solid', **kwargs):
        return {"color": col, "linestyle": linestyle,
                "linewidth":1.5, **kwargs}

    # High resolution:
    plot_FD(axes, "FD pure", N=N, dt=dt, z_levels=z_levels_les,
            name="FD, M=400", style=style(col_FDpure))
    plot_FV(axes, "FV1", delta_sl=z_levels_les[1]/2,
            N=N, dt=dt, z_levels=z_levels_les,
            name="FV1, M=400", style=style(col_FV1))
    plot_FV(axes, "FV2", delta_sl=z_levels_les[1],
            N=N, dt=dt, z_levels=z_levels_les,
            name="FV2, M=400", style=style("c"))
    # plot_FV(axes, "FV pure", delta_sl=z_levels_les[1]/2,
    #         N=N, dt=dt, z_levels=z_levels_les,
    #         name="FV pure, M=400", style=style("m"))
    plot_FV(axes, "FV free", delta_sl=z_levels[1]/2,
            N=N, dt=dt, z_levels=z_levels_les,
            name="FV free, M=400", style=style(col_FVfree))

    # Low resolution:

    plot_FD(axes, "FD pure", N=N, dt=dt, z_levels=z_levels,
            name="FD, M="+str(z_levels.shape[0] - 1),
            style=style(col_FDpure, "dotted"))
    plot_FV(axes, "FV1", delta_sl=z_levels[1]/2,
            N=N, dt=dt, z_levels=z_levels,
            name=None, style=style(col_FV1, "dotted"))
    plot_FV(axes, "FV2", delta_sl=z_levels[1]/2,
            N=N, dt=dt, z_levels=z_levels_FV2,
            name=None, style=style("c", "dotted"))
    # plot_FV(axes, "FV pure", delta_sl=z_levels[1]/2,
    #         N=N, dt=dt, z_levels=z_levels,
    #         name=None, style=style("m", "dotted"))
    plot_FV(axes, "FV free", delta_sl=z_levels[1]/2,
            N=N, dt=dt, z_levels=z_levels,
            name=None, style=style(col_FVfree, "dotted"))

    axes[0].set_ylim(top=1500.)
    axes[1].set_ylim(top=1500.)
    axes[0].set_xlabel("wind speed (u, $m.s^{-1}$)")
    axes[0].set_ylabel("height (m)")
    axes[1].set_xlabel("wind speed (v, $m.s^{-1}$)")
    axes[1].set_ylabel("height (m)")
    axes[2].set_xlabel("energy (J)")
    axes[2].set_ylabel("height (m)")
    axes[3].set_ylabel("friction velocity (u*, $m.s^{-1}$)")
    axes[3].set_ylim(top=0.5, bottom=0.38)
    axes[3].set_xlabel("time (s)")
    axes[0].legend(loc="upper right")
    axes[1].legend(loc="upper right")
    axes[2].legend(loc="upper right")
    show_or_save("fig_consistency_comparison")

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
            fig.set_window_title(name_fig) 
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
