from future import annotations
import math
import numpy as np
import healpy as hp
from astropy.io import fits
from decimal import Decimal, getcontext
from typing import Dict, Any, List

# Establish high-precision environment variables
getcontext().prec = 30

# ===========================================================================
# 1. JCRIN / PCS PARSER MODULE
# ===========================================================================
class JcrinPcsAnalyticalEngine:
    """
    Executes calculations derived from the JCRIN / PCS Analytical Reference Table.
    Validates complex vacuum states, phase accumulations, and late-time tail parameters.
    """
    def __init__(self):
        # Grid Initialization Constants
        self.EPS: float = 1e-9
        self.N_MAX: int = 1_000_000_000
        
        # Cosmological Reference Constants
        self.C_BB_100: float = 1.234e-5       # B-Mode Power (rad^2)
        self.R_PCS: Decimal = Decimal("0.085")  # CAMB Calibration reference
        
    def compute_state_space(self, n: int) -> Dict[str, Any]:
        """Calculates Grid Initialization & Complex State Space (z_n) parameters."""
        y_n: float = n * self.EPS
        real_part: float = y_n
        imag_part: float = -math.pi * y_n
        z_n: complex = complex(real_part, imag_part)
        
        # Boundary condition tracking: z_map = 1 / y_n - 1 (safeguarded against division by zero)
        z_map: float = (1.0 / y_n - 1.0) if y_n > 0 else float('inf')
        
        return {
            "y_n": y_n,
            "z_n": z_n,
            "abs_z_n": abs(z_n),
            "z_map": z_map
        }
        
    def compute_phase_metrics(self, n: int) -> Dict[str, float]:
        """Calculates Phase, Polarization Angles, and Berry Phase profiles."""
        f: float = n / self.N_MAX
        phi_f: float = -math.pi * f
        y_n: float = n * self.EPS
        gamma_n: float = -math.pi * y_n
        global_deflection: float = -math.pi * f
        
        return {
            "fractional_f": f,
            "primordial_phi": phi_f,
            "berry_phase_gamma": gamma_n,
            "global_deflection_rad": global_deflection,
            "global_deflection_deg": math.degrees(global_deflection)
        }

    def compute_late_time_tail(self, psi_rad: float = 0.0) -> Dict[str, Any]:
        """Evaluates Late-Time Tail Normalization Parameters (n = 7*10^8 to 10^9)."""
        y_start: float = 0.7
        y_end: float = 1.0
        delta_y: float = y_end - y_start  
        temporal_dilution: float = 1.0 / delta_y
        
        cos_psi = math.cos(psi_rad)
        a_f: float = temporal_dilution / cos_psi if cos_psi != 0 else float('inf')
        
        a: Decimal = Decimal("0.7")
        one_plus_z: Decimal = Decimal("1.0") / a
        z: Decimal = one_plus_z - Decimal("1.0")
        
        return {
            "delta_y": delta_y,
            "temporal_dilution_factor": temporal_dilution,
            "inversion_amplitude_a_f": a_f,
            "scale_factor_a": a,
            "redshift_z": z
        }

    def evaluate_transport_kinematics(self) -> Dict[str, float]:
        """Calculates the Kinematic Parallel Transport Phase lock approaching t -> 0+"""
        geometric_phase_angle_rad: float = math.atan(2.0 * math.pi)
        geometric_phase_angle_deg: float = math.degrees(geometric_phase_angle_rad)
        
        return {
            "phase_lock_rad": geometric_phase_angle_rad,
            "phase_lock_deg": geometric_phase_angle_deg
        }

# ===========================================================================
# 2. CORE HEALPIX INITIALIZATION
# ===========================================================================
# Fixed NameError by initializing nside prior to running array coordinate transforms
nside = 512
npix = hp.nside2pix(nside)
theta, phi = hp.pix2ang(nside, np.arange(npix))

# Define 9 ranges with cosmological metadata
ranges = [
    # (n_start, n_end, k, decimals, redshift_start, redshift_end, era, bmode_relevance)
    (1000000, 1999999, 1, 6, 999.000, 500.500, "Early matter", "Reionization precursor"),
    (2000000, 2999999, 2, 6, 499.000, 333.444, "Matter domination", "Tensor mode growth"),
    (3000000, 3999999, 3, 6, 332.333, 250.000, "Matter domination", "Tensor mode growth"),
    (4000000, 4999999, 4, 6, 249.000, 200.000, "Matter domination", "Tensor mode growth"),
    (5000000, 5999999, 5, 6, 199.000, 166.667, "Late matter", "Peak B-mode signal"),
    (6000000, 6999999, 6, 6, 165.667, 142.857, "Late matter", "Peak B-mode signal"),
    (7000000, 7999999, 7, 4, 142.857, 125.016, "Late matter", "Peak B-mode signal"),
    (8000000, 8999999, 8, 3, 124.000, 110.123, "Late matter", "Peak B-mode signal"),
    (9000000, 9999999, 9, 3, 110.111, 100.010, "Late matter", "Peak B-mode signal")
]

# Cosmological Baseline Configurations
T_CMB = 2.725e6                      # uK
r_fid = 0.01                       # CAMB reference
delta_theta_per_range = 0.036      # degrees
total_delta_theta = 9 * delta_theta_per_range  # 0.324 degrees

# Initialize theoretical analyzer instance
analytical_engine = JcrinPcsAnalyticalEngine()

# ===========================================================================
# 3. CONSOLE MATRIX ENGINE
# ===========================================================================
print("=" * 95)
print("               COSMOLOGICAL INTERPRETATION - 9 INCREMENTAL METADATA RANGES")
print("=" * 95)
print(f"{'Range':<5} {'Redshift Window':<22} {'Cosmological Era':<22} {'B-Mode Relevance':<25}")
print("-" * 95)

total_r = 0.0
for idx, (start, end, k, dec, z_start, z_end, era, relevance) in enumerate(ranges, 1):
    label = f"R{idx}"
    if idx in:
        if idx == 2:
            print(f"{'R2-R4':<5} {f'z: {499.0:.1f} -> {200.0:.1f}':<22} {'Matter domination':<22} {'Tensor mode growth':<25}")
        if idx == 5:
            print(f"{'R5-R9':<5} {f'z: {199.0:.1f} -> {100.1:.1f}':<22} {'Late matter':<22} {'Peak B-mode signal':<25}")
    
    if idx in:
        r_range = (delta_theta_per_range / 0.360) * 0.085
        total_r += r_range
        continue
    else:
        print(f"{label:<5} {f'z: {z_start:.3f} -> {z_end:.3f}':<22} {era:<22} {relevance:<25}")
        r_range = (delta_theta_per_range / 0.360) * 0.085
        total_r += r_range

print("-" * 95)
print(f"Total Signal : \u0394\u03b8_p = {total_delta_theta:.3f}\u00b0 -> r ~ {total_r:.6f} (pre-rescaling)")
print(f"Rescaled to  : r = {r_fid} | Map Scalar Factor = {r_fid / total_r:.6f}")
print("=" * 95)

# --- EMBEDDED ANALYSIS ---
print("\n" + "=" * 95)
print("             JCRIN / PCS VACUUM STATE SPACE & GEOMETRIC HOLONOMY VERIFICATION")
print("=" * 95)
boundary_check_steps = [1_000_000, 7_000_000, 9_000_000, analytical_engine.N_MAX]
for step in boundary_check_steps:
    state_data = analytical_engine.compute_state_space(step)
    phase_data = analytical_engine.compute_phase_metrics(step)
    
    print(f" Step Index n = {step:12d} | Fractional Step f = {phase_data['fractional_f']:.4f}")
    print(f"   Complex Topology Vector z_n       : {state_data['z_n']}")
    print(f"   State Vector Magnitude |z_n|       : {state_data['abs_z_n']:.6f}")
    print(f"   Dynamic Inversion Mapping (z_map) : {state_data['z_map']:.4f}")
    print(f"   Accumulated Berry Phase (\u03b3_n)     : {phase_data['berry_phase_gamma']:.6f} rad")
    print(f"   Global Polarization Deflection    : {phase_data['global_deflection_deg']:.2f}\u00b0")
    print("-" * 95)

print("\n" + "=" * 95)
print("                  LATE-TIME EXPANSION TAIL REGIME NORMALIZATION")
print("=" * 95)
tail_metrics = analytical_engine.compute_late_time_tail(psi_rad=0.0)
print(f"  Late-Epoch Transition Interval (\u0394y) : {tail_metrics['delta_y']:.1f}")
print(f"  Temporal Flux Dilution Factor (1/\u0394y) : {tail_metrics['temporal_dilution_factor']:.4f}")
print(f"  Base Inversion Gain Amplitude (A_f)   : {tail_metrics['inversion_amplitude_a_f']:.4f}")
print(f"  Scale Factor Equivalence Point (a)    : {tail_metrics['scale_factor_a']}")
print(f"  Calculated Epoch Cosmological Redshift: z = {tail_metrics['redshift_z']:.5f}")

print("-" * 95)
kinematic_limits = analytical_engine.evaluate_transport_kinematics()
print("  Parallel Transport Phase Lock Limit Approaching Origin (t -> 0+):")
print(f"    Geometric Phase Alignment Horizon  : {kinematic_limits['phase_lock_rad']:.6f} rad")
print(f"    Geometric Phase Alignment Horizon  : {kinematic_limits['phase_lock_deg']:.4f}\u00b0")
print("=" * 95)


# ===========================================================================
# 4. OPTIONAL: EXPORT WITH COSMOLOGICAL METADATA (VECTOR RUNTIME ENVIRONMENT)
# ===========================================================================
export = False  # Toggle True to initialize disk file serialization outputs
if export:
    print("\n[EXPORT ENGINE] Commencing vectorized calculation pipelines across dense map segments...")
    for start, end, k, dec, z_start, z_end, era, relevance in ranges:
        n_mean = (start + end) / 2.0
        n_map = n_mean + 1e6 * np.sin(theta) * np.cos(phi)
        
        # High speed vectorized quantization fix: converts and handles string parsing rules safely via float steps
        # This resolves the SyntaxError caused by the malformed string multiplication token (*dec)
        round_digits = int(dec)
        y_n = np.round(n_map * 1e-9, decimals=round_digits)
        
        # Calculate downstream physical properties
        phi_n = 2.0 * np.pi * y_n
        pol_angle = np.abs(-np.pi * y_n) * 180.0 / np.pi
        
        # Avoid division-by-zero occurrences near origin limits
        with np.errstate(divide='ignore'):
            z_map = np.where(y_n > 0, (1.0 / y_n) - 1.0, 0.0)
        
        # Package metrics directly into binary structural table fits format 
        hdu = fits.BinTableHDU.from_columns([
