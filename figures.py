#!/usr/bin/python3
"""
    This module is the container of the generators of figures.
    The code is redundant, but it is necessary to make sure
    a future change in the default values won't affect old figures...
"""
import numpy as np
from memoisation import memoised
import matplotlib.pyplot as plt
import matplotlib as mpl
mpl.rc('text', usetex=True)
mpl.rcParams['text.latex.preamble']=r"\usepackage{amsmath, amsfonts}"
mpl.rcParams["axes.grid"] = True
mpl.rcParams["grid.linestyle"] = ':'
mpl.rcParams["grid.alpha"] = '0.7'
mpl.rcParams["grid.linewidth"] = '0.5'

def fig_integration_1dekman():
    from simu1DEkman import Simu1dEkman
    z_levels= np.linspace(0, np.sqrt(1200), 100)**2
    z_levels= np.linspace(0, 1200, 100)
    M = z_levels.shape[0] - 1
    dt = 100.
    N = 100
    simulator = Simu1dEkman(z_levels=z_levels,
            h_cl=1e4, dt=dt, u_geostrophy=10.,
            K_mol=1e-7, C_D=1e-3, f=1e-4)
    # choosing u_0 linear so it can be the same FD, FV
    u_0 = 10 - 7*np.linspace(1, 0, 100)
    dirichlet = 3*np.ones(N+1)
    forcing = np.zeros((N+1, M + 1))

    u_N1 = simulator.FD_KPP(u_t0=u_0,
            forcing=forcing)

    phi_0 = np.diff(u_0, append=11) / np.diff(z_levels, append=1300)
    phi_0[-1] = phi_0[-2] # correcting the last flux

    u_FV_sffd, phi_FV_sffd = simulator.FV_KPP(u_t0=u_0[:-1],
            phi_t0=phi_0,
            forcing=forcing[:, :-1],
            sf_scheme="FD")

    u_FV_sffv, phi_FV_sffv = simulator.FV_KPP(u_t0=u_0[:-1],
            phi_t0=phi_0,
            forcing=forcing[:, :-1],
            sf_scheme="FV")
    z_subgrid, u_full_sffd = simulator.reconstruct_FV(u_bar = u_FV_sffd, phi=phi_FV_sffd)
    z_subgrid, u_full_sffv = simulator.reconstruct_FV(u_bar = u_FV_sffv, phi=phi_FV_sffv)

    fig, axes = plt.subplots(1,1, figsize=(3.5, 3.5))
    fig.subplots_adjust(left=0.21, bottom=0.14)
    axes.plot(np.real(u_0), z_levels, label="$\mathfrak{R}( u_0)$")
    axes.plot(np.real(u_N1), z_levels, label="$\mathfrak{R}(u_{FD})$")
    axes.plot(np.real(u_full_sffd), z_subgrid, label="$\mathfrak{R}(u_{FV})$ (FD inter.)")
    axes.plot(np.real(u_full_sffv), z_subgrid, "--", label="$\mathfrak{R}(u_{FV})$ (FV inter.)")
    #axes.plot(np.real(u_N3), z_levels, label="$u_{N3}$")
    axes.set_xlabel("wind speed ($m.s^{-1}$)")
    axes.set_ylabel("height (m)")
    axes.legend()
    show_or_save("fig_integration_1dekman")


def fig_stationary_compare():
    import simulator
    NUMBER_OF_LEVELS = 100
    H = 1200.
    H_cfl = 50.
    H_bl = 1000.
    NUMBER_ITERATION = 3000
    skip_iterations = 10
    z = np.linspace(1, H, NUMBER_OF_LEVELS)

    errors, profile, viscosity = simulator.stationary_case_KPP(z, H_cfl=H_cfl, H_bl=H_bl, NUMBER_ITERATION=NUMBER_ITERATION)
    # print(errors)
    fig, axes = plt.subplots(1,3, figsize=(7.5, 2.5))
    fig.subplots_adjust(wspace=0.53, left=0.22, bottom=0.22)
    axes[0].semilogy(range(0, len(errors), skip_iterations),
            np.array(errors)[::skip_iterations] / np.sqrt(NUMBER_OF_LEVELS) * np.sqrt(H), "k+")
    axes[0].set_xlabel("iteration")
    axes[0].set_ylabel(r"$||u_{n+1} - u_n||_2$")
    axes[1].axhline(H_cfl, color="k", linestyle="dashed")
    axes[1].axhline(H_bl, color="grey", linestyle="dashed")
    axes[1].plot(np.real(profile), z, label="u")
    axes[1].plot(np.imag(profile), z, label="v")
    axes[1].legend(loc="center")
    axes[1].set_xlabel("u(z), v(z)")
    axes[1].set_ylabel("z")
    axes[2].axhline(H_cfl, linestyle="dashed", color="black", label=r"$\delta_{cfl}$")
    axes[2].axhline(H_bl, linestyle="dashed", color="grey", label=r"$H_{bl}$")
    axes[2].plot(viscosity, np.concatenate(([0],(z[1:] + z[:-1])/2)))
    axes[2].set_xlabel("K(z)")
    axes[2].set_ylabel("z")
    axes[2].legend(loc="center")
    # axes[3].axhline(H_cfl, linestyle="dashed", color="black")
    # axes[3].axhline(H_bl, linestyle="dashed", color="grey")
    # axes[3].plot(l, (z[1:] + z[:-1])/2)
    # axes[3].set_xlabel(r"$l_m(z)$")
    # axes[3].set_ylabel("z")
    show_or_save("fig_stationary_test")

def fig_stationary_test():
    import simulator
    NUMBER_OF_LEVELS = 1000
    H = 1200.
    H_cfl = 50.
    H_bl = 1000.
    NUMBER_ITERATION = 1000000
    z = np.linspace(0, H, NUMBER_OF_LEVELS)

    errors, profile, viscosity, l = simulator.stationary_case_MOST(z, H_cfl=H_cfl, H_bl=H_bl, NUMBER_ITERATION=NUMBER_ITERATION)
    # print(errors)
    fig, axes = plt.subplots(1,4, figsize=(7.5, 2.5))
    fig.subplots_adjust(wspace=0.53, left=0.22, bottom=0.22)
    skip_iterations = 1000
    axes[0].semilogy(range(0, len(errors), skip_iterations),
            np.array(errors)[::skip_iterations] / np.sqrt(NUMBER_OF_LEVELS) * np.sqrt(H), "k+")
    axes[0].set_xlabel("iteration")
    axes[0].set_ylabel(r"$||u_{n+1} - u_n||_2$")
    axes[1].axhline(H_cfl, color="k", linestyle="dashed")
    axes[1].axhline(H_bl, color="grey", linestyle="dashed")
    axes[1].plot(np.real(profile), z, label="u")
    axes[1].plot(np.imag(profile), z, label="v")
    axes[1].legend(loc="center")
    axes[1].set_xlabel("u(z), v(z)")
    axes[1].set_ylabel("z")
    axes[2].axhline(H_cfl, linestyle="dashed", color="black", label=r"$\delta_{cfl}$")
    axes[2].axhline(H_bl, linestyle="dashed", color="grey", label=r"$H_{bl}$")
    axes[2].plot(viscosity, (z[1:] + z[:-1])/2)
    axes[2].set_xlabel("K(z)")
    axes[2].set_ylabel("z")
    axes[2].legend(loc="center")
    axes[3].axhline(H_cfl, linestyle="dashed", color="black")
    axes[3].axhline(H_bl, linestyle="dashed", color="grey")
    axes[3].plot(l, (z[1:] + z[:-1])/2)
    axes[3].set_xlabel(r"$l_m(z)$")
    axes[3].set_ylabel("z")
    show_or_save("fig_stationary_test")

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
