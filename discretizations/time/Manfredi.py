"""
    Finite volume for diffusion advection reaction equation.
    The functions to use are integrate_one_step and integrate_one_step_star.
    Theses function make a single step in time. It is not efficient
    (need to compute the matrix each time) but it is simple.
"""

import numpy as np
from utils_linalg import solve_linear
from discretizations.discretization import Discretization
from utils_linalg import solve_linear
from utils_linalg import scal_multiply
from utils_linalg import multiply_interior
from utils_linalg import multiply
from utils_linalg import add_banded


class Manfredi(Discretization):

    def __init__(self, *args, **kwargs):
        """
            give default values of all variables.
        """
        pass

    def integrate_one_step(self, f, bd_cond, u_nm1, u_interface,
            phi_interface, upper_domain=True, Y=None, additional=[], **kwargs):

        alpha = 1. + np.sqrt(2)
        beta = 1. + 1/np.sqrt(2)

        bma = beta - alpha # beta - alpha = -1/sqrt(2)

        u_star_interface = u_interface(bma)
        phi_star_interface = phi_interface(bma)
        u_star_interface = u_interface(bma)
        f_star = f(1+np.sqrt(2))
        bd_cond_star = bd_cond(bma)

        f_nm1 = f(0)
        f_nm1_2 = f(1/2)
        f = f(1)
        bd_cond_nm1 = bd_cond(0)
        bd_cond = bd_cond(1)
        u_nm1_interface = u_interface(0)
        u_interface = u_interface(1)
        phi_nm1_interface = phi_interface(0)
        phi_interface = phi_interface(1)

        if len(additional) == 0:
            additional = self.create_additional(upper_domain=upper_domain)
        else:
            additional = additional[0]
        
        assert upper_domain is True or upper_domain is False

        M, h, D, Lambda = self.M_h_D_Lambda(upper_domain=upper_domain)

        # L'idée c'est qu'en semi-discret en espace, on a: A\partial_t u = B u
        reaction = self.C
        self.C = 0
        A = self.A_interior(upper_domain=upper_domain) # without reaction
        B = self.B_interior(upper_domain=upper_domain) # without reaction

        ###################
        # FIRST STEP : find the time derivative at star time
        # The equation is A(u*-u_nm1)/dt - (beta*Bu* - alpha*Bu_nm1) + reaction*Au_nm1 = f(1/2)
        ###################
        to_inverse = add_banded(scal_multiply(A, 1./self.DT), scal_multiply(B, -beta))
        rhs = multiply_interior(A, u_nm1) * (1 / self.DT - reaction) \
                - alpha * multiply_interior(B, u_nm1) + f_nm1_2[1:-1]

        cond_robin_star = Lambda * u_star_interface + phi_star_interface

        # instead of giving additional = \Bar{u}, we give \Bar{u} * (1-c*DT). Since our problem comes
        # From Finite volumes, we can thus solve only for finite volumes.
        Y, rhs = self.add_boundaries(to_inverse=to_inverse, rhs=rhs, interface_cond=cond_robin_star,
                                     coef_explicit=-alpha, coef_implicit=beta,
                                     dt=self.DT, f=f_nm1_2, sol_for_explicit=u_nm1, sol_unm1=u_nm1,
                                     bd_cond=bd_cond_star, upper_domain=upper_domain,
                                     additional=None if additional is None else additional * (1-reaction*self.DT))
        result_star = solve_linear(Y, rhs)

        self.C = reaction

        additional_star = self.update_additional(result=-alpha*u_nm1 + beta*result_star,
                additional=additional, dt=self.DT,
                upper_domain=upper_domain, f=f_nm1_2,
                reaction_explicit=None if additional is None else additional,
                coef_reaction_implicit=0)

        ###################
        # SECOND STEP : We need to inverse the same tridiagonal matrix, except the boundaries
        # The equation is (u_np1-u*)/dt - beta*Bu_np1 = 0, WITHOUT REACTION AND FORCING TERM
        ###################
        # keeping the same matrix to inverse
        # to_inverse = add_banded(scal_multiply(A, 1/self.DT), scal_multiply(B, -beta))
        # This time the rhs does not take into account the forcing term
        rhs = multiply_interior(A, result_star) / self.DT

        cond_robin = Lambda * u_interface + phi_interface
    
        self.C = 0 # We need to avoid reaction and forcing term in the second step
        Y, rhs = self.add_boundaries(to_inverse=to_inverse, rhs=rhs, interface_cond=cond_robin,
                                     coef_explicit=0., coef_implicit=1.,
                                     dt=beta*self.DT, f=np.zeros_like(f), sol_for_explicit=result_star,
                                     sol_unm1=result_star,
                                     bd_cond=bd_cond, upper_domain=upper_domain,
                                     additional=additional_star)
        result = solve_linear(Y, rhs)

        additional = self.update_additional(result=result, additional=additional_star, dt=beta*self.DT,
                upper_domain=upper_domain, f=np.zeros_like(f), reaction_explicit=0, coef_reaction_implicit=0) # Now additional is in time n

        self.C = reaction # set back reaction coefficient
        partial_t_result0 = (result[0] - u_nm1[0])/self.DT
        return self.projection_result(result=result, upper_domain=upper_domain,
                additional=additional, partial_t_result0=partial_t_result0, f=f, result_explicit=result)

    # s_time_discrete is not a variable but an operator for Manfredi scheme
    def s_time_modif(self, w, order):
        s = w * 1j
        if order > 1:
            s -= 4+3*np.sqrt(2)* w**3 * self.DT**2/6 * 1j
        return s
