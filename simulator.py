#!/usr/bin/python3
"""
    This module provides functions to observe real convergence factors.
"""
import time
import functools
import numpy as np
from numpy import pi

def frequency_simulation(discretization, N, number_samples=100, **kwargs):
    """
        Simulate and returns directly errors in frequencial domain.
        number_samples simulations are done to have
        an average on all possible first guess.
        Every argument should be given in discretization.
        N is the number of time steps.
        kwargs can contain any argument of interface_errors:
        Lambda_1, Lambda_2, a, c, dt, M1, M2,
    """
    import concurrent.futures
    from numpy.fft import fft, fftshift
    to_map = functools.partial(interface_errors, discretization, N,
                               **kwargs)
    print(number_samples, "samples")

    from progressbar import ProgressBar
    progressbar = ProgressBar(maxval=number_samples)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        errors = []
        for result in progressbar(executor.map(to_map, range(number_samples))):
            errors += [result]
    freq_err = fftshift(fft(np.array(errors), axis=-1), axes=(-1, ))
    return np.std(freq_err, axis=0)


def interface_errors(discretization,
                     time_window_len,
                     seed=9380,
                     NUMBER_IT=2):
    """
        returns errors at interface from beginning (first guess) until the end.
    """
    f1 = np.zeros(discretization.size_f(upper_domain=False))
    f2 = np.zeros(discretization.size_f(upper_domain=True))
    neumann = 0
    dirichlet = 0

    precomputed_Y1 = discretization.precompute_Y(f=f1, bd_cond=dirichlet,
                                                 upper_domain=False)

    precomputed_Y2 = discretization.precompute_Y(f=f2, bd_cond=neumann,
                                                 upper_domain=True)

    u1_0 = np.zeros(discretization.size_prognostic(upper_domain=False))
    u2_0 = np.zeros(discretization.size_prognostic(upper_domain=True))
    # random false initialization:
    np.random.seed(seed)
    all_u1_interface = np.concatenate(([0], 2 * (np.random.rand(time_window_len) - 0.5)))
    all_phi1_interface = np.concatenate(([0], 2 * (np.random.rand(time_window_len) - 0.5)))
    ret = [all_u1_interface[1:]]
    # Beginning of schwarz iterations:
    from scipy.interpolate import interp1d
    for k in range(NUMBER_IT):
        all_u2_interface = [0]
        all_phi2_interface = [0]
        last_u2 = u2_0
        additional = []
        # Time iteration:
        interpolator_u1 = interp1d(x=np.array(range(time_window_len+1)), y=all_u1_interface, kind='cubic')
        interpolator_phi1 = interp1d(x=np.array(range(time_window_len+1)), y=all_phi1_interface, kind='cubic')

        for i in range(1, time_window_len+1):
            u_nm1_interface = all_u1_interface[i-1]
            phi_nm1_interface = all_phi1_interface[i-1]
            u_nm1_2_interface = interpolator_u1(i-1/2)
            phi_nm1_2_interface = interpolator_phi1(i-1/2)
            u_interface = all_u1_interface[i]
            phi_interface = all_phi1_interface[i]

            u2_ret, u_interface, phi_interface, *additional = \
                    discretization.integrate_one_step(
                f=f2,
                f_nm1=f2,
                f_nm1_2=f2,
                bd_cond=neumann,
                bd_cond_nm1_2=neumann,
                bd_cond_nm1=neumann,
                u_nm1=last_u2,
                u_interface=u_interface,
                phi_interface=phi_interface,
                u_nm1_2_interface=u_nm1_2_interface,
                phi_nm1_2_interface=phi_nm1_2_interface,
                u_nm1_interface=u_nm1_interface,
                phi_nm1_interface=phi_nm1_interface,
                additional=additional,
                upper_domain=True,
                Y=precomputed_Y2)
            last_u2 = u2_ret
            all_u2_interface += [u_interface]
            all_phi2_interface += [phi_interface]

        all_u1_interface = [0]
        all_phi1_interface = [0]
        last_u1 = u1_0
        additional = []

        interpolator_u2 = interp1d(x=np.array(range(time_window_len+1)), y=all_u2_interface, kind='cubic')
        interpolator_phi2 = interp1d(x=np.array(range(time_window_len+1)), y=all_phi2_interface, kind='cubic')
        for i in range(1, time_window_len+1):

            u_interface = all_u2_interface[i]
            phi_interface = all_phi2_interface[i]
            u_nm1_2_interface = interpolator_u2(i-1/2)
            phi_nm1_2_interface = interpolator_phi2(i-1/2)
            u_nm1_interface = all_u2_interface[i-1]
            phi_nm1_interface = all_phi2_interface[i-1]

            u1_ret, u_interface, phi_interface, *additional = \
                    discretization.integrate_one_step(
                f=f1,
                f_nm1_2=f1, #0 anywayy
                f_nm1=f1,#0 anywayy
                bd_cond=dirichlet,
                bd_cond_nm1_2=dirichlet,
                bd_cond_nm1=dirichlet,
                u_nm1=last_u1,
                u_interface=u_interface,
                phi_interface=phi_interface,
                u_nm1_interface=u_nm1_interface,
                phi_nm1_interface=phi_nm1_interface,
                u_nm1_2_interface=u_nm1_2_interface,
                phi_nm1_2_interface=phi_nm1_2_interface,
                additional=additional,
                upper_domain=False,
                Y=precomputed_Y1)
            last_u1 = u1_ret
            all_u1_interface += [u_interface]
            all_phi1_interface += [phi_interface]

        ret += [all_u1_interface[1:]]

    return ret


if __name__ == "__main__":
    import main
    main.main()
