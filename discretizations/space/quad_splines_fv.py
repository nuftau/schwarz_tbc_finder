"""
    Intermediary class, used to describe finite volumes by quadratic splines reconstruction.   
    Right now we will only use this class for the analysis but maybe it could be used for
    the integration.
"""

import numpy as np
from utils_linalg import solve_linear
from discretizations.discretization import Discretization

class QuadSplinesFV(Discretization):

    def __init__(self, *args, **kwargs):
        """
            give default values of all variables.
        """
        super().__init__(*args, **kwargs)

    #####################
    # INTEGRATION FUNCTIONS:
    #####################
    # In this scheme we consider the main variable to be phi
    # and the additional to be \\Bar{u}^{n}.
    # if the scheme is used with a forcing term, don't forget to pass
    # f_{m+1/2} - f_{m-1/2}, with f_{m+1/2} the average of the forcing
    # between x_m and x_{m+1}, except at the boundaries.
    # Finally, f should be given as:
    # f = np.concatenate(([f[0]], np.diff(f), [f[-1]]))
    def A_interior(self, upper_domain):
        """
            gives A, such as inside the domain, A \\partial_t u = Bu
            For finite differences, A is identity.
        """
        M, h, D, _ = self.M_h_D_Lambda(upper_domain=upper_domain)
        diag = (h[:-1]/D[1:-1] + h[1:]/D[1:-1])/3
        lower_diag = h[:-1]/D[:-2]/6
        upper_diag = h[1:]/D[2:]/6
        return lower_diag, diag, upper_diag

    def B_interior(self, upper_domain):
        """
            gives f, such as inside the domain, A \\partial_t u = Bu
            This function supposes there is no forcing. this forcing should be added
            in the time integration.
            For finite differences, A is identity.
        """
        a, c, _ = self.get_a_c_dt()
        M, h, D, _ = self.M_h_D_Lambda(upper_domain=upper_domain)
        #left diagonal: applies to u[:-2]
        Y_0 = - (1/h[:-1] + a / (2*D[2:])) + c * h[:-1] / D[:-2] /6
        # diagonal: applies to u[1:-1]
        Y_1 = 1/h[:-1] + 1/h[1:] + c * (h[1:] + h[:-1]) / D[1:-1] /3
        # right diagonal: applies to u[2:]
        Y_2 = - (1/h[1:] - a / (2*D[:-2])) + c * h[1:] / D[2:] /6
        Y_0, Y_1, Y_2 = -Y_0, -Y_1, -Y_2 # Bu is at the rhs of the equation
        return (Y_0, Y_1, Y_2)

    def discretization_bd_cond(self, upper_domain):
        """
        Gives the coefficients in front of u to compute the bd condition,
        either at the top of the atmosphere (Dirichlet)
        or at the bottom of the Ocean (Neumann)
        """
        # starting from index -1
        if not upper_domain: # Neumann :
            M, h, D, _ = self.M_h_D_Lambda(upper_domain=upper_domain)
            return [1/D[-1]]
        else: # Dirichlet :
            M, h, D, _ = self.M_h_D_Lambda(upper_domain=upper_domain)
            return None

    def hardcoded_bd_cond(self, upper_domain, bd_cond, coef_implicit, coef_explicit, dt, f, sol_for_explicit, additional, override_r=None, **kwargs):
        """
            For schemes that use corrective terms or any mechanism of time derivative inside bd cond,
            this method allows the time scheme to correct the boundary condition.
            in this case, sol_for_explicit will be \\phi (in n-1/2 or n-1)
            and additional will be \\Bar(u) (in n-1)
            f is the right hand side of the PDE.
            the part of time scheme is represented by doing the integration
            (u^{n+1} - u^n)/dt = coef_implicit * dx^2 u^{n+1} + coef_explicit * dx^2 u^n
            don't forget to interpolate f in time before calling function
        """
        if not upper_domain: # Neumann :
            M, h, D, _ = self.M_h_D_Lambda(upper_domain=upper_domain)
            return ([1/D[-1]], bd_cond)
        else: # Dirichlet :
            M, h, D, _ = self.M_h_D_Lambda(upper_domain=upper_domain)
            a, c, _ = self.get_a_c_dt()

            if override_r is not None:
                c = override_r

            assert h[-1] > 0
            assert sol_for_explicit is not None
            assert additional is not None
            phi_m_phi = np.array([(1/h[-1] - a/(2*D[-1])), (-1/h[-1] - a/(2*D[-2]))])
            coeffs_phi = dt/(1+dt*c*coef_implicit) * phi_m_phi
            return (np.array([h[-1]/(3*D[-1]), h[-1]/(6*D[-2])]) + coef_implicit * coeffs_phi,
                    bd_cond - dt/(1+dt*c*coef_implicit) * (additional[-1]*(1/dt - c*coef_explicit) + f[-1])
                    - coef_explicit * np.dot(coeffs_phi, sol_for_explicit[-1:-3:-1]))

    def hardcoded_interface(self, upper_domain, robin_cond, coef_implicit, coef_explicit, dt, f, sol_for_explicit, additional, override_r=None, **kwargs):
        """
            For schemes that use corrective terms or any mechanism of time derivative inside interface condition,
            this method allows the time scheme to correct the boundary condition.
            in this case, sol_for_explicit will be \\phi and additional will be \\Bar(u) (both in n-1)
            f is the right hand side of the PDE.
            the part of time scheme is represented by doing the integration
            (u^{n+1} - u^n)/dt = coef_implicit * dx^2 u^{n+1} + coef_explicit * dx^2 u^n
            don't forget to interpolate f in time before calling function
        """
        M, h, D, Lambda = self.M_h_D_Lambda(upper_domain=upper_domain)
        a, c, _ = self.get_a_c_dt()
        if override_r is not None:
            c = override_r

        phi_m_phi = np.array([(- 1/h[0] - a/(2*D[0])), (1/h[0] - a/(2*D[1]))])
        coeffs_phi = dt/(1+dt*c*coef_implicit) * phi_m_phi
        return (np.array([1, 0]) + Lambda * (\
                np.array([-h[0]/(3*D[0]), -h[0]/(6*D[1])]) + coef_implicit * coeffs_phi),
                robin_cond - Lambda * ( dt/(1+dt*c*coef_implicit) * (additional[0]*(1/dt - c*coef_explicit) + f[0])
                    + coef_explicit * np.dot(coeffs_phi, sol_for_explicit[:2]))) # This last line seems better with a - but the formulaes give +

    def discretization_interface(self, upper_domain):
        return None

    def create_additional(self, upper_domain): # average of u on a cell
        M, h, D, Lambda = self.M_h_D_Lambda(upper_domain=upper_domain)
        return np.zeros(M)

    def update_additional(self, result, additional, dt, f, upper_domain,
            reaction_explicit, coef_reaction_implicit):
        # starting from additional=\\Bar{u}^n, making additional=\\Bar{u}^{n+1}
        # average of u on a cell. Warning, you need to interpolate result for making
        # an implicit/explicit thing
        a, c, _ = self.get_a_c_dt()
        M, h, D, Lambda = self.M_h_D_Lambda(upper_domain=upper_domain)
        return dt / (1 + dt * c * coef_reaction_implicit) * \
                (additional/dt + np.diff(result) / h - a * (result[1:] + result[:-1]) / 2 \
                - c * reaction_explicit + np.cumsum(f[:-1]))

    def new_additional(self, result, upper_domain, cond):
        if upper_domain: # cond is a Dirichlet condition
            _, h2 = self.get_h()
            _, D = self.get_D()
            rhs = h2[1:]*result[2:]/(6*D[2:]) + \
                    2*(h2[1:] + h2[:-1])*result[1:-1]/(6*D[1:-1]) + \
                    h2[:-1]*result[:-2]/(6*D[:-2])
            u_bar_size = h2.shape[0]
            upper_diag = np.ones(u_bar_size-1)
            diag = np.concatenate((-np.ones(u_bar_size-1), [1]))
            rhs = np.concatenate((rhs, [cond - result[-1]*h2[-1]/(3*D[-1]) - result[-2] * h2[-1]/(6*D[-2])]))
            import scipy.linalg
            return scipy.linalg.solve_banded(l_and_u=(0,1),
                    ab=np.vstack((np.concatenate(([0], upper_diag)), diag)),
                    b=rhs)
        else: # cond is the Robin condition
            h1, _ = self.get_h()
            D, _ = self.get_D()
            Lambda = self.LAMBDA_1
            assert Lambda != 0.
            rhs = h1[1:]*result[2:]/(6*D[2:]) + \
                    2*(h1[1:] + h1[:-1])*result[1:-1]/(6*D[1:-1]) + \
                    h1[:-1]*result[:-2]/(6*D[:-2])

            u_bar_size = h1.shape[0]
            lower_diag = -np.ones(u_bar_size-1)
            diag = np.ones(u_bar_size)

            diag[0] *= Lambda
            rhs = np.concatenate(([cond - result[0] + Lambda*(result[0]*h1[0]/(3*D[0]) + result[1] * h1[0]/(6*D[1]))], rhs))
            import scipy.linalg
            return scipy.linalg.solve_banded(l_and_u=(1,0),
                    ab=np.vstack((diag, np.concatenate((lower_diag, [0])))),
                    b=rhs)


    def projection_result(self, result, upper_domain, additional, **kwargs):
        """
            given the result of the inversion, returns (u_np1, u_interface, phi_interface)
        """
        M, h, D, Lambda = self.M_h_D_Lambda(upper_domain=upper_domain)
        u = additional[0] - result[0] * h[0]/(3*D[0]) - result[1] * h[0]/(6*D[1])
        return result, u, result[0], additional

    def size_f(self, upper_domain):
        M, h, D, Lambda = self.M_h_D_Lambda(upper_domain=upper_domain)
        return M+1 # f is theorically of size M, but we may need a little more
        #because of the time scheme ?

    def size_prognostic(self, upper_domain):
        M, h, D, Lambda = self.M_h_D_Lambda(upper_domain=upper_domain)
        return M+1

    def reconstruction_spline(self, phi, u_bar, upper_domain, x): # for a single x !
        if upper_domain:
            _, h = self.get_h()
            D = self.D2
            x_1_2 = np.cumsum(np.concatenate(([0], h)))

            # First : find WHERE IS X
            from bisect import bisect_right
            index = bisect_right(x_1_2, x) - 1

            if index >= x_1_2.shape[0]:
                index = x_1_2.shape[0] - 2
            assert x >= x_1_2[index]
            assert x <= x_1_2[index+1]

            # useful variables:
            xi = x - (x_1_2[index+1] + x_1_2[index])/2
            h = x_1_2[index+1] - x_1_2[index]

            d_mp1 = phi[index+1] / D
            d_m = phi[index] / D
            u_bar_m = u_bar[index]
            # returning result
            return u_bar_m + xi*(d_mp1 + d_m)/2 + (xi**2 - h**2/12)*(d_mp1-d_m)/(2*h)
        else:
            # First : find WHERE IS X
            h, _ = self.get_h()
            D = self.D1

            x_1_2 = np.cumsum(np.concatenate(([0], h)))

            # First : find WHERE IS X
            from bisect import bisect_right
            index = bisect_right(-x_1_2, -x)

            if index >= x_1_2.shape[0]-1:
                index = x_1_2.shape[0] - 1
            assert x >= x_1_2[index]
            assert x <= x_1_2[index-1]

            # useful variables:
            xi = x - (x_1_2[index-1] + x_1_2[index])/2
            h = x_1_2[index-1] - x_1_2[index] 

            d_mp1 = phi[index] / D
            d_m = phi[index-1] / D
            u_bar_m = u_bar[index-1]
            # returning result
            return u_bar_m + xi*(d_mp1 + d_m)/2 + (xi**2 - h**2/12)*(d_m-d_mp1)/(2*h)

    #####################
    # ANALYSIS FUNCTIONS:
    #####################

    def lambda_1_2_pm(self, s):
        # The convention here is: \\lambda_- is the main root,
        # and \\lambda_+ is the secondary root.
        """
            Gives the \\lambda_\\pm:
            returns \\lambda_{-, j=1}, \\lambda_{-, j=2}, \\lambda_{+, j=1}, \\lambda_{+, j=2}.
        """
        assert s is not None
        M, h, D, Lambda = self.M_h_D_Lambda(upper_domain=False)
        a, c, _ = self.get_a_c_dt()
        h, D = h[0], D[0]
        Y_0 = -1 / (s + c) * (1 / h + a / (2 * D)) + h / (6 * D)
        Y_1 = 1 / (s + c) * 2 / h + 2 * h / (3 * D)
        Y_2 = -1 / (s + c) * (1 / h - a / (2 * D)) + h / (6 * D)

        lam1_m = (Y_1 - np.sqrt(Y_1**2 - 4 * Y_0 * Y_2)) \
                                / (-2 * Y_2)
        lam1_p = (Y_1 + np.sqrt(Y_1**2 - 4 * Y_0 * Y_2)) \
                                / (-2 * Y_2)

        M, h, D, Lambda = self.M_h_D_Lambda(upper_domain=True)
        h, D = h[0], D[0]
        Y_0 = -1 / (s + c) * (1 / h + a / (2 * D)) + h / (6 * D)
        Y_1 = 1 / (s + c) * 2 / h + 2 * h / (3 * D)
        Y_2 = -1 / (s + c) * (1 / h - a / (2 * D)) + h / (6 * D)

        lam2_m = (Y_1 - np.sqrt(Y_1**2 - 4 * Y_0 * Y_2)) \
                                / (-2 * Y_2)
        lam2_p = (Y_1 + np.sqrt(Y_1**2 - 4 * Y_0 * Y_2)) \
                                / (-2 * Y_2)

        return lam1_m, lam2_m, lam1_p, lam2_p

    def eta_dirneu(self, j, lam_m, lam_p, s=None):
        """
            Gives the \\eta of the discretization:
            can be:
                -eta(1, ..);
                -eta(2, ..);
            returns tuple (etaj_dir, etaj_neu).
        """
        assert j == 1 or j == 2 and s is not None
        M, h, D, Lambda = self.M_h_D_Lambda(upper_domain=(j==2))
        a, c, _ = self.get_a_c_dt()
        h, D = h[0], D[0]

        lambda_moins = lam_m
        lambda_plus = lam_p

        # The computation is then different because the boundary condition is different (and we are in the finite domain case)
        if j == 1:
            lambda_moins, lambda_plus = lambda_plus, lambda_moins # we invert the l- and l+ to have |l-|<1
            # We added a minus in front of h/6D ?
            xi = (-h/(6*D) * (s+c) + 1/h + a/(2*D)) / (h/(3*D) * (s+c) + 1/h - a/(2*D))
            eta1_dir = (-(1/h + a/(2*D))/(s+c) - h/(3*D)) \
                    * (1 - (lambda_moins - xi) / (lambda_plus - xi) * (lambda_moins / lambda_plus)**(M-1)) \
                    + ((1/h - a/(2*D))/(s+c) - h/(6*D)) \
                    * (lambda_moins - lambda_plus* (lambda_moins - xi) / (lambda_plus - xi) *(lambda_moins / lambda_plus)**M)
            eta1_neu = 1 + (lambda_moins-xi) / (lambda_plus - xi) *(lambda_moins / lambda_plus) ** (M - 1)
            return eta1_dir, eta1_neu
        elif j == 2:
            eta2_dir = (-(1/h + a/(2*D))/(s+c) - h/(3*D)) \
                    * (1 - (lambda_moins / lambda_plus)**M) \
                    + ((1/h - a/(2*D))/(s+c) - h/(6*D)) \
                    * (lambda_moins - lambda_plus*(lambda_moins / lambda_plus)**M)
            eta2_neu = 1 + (lambda_moins / lambda_plus) ** M
            return eta2_dir, eta2_neu


    def sigma_modified(self, w, s, order_equations):
        h1, h2 = self.get_h()
        h1, h2 = h1[0], h2[0]
        D1, D2 = self.D1, self.D2

        s1 = np.copy(s)
        if order_equations > 0:
            s1 += (s + self.C)**2 * (h1**2/(12*D1))
        if order_equations > 1:
            s1 += (s + self.C)**3 * h1**4/(90*D1**2)

        s2 = np.copy(s)
        if order_equations > 0:
            s2 += (s + self.C)**2 * (h2**2/(12*D2))
        if order_equations > 1:
            s2 += (s + self.C)**3 * h2**4/(90*D2**2)

        sig1 = np.sqrt((s1+self.C)/self.D1)
        sig2 = -np.sqrt((s2+self.C)/self.D2)
        return sig1, sig2

    def eta_dirneu_modif(self, j, sigj, order_operators, w, *kwargs, **dicargs):
        h1, h2 = self.get_h()
        h1, h2 = h1[0], h2[0]
        D1, D2 = self.D1, self.D2
        dt = self.DT
        if j==1:
            hj = h1
            Dj = D1
        else:
            hj = h2
            Dj = D2
        eta_neu_modif = Dj
        eta_dir_modif = 1/sigj
        if order_operators >= 1:
            eta_dir_modif += (1j*w+self.C)*hj**2/(12*Dj) / sigj
        if order_operators > 1:
            eta_dir_modif += hj**3*sigj**2/24 
        if order_operators >= 2:
            eta_dir_modif += - 7*hj**4*sigj**3/360- dt**2/2*w**2/(sigj)
        return eta_dir_modif, eta_neu_modif

    """
        Simple function to return h in each subdomains,
        in the framework of finite differences.
        returns uniform spaces between points (h1, h2).
        To recover xi, use:
        xi_1_2 = np.cumsum(np.concatenate(([0], hi)))
    """

    def get_h(self, size_domain_1=None, size_domain_2=None, M1=None, M2=None):
        size_domain_1 = self.SIZE_DOMAIN_1
        size_domain_2 = self.SIZE_DOMAIN_2
        M1 = self.M1
        M2 = self.M2
        h1 = -size_domain_1 / M1 + np.zeros(M1)
        h2 = size_domain_2 / M2 + np.zeros(M2)
        return h1, h2

    """
        Simple function to return D in each subdomains,
        in the framework of finite differences.
        provide continuous functions accepting ndarray
        for D1 and D2, and returns the right coefficients.
    """

    def get_D(self, h1=None, h2=None, function_D1=None, function_D2=None):
        if h1 is None or h2 is None:
            h1, h2 = self.get_h()
        if function_D1 is None:
            def function_D1(x): return self.D1 + np.zeros_like(x)
        if function_D2 is None:
            def function_D2(x): return self.D2 + np.zeros_like(x)
        # coordinates at half-points:
        x1_1_2 = np.cumsum(np.concatenate(([0], h1)))
        x2_1_2 = np.cumsum(np.concatenate(([0], h2)))
        D1 = function_D1(x1_1_2)
        D2 = function_D2(x2_1_2)
        return D1, D2

    def name(self):
        return "Volumes finis (splines quadratiques)"

    def repr(self):
        return "finite volumes (spl2)"

