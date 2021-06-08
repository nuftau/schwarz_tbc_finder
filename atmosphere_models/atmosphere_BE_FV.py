import numpy as np
from scipy.linalg import solve_banded

class AtmosphereBEFV():
    def __init__(self, r, # reaction coefficient
                 nu, # Diffusivity
                 M, # Number of collocation points
                 SIZE_DOMAIN, # Size of \\Omega_1
                 LAMBDA, # Robin parameter
                 DT): # Time step
        """
            The data needed is passed through this constructor.
            The space step is SIZE_DOMAIN / (M-1)
            there is M-1 points for u, M points for phi
        """
        self.r, self.nu, self.M, self.size_domain, self.Lambda, self.dt = \
            r, nu, M, SIZE_DOMAIN, LAMBDA, DT
        self.h = SIZE_DOMAIN / (M - 1)

    def size_u(self):
        return self.M- 1

    def interface_values(self, prognosed, diagnosed, overlap):
        u_interface = diagnosed[overlap] - self.h / 3 * prognosed[overlap] - self.h / 6 * prognosed[overlap+1]
        phi_interface = prognosed[overlap]
        return u_interface, phi_interface

    def integrate_large_window(self, interface,
            initial_prognostic=None, initial_diagnostic=None,
            forcing=None, boundary=None): 
        """
            Given the information, returns the interface information after integration in time.

            Parameters:
            interface: Robin condition given to the model, array of size N+1
                (N being the number of time steps, the first value can be generally set to 0)
            The following parameters are set to 0 if not prescribed:
                initial_prognostic (prognosed variable, space derivative of the solution), (size M)
                initial_diagnostic (diagnosed average solution), (size M-1)
                forcing: function [0,T] -> C^M used as forcing in each volume
                boundary: array of size N+1

            Returns:
            Tuple solution, derivative where solution and derivative are (N+1) 1D arrays

            scheme is:
                -Noting Y = 1+delta_x^2/6, b=1+1/sqrt(2), a=1+sqrt(2)
                -Noting R = r*dt, Gamma = nu*dt/h^2

                    (Y + (R Y - Gamma delta_x^2))phi_np1 = Y phi_n
                See pdf for the implementation.
        """
        # global initialisation, defining matrices and variables
        initial_prognostic = np.zeros(self.M) if initial_prognostic is None else initial_prognostic
        initial_diagnostic = np.zeros(self.M-1) if initial_diagnostic is None else initial_diagnostic
        forcing = (lambda _: np.zeros(self.M)) if forcing is None else forcing
        boundary = np.zeros_like(interface) if boundary is None else boundary
        Gamma = self.nu * self.dt / self.h**2
        R = self.r * self.dt
        h, dt, nu = self.h, self.dt, self.nu
        tilde_p = -self.Lambda

        Y_FV = 1/6*np.vstack((np.concatenate(([1e100, tilde_p], np.ones(self.M-2))),#up_diag
            np.concatenate(([2*tilde_p + 6*nu/h], 4*np.ones(self.M-2), [2])), # diag
            np.concatenate((np.ones(self.M-1), [1e100]))))# low_diag
        D_FV = np.vstack((np.concatenate(([1e100,tilde_p], np.ones(self.M-2))),#up_diag
            np.concatenate(([-tilde_p], -2*np.ones(self.M-2), [-1])), # diag
            np.concatenate((np.ones(self.M-1), [1e100]))))# low_diag
        def prod_banded(tridiag_mat, x):
            ret = tridiag_mat[1]*x
            ret[:-1] += tridiag_mat[0,1:]*x[1:]
            ret[1:] += tridiag_mat[2,:-1]*x[:-1]
            return ret
        matrix_to_inverse = (1+R)*Y_FV - Gamma*D_FV

        # initialisation of the main loop of integration
        u_current = initial_diagnostic
        phi_current = initial_prognostic
        solution = [initial_diagnostic[0] \
                - h / 3 * initial_prognostic[0] - h / 6 * initial_prognostic[0]]
        derivative = [initial_prognostic[0]]

        # actual integration:
        for n in range(interface.shape[0]-1):
            f_np1 = forcing((n+1)*dt)
            rhs_c = np.concatenate((
                [1/h*((1+R)*interface[n+1] - interface[n] - dt*self.Lambda*f_np1[0])],
                            +dt*np.diff(f_np1)/h,
                            [1/h*((1+R)*boundary[n+1] - boundary[n] - dt*f_np1[-1])]))
            rhs_step = prod_banded(Y_FV, phi_current) + rhs_c
            phi_next = solve_banded(l_and_u=(1, 1), ab=matrix_to_inverse, b=rhs_step)

            u_next = (u_current + (h*Gamma*np.diff(phi_next) + dt*f_np1)) / (1 + R)

            solution += u_next[0] - h / 3 * phi_next[0] - h / 6 * phi_next[0]
            derivative += [phi_next[0]]
            
            # preparing next integration
            phi_current = phi_next
            u_current = u_next

        return solution, derivative

    def integrate_in_time(self, prognosed, diagnosed, interface_robin, forcing, boundary):
        """
            Given the information, returns the tuple (phi_(n+1), u_(n+1)).

            Parameters:
            phi_n (prognostic variable, space derivative of solution), (size M)
            u_n (average of solution on each volume), (size M-1)
            interface_robin, forcing, boundary: tuples for time (tn, t*, t{n+1})
            time t* is not used.

            forcing: the forcing in the diffusion-reaction equation, averaged on each volume
            boundary conditions :
                -Dirichlet(t)=boundary(t) at the top of atmosphere
                -Robin(t)=interface_robin(t) at interface

            scheme is:
                -Noting Y = 1+delta_x^2/6, b=1+1/sqrt(2), a=1+sqrt(2)
                -Noting R = r*dt, C = nu*dt/h^2

                    (Y + (R Y - C delta_x^2))phi_np1 = Y phi_n
        """
        
        phi_n = prognosed
        u_n = diagnosed
        Gamma = self.nu * self.dt / self.h**2
        R = self.r * self.dt
        h, dt, nu = self.h, self.dt, self.nu
        tilde_p = -self.Lambda
        f_n, _, f_np1 = forcing
        robin_n, _, robin_np1 = interface_robin
        bd_n, _, bd_np1 = boundary

        def prod_banded(tridiag_mat, x):
            ret = tridiag_mat[1]*x
            ret[:-1] += tridiag_mat[0,1:]*x[1:]
            ret[1:] += tridiag_mat[2,:-1]*x[:-1]
            return ret

        rhs_c = np.concatenate((
            [1/h*((1+R)*robin_np1 - robin_n - dt*self.Lambda*f_np1[0])],
                        +dt*np.diff(f_np1)/h,
                        [1/h*((1+R)*bd_np1 - bd_n - dt*f_np1[-1])]))

        Y_FV = 1/6*np.vstack((np.concatenate(([1e100, tilde_p], np.ones(self.M-2))),#up_diag
            np.concatenate(([2*tilde_p + 6*nu/h], 4*np.ones(self.M-2), [2])), # diag
            np.concatenate((np.ones(self.M-1), [1e100]))))# low_diag
        D_FV = np.vstack((np.concatenate(([1e100,tilde_p], np.ones(self.M-2))),#up_diag
            np.concatenate(([-tilde_p], -2*np.ones(self.M-2), [-1])), # diag
            np.concatenate((np.ones(self.M-1), [1e100]))))# low_diag
        matrix_to_inverse = (1+R)*Y_FV - Gamma*D_FV

        rhs_step = prod_banded(Y_FV, phi_n) + rhs_c

        phi_np1 = solve_banded(l_and_u=(1, 1), ab=matrix_to_inverse, b=rhs_step)

        u_np1 = (u_n + (h*Gamma*np.diff(phi_np1) + dt*f_np1)) / (1 + R)

        return phi_np1, u_np1

    """
        __eq__ and __hash__ are implemented, so that a discretization
        can be stored as key in a dict
        (it is useful for memoisation)
    """

    def repr(self):
        return "AtmBEFV"

    def __eq__(self, other):
        return self.__dict__ == other.__dict__ and self.repr() == other.repr()

    def __hash__(self):
        return hash(repr(sorted(self.__dict__.items())) + self.repr())

    def __repr__(self):
        return repr(sorted(self.__dict__.items())) + self.repr()
