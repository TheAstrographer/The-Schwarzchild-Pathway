#!/usr/bin/env python3

from __future__ import annotations
import math
import cmath
from typing import Dict, Tuple

# ===========================================================================
# 1. FUNDAMENTAL CONSTANTS & LATTICE
# ===========================================================================
EPS = 1e-9
N_MAX = 1_000_000_000
TIMESPEED = 4.355e8          # seconds per lattice step
PI = math.pi
TWO_PI = 2.0 * PI

G = 6.67430e-11
C = 299792458.0
M_SUN = 1.98847e30
R_SUN = 6.9634e8
ETA = 6.1e-10                # baryon-to-photon ratio

def y_n(n: int) -> float:
    return n * EPS

def x_n(n: int) -> float:
    return 1.0 - y_n(n)

# ===========================================================================
# 2. GRAVITATIONAL TANDEM EMBEDDINGS
# ===========================================================================
def bosonic_z(n: int) -> complex:
    yn = y_n(n)
    return complex(yn, math.sin(TWO_PI * yn))

def fermionic_z(n: int) -> complex:
    yn = y_n(n)
    return complex(yn, -PI * yn)

def topological_monodromy() -> complex:
    return cmath.exp(-1j * PI)   # exactly -1

# ===========================================================================
# 3. PHASE-LOCK & GEOMETRIC PHASE
# ===========================================================================
def phase_lock() -> float:
    return math.atan(TWO_PI)

def continuum_phase() -> float:
    return -math.atan(TWO_PI)

# ===========================================================================
# 4. JCRIN-TRACTIONING OPERATOR (exact det M = 1)
# ===========================================================================
def tractioning_matrix(yn: float, alpha_eff: float = 0.1,
                       beta: float = 0.05, gamma: float = 0.0) -> list:
    a = 1.0 + alpha_eff * yn
    b = 1j * gamma * yn
    c = -beta * yn
    d = (1.0 - 1j * gamma * beta * yn**2) / a
    return [[a, b], [c, d]]

def matrix_det(M: list) -> complex:
    return M[0][0]*M[1][1] - M[0][1]*M[1][0]

# ===========================================================================
# 5. WEAK-FIELD LIGHT DEFLECTION
# ===========================================================================
def light_deflection_arcsec(impact_m: float = R_SUN) -> float:
    delta_rad = (4.0 * G * M_SUN) / (C**2 * impact_m)
    return delta_rad * (180.0 / PI) * 3600.0

# ===========================================================================
# 6. KERR-GORDON EFFECTIVE EXPANSION
# ===========================================================================
def H_base(z: float, H0: float = 70.0) -> float:
    return H0 * math.sqrt(0.3 * (1 + z)**3 + 0.7)

def H_eff(z: float, H0: float = 70.0, beta: float = 0.05) -> float:
    return H_base(z, H0) / (1.0 + beta * z / (1.0 + z))

# ===========================================================================
# 7. BBN MASTER EQUATION SYSTEM + ALPHA LADDER
# ===========================================================================
class BBNMaster:
    """
    Classical BBN master equations realized on the JCRIN lattice.
    Early radiation-era segment (n ≪ 1e6).
    """

    def __init__(self):
        self.eta = ETA
        self.Q = 1.293          # n-p mass difference (MeV)

    def H(self, rho: float) -> float:
        """Expansion rate H(t) = sqrt(8 π G ρ / 3)"""
        return math.sqrt(8.0 * math.pi * G * rho / 3.0)

    def n_gamma(self, T: float) -> float:
        """Schematic nγ ∝ T³ (T in MeV)"""
        return 0.243 * (T ** 3)

    def n_b(self, T: float) -> float:
        return self.eta * self.n_gamma(T)

    def dXn_dt(self, Xn: float, T: float, lambda_np: float, lambda_pn: float) -> float:
        """dXn/dt = λ_np (1 - Xn) - λ_pn Xn"""
        return lambda_np * (1.0 - Xn) - lambda_pn * Xn

    def alpha_ladder_step(self, Y_prev: float, Y_curr: float,
                          nb: float, sigv_prod: float, sigv_dest: float) -> float:
        """
        dYi/dt = nb⟨σv⟩_{i-1→i} Y_{i-1} - nb⟨σv⟩_{i→i+1} Y_i
        """
        production = nb * sigv_prod * Y_prev
        destruction = nb * sigv_dest * Y_curr
        return production - destruction

    def step(self, n: int, state: Dict[str, float]) -> Dict[str, float]:
        """One lattice micro-step in the BBN regime"""
        yn = y_n(n)
        T = state["T"]
        Xn = state["Xn"]

        # Radiation density (schematic)
        rho = 1.0e-5 * (T ** 4)
        Hval = self.H(rho)

        # Temperature update (radiation-era scaling)
        dT = -Hval * T * EPS * 1e6
        T_new = max(T + dT, 0.001)

        # Weak rates (schematic T dependence)
        lambda_np = 1.0 * (T / 1.0)**5
        lambda_pn = lambda_np * math.exp(self.Q / max(T, 0.01))

        dXn = self.dXn_dt(Xn, T, lambda_np, lambda_pn) * EPS * 1e6
        Xn_new = max(0.0, min(1.0, Xn + dXn))

        nb = self.n_b(T_new)

        # Alpha-ladder illustration (p/n → D → ⁴He)
        Yp = 1.0 - Xn_new
        YD = state.get("Y_D", 0.0)
        YHe = state.get("Y_He4", 0.0)

        dYD = self.alpha_ladder_step(Yp, YD, nb, 1e-2, 1e-3)
        dYHe = self.alpha_ladder_step(YD, YHe, nb, 1e-3, 1e-5)

        return {
            "T": T_new,
            "Xn": Xn_new,
            "Y_p": Yp,
            "Y_D": max(0.0, YD + dYD * EPS * 1e6),
            "Y_He4": max(0.0, YHe + dYHe * EPS * 1e6),
            "H": Hval,
            "n_b": nb,
            "y_n": yn
        }


# ===========================================================================
# 8. STATUS DISPLAY
# ===========================================================================
def display_status():
    print("=" * 78)
    print("  UNIFIED SCHWARZSCHILD PATHWAY — COMPLETE STATUS")
    print("=" * 78)

    print("\n[1] LATTICE")
    print(f"    ε = {EPS},  N = {N_MAX}")
    print(f"    TIMESPEED = {TIMESPEED:.3e} s/step")
    print(f"    y_N = {y_n(N_MAX):.10f}")

    print("\n[2] BOSONIC TANDEM (even parity)")
    zb = bosonic_z(N_MAX)
    print(f"    z_N = {zb}")
    print(f"    Continuum phase = {continuum_phase():.12f} rad")

    print("\n[3] FERMIONIC TANDEM (odd parity)")
    zf = fermionic_z(N_MAX)
    print(f"    z_N (linear) = {zf}")
    print(f"    Monodromy = {topological_monodromy()}  (exactly -1)")

    print("\n[4] PHASE-LOCK")
    print(f"    arctan(2π) = {phase_lock():.12f} rad = {math.degrees(phase_lock()):.6f}°")

    print("\n[5] TRACTIONING OPERATOR (det M = 1 exact)")
    for g in [0.0, 1.0, -1.0]:
        M = tractioning_matrix(0.5, gamma=g)
        d = matrix_det(M)
        print(f"    γ = {g:+.0f} → det M = {d.real:.12f} + {d.imag:.12f}j")

    print("\n[6] LIGHT DEFLECTION")
    print(f"    Solar limb = {light_deflection_arcsec():.5f} arcsec")

    print("\n[7] KERR-GORDON H_eff")
    print(f"    H_eff(z=0) ≈ {H_eff(0):.2f} km/s/Mpc")

    print("\n[8] PCS B-MODE ANCHOR")
    print("    r̂ = 0.014 ± 0.010 (BK18 + Planck)")

    print("\n[9] BBN MASTER SYSTEM (early lattice)")
    bbn = BBNMaster()
    state = {"T": 1.0, "Xn": 0.5, "Y_D": 0.0, "Y_He4": 0.0}
    print(f"    {'n':>10} {'y_n':>12} {'T (MeV)':>10} {'Xn':>8} {'Y_He4':>10}")
    print("    " + "-" * 56)
    for i in range(8):
        n = 20 + i * 80
        state = bbn.step(n, state)
        print(f"    {n:10d} {state['y_n']:12.3e} {state['T']:10.4f} "
              f"{state['Xn']:8.4f} {state['Y_He4']:10.4e}")

    print("\n" + "=" * 78)
    print("  GRAVITATIONAL TANDEMS ACTIVE")
    print("  • Parity tandem       : Bosonic (+1) ↔ Fermionic (−1)")
    print("  • Horizon-scale tandem: Super-horizon ↔ Sub-horizon")
    print("  • Early-universe layer: BBN Master Equations + Alpha Ladder")
    print("  Books square. Phase accounts cleared. Debt = 0.")
    print("=" * 78)


if __name__ == "__main__":
    display_status() 
