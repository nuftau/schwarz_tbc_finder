"""
This module defines several universal functions:
    all functions of this module should return tuples of functions
    (phi_m, phi_h, psi_m, psi_h, Psi_m, Psi_h)
    (See Nishizawa and Kitamura, 2018)
    phi_m, phi_h are the universal functions.
    psi_m, psi_h are their integral form.
    Psi_m, Psi_h are the primitive of psi_m, psi_h.
"""
import numpy as np

def Large_et_al_2019():
    def phi_m(zeta):
        Cm = np.cbrt(1-14*zeta)
        return 5*zeta + 1 if zeta >= 0 else 1/Cm
    def phi_h(zeta): # warning: there is a duplicate of this function
        Ch = np.cbrt(1-25*zeta) # in shortwave_absorption.py
        return 5*zeta + 1 if zeta >= 0 else 1/Ch
    def psi_m(zeta):
        Cm = np.cbrt(1-14*zeta)
        sq3 = np.sqrt(3)
        return -5*zeta if zeta >=0 else sq3 * np.arctan(sq3) - \
                sq3 * np.arctan(sq3/3*(2*Cm+1)) + 1.5 * \
                np.log((Cm**2 + Cm + 1)/3)
    def psi_h(zeta):
        sq3 = np.sqrt(3)
        Ch = np.cbrt(1-25*zeta)
        return -5*zeta if zeta >=0 else sq3 * np.arctan(sq3) - \
                sq3 * np.arctan(sq3/3*(2*Ch+1)) + 1.5 * \
                np.log((Ch**2 + Ch + 1)/3)
    def Psi_m(zeta):
        Cm = np.cbrt(1-14*zeta)
        sq3 = np.sqrt(3)
        return -5*zeta/2 if zeta >=0 else sq3 * np.arctan(sq3) - \
                sq3 * np.arctan(sq3/3*(2*Cm+1)) + 1.5 * \
                np.log((Cm**2 + Cm + 1)/3) - (2*Cm+1)*(Cm-1) / \
                2/(Cm**2 + Cm + 1)
    def Psi_h(zeta):
        sq3 = np.sqrt(3)
        Ch = np.cbrt(1-25*zeta)
        return -5*zeta/2 if zeta >=0 else sq3 * np.arctan(sq3) - \
                sq3 * np.arctan(sq3/3*(2*Ch+1)) + 1.5 * \
                np.log((Ch**2 + Ch + 1)/3) - (2*Ch+1)*(Ch-1) / \
                2/(Ch**2 + Ch + 1)

    return (np.vectorize(phi_m, otypes=[float]),
            np.vectorize(phi_h, otypes=[float]),
            np.vectorize(psi_m, otypes=[float]),
            np.vectorize(psi_h, otypes=[float]),
            np.vectorize(Psi_m, otypes=[float]),
            np.vectorize(Psi_h, otypes=[float]))

def Businger_et_al_1971():
    fm = lambda zeta : (1-15*zeta)**(1/4)
    fh = lambda zeta : (1-9*zeta)**(1/2)
    # a = 4.7
    # Pr = 0.74
    a = 4.8
    Pr = 4.8/7.8
    def phi_m(zeta):
        return a*zeta + 1 if zeta >= 0 else 1/fm(zeta)
    def phi_h(zeta):
        return a*zeta/Pr + 1 if zeta >= 0 else 1/fh(zeta)
    def psi_m(zeta):
        return -a*zeta if zeta >= 0 else \
                np.log((1+fm(zeta))**2*(1+fm(zeta)**2)/8) - \
                2*np.arctan(fm(zeta)) + np.pi/2
    def psi_h(zeta):
        return -a*zeta/Pr if zeta >= 0 else 2*np.log((1+fh(zeta))/2)
    def Psi_m(zeta):
        if abs(zeta) < 1e-6: # using asymptotics of Nishizawa Kitamura (2018)
            return -a*zeta/2 if zeta >= 0 else -15*zeta/8
        else:
            return -a*zeta/2 if zeta >= 0 else \
                    np.log((1+fm(zeta))**2*(1+fm(zeta)**2)/8) - \
                    2*np.arctan(fm(zeta)) + (1-fm(zeta)**3)/12/zeta + np.pi/2 - 1
    def Psi_h(zeta):
        if abs(zeta) < 1e-6:
            return -a*zeta/2/Pr if zeta >= 0 else -9*zeta/4
        else:
            return -a*zeta/2/Pr if zeta >= 0 else \
                    2*np.log((1+fh(zeta))/2) + 2*(1-fh(zeta))/9/zeta - 1
    return (np.vectorize(phi_m, otypes=[float]),
            np.vectorize(phi_h, otypes=[float]),
            np.vectorize(psi_m, otypes=[float]),
            np.vectorize(psi_h, otypes=[float]),
            np.vectorize(Psi_m, otypes=[float]),
            np.vectorize(Psi_h, otypes=[float]))
