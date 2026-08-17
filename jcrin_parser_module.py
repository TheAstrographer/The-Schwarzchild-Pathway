import math
import numpy as np
from decimal import Decimal, getcontext
from typing import Dict, Any, List

# Optional heavy dependencies
try:
    import healpy as hp
    from astropy.io import fits
    HAS_HEALPIX = True
except ImportError:
    HAS_HEALPIX = False
    print("[WARNING] healpy / astropy not installed – HEALPix & FITS export disabled.")

getcontext().prec = 30

# ===========================================================================
# 1. JCRIN / PCS ANALYTICAL ENGINE
# ===========================================================================
class JcrinPcsAnalyticalEngine:
    """
    Executes calculations derived from the JCRIN / PCS Analytical Reference Table.
    Validates complex vacuum states, phase accumulations, and late-time tail parameters.
    """
    def __init__(self):
        self.EPS: float = 1e-9
        self.N_MAX: int = 1_000_000_000
        self.C_BB_100: float = 1.234e-5
        self.R_PCS: Decimal = Decimal("0.085")

    def compute_state_space(self, n: int) -> Dict[str, Any]:
        y_n = n * self.EPS
        real_part = y_n
        imag_part = -math.pi * y_n
        z_n = complex(real_part, imag_part)
        z_map = (1.0 / y_n - 1.0) if y_n > 0 else float('inf')
        return {
            "y_n": y_n,
            "z_n": z_n,
            "abs_z_n": abs(z_n),
            "z_map": z_map
        }

    def compute_phase_metrics(self, n: int) -> Dict[str, float]:
        f = n / self.N_MAX
        phi_f = -math.pi * f
        y_n = n * self.EPS
        gamma_n = -math.pi * y_n
        global_deflection = -math.pi * f
        return {
            "fractional_f": f,
            "primordial_phi": phi_f,
            "berry_phase_gamma": gamma_n,
            "global_deflection_rad": global_deflection,
            "global_deflection_deg": math.degrees(global_deflection)
        }

    def compute_late_time_tail(self, psi_rad: float = 0.0) -> Dict[str, Any]:
        delta_y = 1.0 - 0.7
        temporal_dilution = 1.0 / delta_y
        cos_psi = math.cos(psi_rad)
        a_f = temporal_dilution / cos_psi if cos_psi != 0 else float('inf')
        a = Decimal("0.7")
        one_plus_z = Decimal("1.0") / a
        z = one_plus_z - Decimal("1.0")
        return {
            "delta_y": delta_y,
            "temporal_dilution_factor": temporal_dilution,
            "inversion_amplitude_a_f": a_f,
            "scale_factor_a": a,
            "redshift_z": z
        }

    def evaluate_transport_kinematics(self) -> Dict[str, float]:
        rad = math.atan(2.0 * math.pi)
        return {
            "phase_lock_rad": rad,
            "phase_lock_deg": math.degrees(rad)
        }


# ===========================================================================
# 2. RANGE DEFINITIONS & COSMOLOGICAL CONSTANTS
# ===========================================================================
ranges = [
    # (n_start, n_end, k, decimals, z_start, z_end, era, relevance)
    (1_000_000, 1_999_999, 1, 6, 999.000, 500.500, "Early matter", "Reionization precursor"),
    (2_000_000, 2_999_999, 2, 6, 499.000, 333.444, "Matter domination", "Tensor mode growth"),
    (3_000_000, 3_999_999, 3, 6, 332.333, 250.000, "Matter domination", "Tensor mode growth"),
    (4_000_000, 4_999_999, 4, 6, 249.000, 200.000, "Matter domination", "Tensor mode growth"),
    (5_000_000, 5_999_999, 5, 6, 199.000, 166.667, "Late matter", "Peak B-mode signal"),
    (6_000_000, 6_999_999, 6, 6, 165.667, 142.857, "Late matter", "Peak B-mode signal"),
    (7_000_000, 7_999_999, 7, 4, 142.857, 125.016, "Late matter", "Peak B-mode signal"),
    (8_000_000, 8_999_999, 8, 3, 124.000, 110.123, "Late matter", "Peak B-mode signal"),
    (9_000_000, 9_999_999, 9, 3, 110.111, 100.010, "Late matter", "Peak B-mode signal"),
]

T_CMB = 2.725e6          # µK
r_fid = 0.01
delta_theta_per_range = 0.036   # degrees
total_delta_theta = 9 * delta_theta_per_range

analytical_engine = JcrinPcsAnalyticalEngine()

# ===========================================================================
# 3. CONSOLE MATRIX ENGINE
# ===========================================================================
print("=" * 95)
print("               COSMOLOGICAL INTERPRETATION - 9 INCREMENTAL METADATA RANGES")
print("=" * 95)
print(f"{'Range':<6} {'Redshift Window':<24} {'Cosmological Era':<22} {'B-Mode Relevance':<25}")
print("-" * 95)

total_r = 0.0
for idx, (start, end, k, dec, z_start, z_end, era, relevance) in enumerate(ranges, 1):
    label = f"R{idx}"
    # Grouped summary lines for cleaner output
    if idx == 2:
        print(f"{'R2-R4':<6} {'z: 499.0 → 200.0':<24} {'Matter domination':<22} {'Tensor mode growth':<25}")
    if idx == 5:
        print(f"{'R5-R9':<6} {'z: 199.0 → 100.1':<24} {'Late matter':<22} {'Peak B-mode signal':<25}")

    # Always accumulate the tensor contribution
    r_range = (delta_theta_per_range / 0.360) * 0.085
    total_r += r_range

    # Print individual line only for R1 (the others are summarised above)
    if idx == 1:
        print(f"{label:<6} {f'z: {z_start:.3f} → {z_end:.3f}':<24} {era:<22} {relevance:<25}")

print("-" * 95)
print(f"Total Signal : Δθ_p = {total_delta_theta:.3f}° → r ≈ {total_r:.6f} (pre-rescaling)")
print(f"Rescaled to  : r = {r_fid} | Map Scalar Factor = {r_fid / total_r:.6f}")
print("=" * 95)

# --- VACUUM STATE & HOLONOMY VERIFICATION ---
print("\n" + "=" * 95)
print("             JCRIN / PCS VACUUM STATE SPACE & GEOMETRIC HOLONOMY VERIFICATION")
print("=" * 95)

boundary_check_steps = [1_000_000, 7_000_000, 9_000_000, analytical_engine.N_MAX]
for step in boundary_check_steps:
    state = analytical_engine.compute_state_space(step)
    phase = analytical_engine.compute_phase_metrics(step)
    print(f" Step Index n = {step:12d} | Fractional Step f = {phase['fractional_f']:.4f}")
    print(f"   Complex Topology Vector z_n       : {state['z_n']}")
    print(f"   State Vector Magnitude |z_n|       : {state['abs_z_n']:.6f}")
    print(f"   Dynamic Inversion Mapping (z_map) : {state['z_map']:.4f}")
    print(f"   Accumulated Berry Phase (γ_n)     : {phase['berry_phase_gamma']:.6f} rad")
    print(f"   Global Polarization Deflection    : {phase['global_deflection_deg']:.2f}°")
    print("-" * 95)

print("\n" + "=" * 95)
print("                  LATE-TIME EXPANSION TAIL REGIME NORMALIZATION")
print("=" * 95)
tail = analytical_engine.compute_late_time_tail(psi_rad=0.0)
print(f"  Late-Epoch Transition Interval (Δy) : {tail['delta_y']:.1f}")
print(f"  Temporal Flux Dilution Factor (1/Δy) : {tail['temporal_dilution_factor']:.4f}")
print(f"  Base Inversion Gain Amplitude (A_f)   : {tail['inversion_amplitude_a_f']:.4f}")
print(f"  Scale Factor Equivalence Point (a)    : {tail['scale_factor_a']}")
print(f"  Calculated Epoch Cosmological Redshift: z = {tail['redshift_z']:.5f}")

print("-" * 95)
kin = analytical_engine.evaluate_transport_kinematics()
print("  Parallel Transport Phase Lock Limit Approaching Origin (t → 0+):")
print(f"    Geometric Phase Alignment Horizon  : {kin['phase_lock_rad']:.6f} rad")
print(f"    Geometric Phase Alignment Horizon  : {kin['phase_lock_deg']:.4f}°")
print("=" * 95)

# ===========================================================================
# 4. OPTIONAL HEALPIX / FITS EXPORT (only if libraries are present)
# ===========================================================================
export = False   # set True only when you want to write files

if export and HAS_HEALPIX:
    print("\n[EXPORT ENGINE] Commencing vectorized calculation pipelines…")
    nside = 512
    npix = hp.nside2npix(nside)
    theta, phi = hp.pix2ang(nside, np.arange(npix))

    for start, end, k, dec, z_start, z_end, era, relevance in ranges:
        n_mean = (start + end) / 2.0
        n_map = n_mean + 1e6 * np.sin(theta) * np.cos(phi)
        y_n = np.round(n_map * 1e-9, decimals=int(dec))

        phi_n = 2.0 * np.pi * y_n
        pol_angle = np.abs(-np.pi * y_n) * 180.0 / np.pi

        with np.errstate(divide='ignore', invalid='ignore'):
            z_map = np.where(y_n > 0, (1.0 / y_n) - 1.0, 0.0)

        # Example FITS table (you can expand columns as needed)
        cols = [
            fits.Column(name="y_n", format="E", array=y_n.astype(np.float32)),
            fits.Column(name="phi_n", format="E", array=phi_n.astype(np.float32)),
            fits.Column(name="pol_angle_deg", format="E", array=pol_angle.astype(np.float32)),
            fits.Column(name="z_map", format="E", array=z_map.astype(np.float32)),
        ]
        hdu = fits.BinTableHDU.from_columns(cols)
        hdu.header["RANGE"] = f"R{k}"
        hdu.header["ZSTART"] = z_start
        hdu.header["ZEND"] = z_end
        hdu.header["ERA"] = era
        hdu.writeto(f"jcrin_pcs_range_R{k}.fits", overwrite=True)
        print(f"  Wrote jcrin_pcs_range_R{k}.fits")
else:
    if export:
        print("[EXPORT] Skipped – healpy/astropy not available.") 
