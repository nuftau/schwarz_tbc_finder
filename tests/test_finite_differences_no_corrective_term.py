import numpy as np
from numpy import cos, sin
from numpy.random import random
from discretizations.finite_difference_no_corrective_term \
        import FiniteDifferencesNoCorrectiveTerm
fdifference = FiniteDifferencesNoCorrectiveTerm()
integrate_one_step = fdifference.integrate_one_step
integrate_one_step_star = fdifference.integrate_one_step_star


def launch_all_tests():
    print("Test integration finite differences without corrective term:", time_test_star())
    print("Test complete finite differences without corrective term:", complete_test_schwarz())
    return "ok"


def complete_test_schwarz():
    from tests.test_schwarz import schwarz_convergence
    ecart = schwarz_convergence(fdifference)
    assert ecart[-1] < 5e-3
    return "ok"


def time_test_star():
    # Our domain is [-1,1]
    # we define u as u(x, t) = sin(dx) + Tt in \Omega_1,
    # u(x, t) = D1 / D2 * sin(dx) + Tt      in \Omega_2

    a = 1.2
    c = 0.3

    T = 5.
    d = 8.
    t = 3.
    dt = 0.05
    M1, M2 = 3000, 3000

    x1 = -np.linspace(0, 1, M1)**1
    x2 = np.linspace(0, 1, M2)**1

    h1 = np.diff(x1)
    h2 = np.diff(x2)

    h = np.concatenate((-h1[::-1], h2))

    # coordinates at half-points:
    x1_1_2 = x1[:-1] + h1 / 2
    x2_1_2 = x2[:-1] + h2 / 2
    x_1_2 = np.concatenate((np.flipud(x1_1_2), x2_1_2))

    x = np.concatenate((np.flipud(x1[:-1]), x2))

    D1 = 1.2 + x1_1_2**2
    D2 = 2.2 + x2_1_2**2

    D1_x = 1.2 + x1**2
    D2_x = 2.2 + x2**2
    D1_prime = 2 * x1
    D2_prime = 2 * x2

    ratio_D = D1_x[0] / D2_x[0]

    t_n, t = t, t + dt
    neumann = ratio_D * d * cos(d * x2_1_2[-1])
    dirichlet = sin(d * x1[-1]) + T * t

    # Note: f is a local approximation !
    f2 = T * (1 + c * t) + ratio_D * (d * a * cos(d * x2) + c *
                                      sin(d * x2) + D2_x * d * d * sin(d * x2) - D2_prime * d * cos(d * x2))

    f1 = T * (1 + c * t) + d * a * cos(d * x1) + c * sin(d * x1) \
        + D1_x * d * d * sin(d * x1) - D1_prime * d * cos(d * x1)

    u0 = np.concatenate(
        (sin(d * x1[-1:0:-1]) + T * t_n, ratio_D * sin(d * x2) + T * t_n))
    u1 = np.concatenate(
        (sin(d * x1[-1:0:-1]) + T * t, ratio_D * sin(d * x2) + T * t))

    D1 = np.concatenate(([D1_x[0]], D1[:-1]))
    D2 = np.concatenate(([D2_x[0]], D2[:-1]))

    u_np1, real_u_interface, real_phi_interface = integrate_one_step_star(M1=M1,
                                                                          M2=M2, h1=h1, h2=h2, D1=D1,
                                                                          D2=D2, a=a, c=c, dt=dt, f1=f1, f2=f2,
                                                                          neumann=neumann, dirichlet=dirichlet, u_nm1=u0)
    """
    import matplotlib.pyplot as plt
    plt.plot(x, u0, "b")
    plt.plot(x, u_np1, "r")
    plt.plot(x, u1, "k--")
    plt.show()
    """
    assert np.linalg.norm(u1 - u_np1) < 1e-2

    return "ok"
