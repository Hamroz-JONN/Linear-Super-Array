import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import numpy as np
import itertools
from complexPyTorch.complexLayers import ComplexLinear
from complexPyTorch.complexFunctions import complex_relu
from complexPyTorch.complexFunctions import complex_normalize
import argparse
import matplotlib.pyplot as plt

# ==========================================
# 3. PHYSICS ENGINE (3D Directivity + DF integral)
# ==========================================

def steering_vector_3d(deltas, omega, M, theta, phi=np.pi/2, c0=340.0, pm=None, am=None):
    """
    Returns conjugated steering vectors d*(omega, theta, phi), so that
    D @ h = d^H h holds directly.

    Shapes:
      deltas: (1, M) or (M,)
      omega : (bins,)
      theta : scalar or (D,)
      phi   : scalar or (D,)
      pm    : (1, M) or (M,)
      am    : (1, M) or (M,)
    Output:
      if single direction: (bins, M)
      if multiple directions: (bins, D, M)
    """
    device = deltas.device
    dtype_r = torch.float32
    dtype_c = torch.complex64

    deltas = torch.as_tensor(deltas, device=device, dtype=dtype_r)
    if deltas.dim() == 1:
        deltas = deltas.view(1, M)

    omega = torch.as_tensor(omega, device=device, dtype=dtype_r).view(-1)

    theta = torch.as_tensor(theta, device=device, dtype=dtype_r).view(-1)
    phi = torch.as_tensor(phi, device=device, dtype=dtype_r).view(-1)

    if theta.numel() == 1 and phi.numel() > 1:
        theta = theta.expand_as(phi)
    if phi.numel() == 1 and theta.numel() > 1:
        phi = phi.expand_as(theta)
    if theta.numel() != phi.numel():
        raise ValueError("theta and phi must have same length or be scalar.")

    pm = torch.as_tensor(pm, device=device, dtype=dtype_r)
    if pm.dim() == 1:
        pm = pm.view(1, M)

    if am is None:
        am = torch.zeros((1, M), device=device, dtype=dtype_r)
    else:
        am = torch.as_tensor(am, device=device, dtype=dtype_r)
        if am.dim() == 1:
            am = am.view(1, M)

    D = theta.numel()

    # propagation term: exp(-j * omega/c * x_m * cos(theta) * sin(phi))
    cos_prop = torch.cos(theta) * torch.sin(phi)                     # (D,)
    phase = torch.exp(
        -1j
        * omega.view(-1, 1, 1)
        * deltas.view(1, 1, M)
        * cos_prop.view(1, D, 1)
        / c0
    ).to(dtype_c)                                                   # (bins, D, M)

    # first-order directivity term from Eq. (5)
    mag = pm.view(1, 1, M) + (1.0 - pm.view(1, 1, M)) * (
        torch.cos(theta.view(1, D, 1) - am.view(1, 1, M))
        * torch.sin(phi.view(1, D, 1))
    )                                                               # (1, D, M)

    sv = mag.to(dtype_c) * phase                                    # (bins, D, M)

    if D == 1:
        return torch.conj(sv[:, 0, :])                              # (bins, M)
    return torch.conj(sv)                                           # (bins, D, M)

def getDF_dB_H(
    h,
    deltas,
    omega,
    M,
    c0,
    pm,
    am=None,
    theta_s=0,
    phi_s=(np.pi / 2),
    n_theta=72,
    n_phi=36,
    chunk=256,
):
    """3D DF using a direct spherical integral of |B(psi)|^2.

    DF(psi_s) = |B(psi_s)|^2 / ( (1/4pi) * ∫_{sphere} |B(psi)|^2 dOmega )

    This avoids building the full spatial coherence matrix G_M.
    """
    device = h.device
    
    assert pm.min() >= 0 and pm.max() <= 1, "pm must be in [0,1]"
    assert am.abs().max() <= 10, "am should be in radians (typically within ~[-pi,pi])"

    # Numerator at the steering direction
    d_s = steering_vector_3d(deltas, omega, M, theta=theta_s, phi=phi_s, c0=c0, pm=pm, am=am)  # (bins, M)
    h_vec = h.squeeze(-1)  # (bins, M)
    b_s = torch.sum(h_vec * d_s, dim=-1)
    
    num = (torch.abs(b_s) ** 2).real  # (bins,)

    # theta: [0, 2pi) (periodic)
    thetas = torch.linspace(0.0, 2 * np.pi, n_theta + 1, device=device, dtype=torch.float32)[:-1]
    dtheta = 2 * np.pi / n_theta

    # phi: [0, pi] (include endpoints)
    phis = torch.linspace(0.0, np.pi, n_phi, device=device, dtype=torch.float32)
    dphi = np.pi / (n_phi - 1)

    coeff_phi = torch.ones_like(phis)
    coeff_phi[0] = 0.5
    coeff_phi[-1] = 0.5

    # weight per phi strip: sin(phi) dphi
    w_phi = torch.sin(phis) * coeff_phi * dphi  # (n_phi,)

    th_grid, ph_grid = torch.meshgrid(thetas, phis, indexing="ij")
    theta_flat = th_grid.reshape(-1)
    phi_flat = ph_grid.reshape(-1)

    # full dOmega weight = sin(phi)dphi dtheta, then divide by 4pi to make it an average
    w_flat = w_phi.view(1, -1).expand(n_theta, -1).reshape(-1)
    w_flat = w_flat * (dtheta / (4.0 * np.pi))

    bins = omega.numel()
    D = theta_flat.numel()

    den = torch.zeros(bins, device=device, dtype=torch.float32)

    for start in range(0, D, chunk):
        end = min(start + chunk, D)
        th = theta_flat[start:end]
        ph = phi_flat[start:end]
        w = w_flat[start:end]
        
        v = steering_vector_3d(deltas, omega, M, th, ph, c0, pm=pm, am=am)  # (bins, c, M)

        b = torch.sum(h_vec.unsqueeze(1) * v, dim=-1)  # (bins, c)
        power = (torch.abs(b) ** 2).real  # (bins, c)

        den = den + torch.sum(power * w.view(1, -1), dim=1)

    DF = (num / (den + 1e-12)).view(bins, 1, 1)
    return 10 * torch.log10(torch.abs(DF))


# ==========================================
# 4. UPDATED LOSS (ReLU Hinge)
# ==========================================

def getWNG_dB_H(h, deltas, omega, M, c0, pm, am, theta_s=0.0, phi_s=np.pi/2):
    """
    Literal Eq. (7):
        WNG = |d^H(theta_s, phi_s) h|^2 / (h^H h)
    """
    if h.dim() == 2:
        h = h.unsqueeze(-1)  # (bins, M, 1)

    d_s = steering_vector_3d(
        deltas=deltas,
        omega=omega,
        M=M,
        theta=theta_s,
        phi=phi_s,
        c0=c0,
        pm=pm,
        am=am,
    )  # (bins, M), already conjugated => d^H row form

    num = torch.abs(torch.sum(d_s * h.squeeze(-1), dim=-1, keepdim=True)) ** 2  # (bins,1)
    den = torch.real(torch.matmul(torch.conj(h).transpose(-1, -2), h)).squeeze(-1)  # (bins,1)

    wng = num / (den + 1e-12)
    return 10.0 * torch.log10(torch.abs(wng) + 1e-12)




def getD(deltas, omega, M, c0, null_list, pm=None, am=None):
    if pm is None:
        pm = torch.ones(1, M, device=deltas.device)

    N = len(null_list)
    bins = len(omega)
    D = torch.zeros(bins, N + 1, M, dtype=torch.cfloat).to(deltas.device)
    
    D[:, 0, :] = steering_vector_3d(deltas, omega, M, theta=0.0, phi=(np.pi / 2), c0=c0, pm=pm, am=am)
    for n in range(1, N + 1):
        D[:, n, :] = steering_vector_3d(deltas, omega, M, theta=null_list[n - 1], phi=(np.pi / 2), c0=c0, pm=pm, am=am)
    return D


# ==========================================
# 5. ANALYTIC BASELINE SOLVER (Paper LSA / LSA+ style constraints)
# ==========================================
def solve_null_constrained_min_norm(
    freqs_hz,
    deltas,
    pm,
    am=None,
    theta_s=0,
    phi_s=(np.pi / 2),
    null_offsets_deg=(106.0, 153.0),
    c0=340.0,
    diag_load=1e-6,
):
    device = deltas.device
    freqs = torch.as_tensor(freqs_hz, device=device, dtype=torch.float32).view(-1)
    omega = 2 * np.pi * freqs  # (bins,)
    
    # Build angles: [look, +off1, -off1, +off2, -off2]
    offs = []
    for od in null_offsets_deg:
        o = float(od) * np.pi / 180.0
        offs += [o, -o]
    angles = torch.tensor([float(theta_s)] + [float(theta_s) + o for o in offs],
                          device=device, dtype=torch.float32)
    
    K = angles.numel()

    # Desired responses: [1, 0, 0, 0, 0]
    c = torch.zeros(K, 1, device=device, dtype=torch.cfloat)
    c[0, 0] = 1.0
    
    # Constraint matrix D: (bins, K, M) with rows = d* so D @ h = d^H h
    D = steering_vector_3d(
        deltas, omega, deltas.shape[-1],
        theta=angles, phi=torch.tensor(phi_s, device=device, dtype=torch.float32),
        c0=c0, pm=pm, am=am
    )

    ''''''

    # Batch solve G x = c
    c_b = c.unsqueeze(0).expand(omega.numel(), -1, -1)  # (bins, K, 1)
    
    D_pinv = torch.linalg.pinv(D, rcond=1e-12)        # (bins, M, K)
    h = D_pinv @ c_b                     # (bins, M, 1)
    
    '''alternative solve below''' 
    
    # D_H = torch.conj(D).transpose(-1, -2)           # (bins, M, K)

    # G = D @ D_H                                     # (bins, K, K)  = D D^H


    # I = torch.eye(K, device=device, dtype=torch.cfloat).unsqueeze(0)  # (1, K, K)
    # G = G + diag_load * I

    # c_b = c.unsqueeze(0).expand(omega.numel(), -1, -1)  # (bins, K, 1)
    # x = torch.linalg.solve(G, c_b)                  # (bins, K, 1) = (D D^H)^-1 c
    # h = D_H @ x                                     # (bins, M, 1)
    
    '''alternative solve above'''
    
    return h, D, angles

def plot_beampattern_polar(
    deltas,              # torch tensor (1,M) or (M,)
    pm,                  # torch tensor (1,M) or (M,)
    am,                  # torch tensor (1,M) or (M,), mic orientations in radians
    h,                   # torch tensor (M,), (M,1), (bins,M), or (bins,M,1)
    f_hz,                # float: frequency to plot (label only; you should pass matching h)
    steering_vector_3d,  # function handle
    theta_s=0,         # look azimuth for normalization (radians)
    phi=np.pi/2,         # elevation cut (radians)
    c0=340.0,
    n_theta=721,
    use_db=True,
    normalize_to_look=True,
    clip_db_min=-60.0,
    title=None,
    # optional: print detected minima (null candidates)
    report_minima=False,
    top_k_minima=8,
    min_separation_deg=5.0,
):
    """
    Polar (circular) beampattern plot for a 1D azimuth cut theta ∈ [-pi, pi], phi fixed.

    IMPORTANT: Assumes steering_vector_3d returns d* (conjugated steering).
    Response computed as B(theta) = sum_m h_m * d*_m(theta) = d^H h.

    FIX: Never uses negative radius. If use_db=True, it plots radius = (dB - clip_db_min),
         so radius is in [0, -clip_db_min] and angles are not flipped.
    """
    
    
    
    device = deltas.device if torch.is_tensor(deltas) else torch.device("cpu")

    # --- shapes ---
    deltas = torch.as_tensor(deltas, device=device)
    if deltas.dim() == 1:
        deltas = deltas.unsqueeze(0)
    M = deltas.shape[-1]

    pm = torch.as_tensor(pm, device=device, dtype=torch.float32)
    if pm.dim() == 1:
        pm = pm.unsqueeze(0)

    am = torch.as_tensor(am, device=device, dtype=torch.float32)
    if am.dim() == 1:
        am = am.unsqueeze(0)
        
    # --- pick h for a single frequency ---
    h = torch.as_tensor(h, device=device)
    h = h.to(torch.cfloat).view(1, M)  # (1,M)

    # omega (single bin)
    omega = torch.tensor([2*np.pi*float(f_hz)], dtype=torch.float32, device=device)

    # theta sweep
    # thetas = torch.linspace(-np.pi, np.pi, n_theta, device=device, dtype=torch.float32)
    thetas = torch.linspace(-np.pi, np.pi, n_theta + 1, device=device, dtype=torch.float32)[:-1]

    phi_t = torch.tensor(float(phi), device=device, dtype=torch.float32)
    
    # steering for all thetas -> (1,T,M) returning d*
    d_star = steering_vector_3d(deltas, omega, M, theta=thetas, phi=phi_t, c0=c0, pm=pm, am=am)
    
    # B(theta) = sum h * d*  -> (T,)
    B = torch.sum(d_star * h.view(1, 1, M), dim=-1).squeeze(0)



    # normalize to look direction
    if normalize_to_look:
        d_star_s = steering_vector_3d(deltas, omega, M, theta=float(theta_s), phi=phi_t, c0=c0, pm=pm, am=am)
        B_s = torch.sum(d_star_s.squeeze(0) * h.squeeze(0), dim=-1)
        B = B / (B_s + 1e-12)
        # B = B / (torch.max(torch.abs(B)) + 1e-30)
        
        print("abs(B_s) at theta_s:", float(torch.abs(B_s)))
        print("global max |B|:", float(torch.max(torch.abs(B))))
        

    mag = torch.abs(B)  # (T,)

    theta_np = thetas.detach().cpu().numpy()
    theta_deg = theta_np * 180.0 / np.pi
    mag_np = mag.detach().cpu().numpy()

    # Optional: detect minima from linear magnitude (safe)
    if report_minima:
        y = mag_np
        idx = np.where((y[1:-1] < y[:-2]) & (y[1:-1] < y[2:]))[0] + 1
        idx = idx[np.argsort(y[idx])]  # deepest first
        chosen = []
        minima = []
        for i in idx:
            ang = theta_deg[i]
            # wrap [-180,180]
            angw = ((ang + 180) % 360) - 180
            if all(abs(((angw - a + 180) % 360) - 180) >= min_separation_deg for a in chosen):
                chosen.append(angw)
                minima.append((angw, y[i]))
            if len(minima) >= top_k_minima:
                break
        print("\n=== Deepest minima (linear magnitude) ===")
        for k, (angw, val) in enumerate(minima, 1):
            lvl_db = 20*np.log10(val + 1e-12)
            print(f"{k:02d}) theta={angw:7.2f} deg | |B|={val:.3e} | {lvl_db:7.2f} dB")

    # ---- radius construction that NEVER goes negative ----
    if use_db:
        patt_db = 20.0 * np.log10(mag_np + 1e-12)
        patt_db = np.maximum(patt_db, clip_db_min)  # clip floor
        r = patt_db - clip_db_min                   # shift => [0, -clip_db_min]
        rlabel = f"dB (shifted by {clip_db_min} dB)"
        rmax = -clip_db_min
    else:
        r = mag_np
        rlabel = "linear |B|"
        rmax = None
        
    # --- polar plot ---
    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(111, polar=True)
    ax.plot(theta_np, r)

    if title is None:
        title = f"Beampattern @ {float(f_hz):.0f} Hz (φ={float(phi)*180/np.pi:.0f}°)"
    ax.set_title(title, va="bottom")
    
    ax.set_rlim(0.0, -clip_db_min)
    ticks_db = np.array([clip_db_min, -40, -30, -20, -10, 0], dtype=float)
    ticks_db = ticks_db[(ticks_db >= clip_db_min) & (ticks_db <= 0)]
    ax.set_yticks(ticks_db - clip_db_min)
    ax.set_yticklabels([f"{t:.0f} dB" for t in ticks_db])
    
    ax.grid(True)

    # set radial limits nicely
    if use_db:
        ax.set_rlim(0.0, rmax)
        # put labels back in actual dB values
        ticks_db = np.array([clip_db_min, -40, -30, -20, -10, 0], dtype=float)
        ticks_db = ticks_db[(ticks_db >= clip_db_min) & (ticks_db <= 0)]
        ticks_r = ticks_db - clip_db_min
        ax.set_yticks(ticks_r)
        ax.set_yticklabels([f"{t:.0f} dB" for t in ticks_db])
    ax.set_rlabel_position(135)

    plt.tight_layout()
    plt.show()

    return theta_np, r


# ==========================================
# 6. MAIN LOOP
# ==========================================

def main(M, L, targetDF, targetWNG, pm, am, deltas, theta_s=0):
    # Frequency range (front-only steering)
    freqs = torch.linspace(100.0, 4000.0, steps=40, dtype=torch.float64)
    target_freqs = [1000, 2000, 3000, 4000]
    
    omega = 2*np.pi*torch.tensor(freqs, dtype=torch.float32)

    # Analytic baseline weights (NO FilterNet)
    h, D, angles = solve_null_constrained_min_norm(
        freqs_hz=freqs,
        deltas=deltas,
        pm=pm,
        am=am,
        theta_s=theta_s
    )

    # Metrics
    wng = getWNG_dB_H(
        h=h,
        deltas=deltas,
        omega=omega,
        M=M,
        c0=340.0,
        pm=pm,
        am=am,
        theta_s=theta_s
    ).squeeze(-1)
    
    df = getDF_dB_H(h, deltas, omega, M, 340.0, pm, am=am, theta_s=theta_s).squeeze()
    
    print(freqs)
    print(wng)
    print(df)
    
    # Plot
    plt.figure(figsize=(15, 7))
    
    # WNG
    plt.subplot(1, 2, 1)

    plt.plot(freqs, wng, "-", ms=2, lw=2)
    target_wng = np.interp(target_freqs, freqs, wng)
    plt.plot(target_freqs, target_wng, '+', color="red", markersize=10)
    
    plt.title(f"WNG")
    plt.xlabel("Frequency (Hz)"); plt.ylabel("WNG (dB)"); plt.grid(True)

    # DF
    plt.subplot(1, 2, 2)
    
    plt.plot(freqs, df, "-", ms=2, lw=2)
    target_df = np.interp(target_freqs, freqs, df)
    plt.plot(target_freqs, target_df, '+', color="red", markersize=10)
    
    plt.title(f"DF")
    plt.xlabel("Frequency (Hz)"); plt.ylabel("DF (dB)"); plt.grid(True)

    plt.tight_layout()
    plt.show()

def parse():
    parser = argparse.ArgumentParser(description="Perform NONULA experiments.", prog="NNv7")
    parser.add_argument("--M", type=int, nargs=1, default=[7], help="Number of microphones")
    parser.add_argument("--L", type=float, nargs=1, default=[0.05], help="The length of the microphone array")
    parser.add_argument("--tWNG", type=int, nargs=1, default=[0], help="Target WNG")
    parser.add_argument("--tDF", type=float, nargs=1, default=[8], help="Target DF")
    parser.add_argument("--rw", type=float, nargs=1, default=[0.5], help="Weight applied to WNG")

    args = parser.parse_args()
    return args.M[0], args.L[0], args.tDF[0], args.tWNG[0]


if __name__ == "__main__":
    device = torch.device("cpu")    
    torch.manual_seed(3)
    torch.autograd.set_detect_anomaly(True)
    M, L, targetDF, targetWNG = parse()
    
    
    spacing = 0.005  # 0.5 cm
    deltas = torch.arange(M, device=device, dtype=torch.float32).view(1, M) * spacing

    # Example arrangement: 3 omni + 4 bidirectional
    # You should match the exact ordering you intend to reproduce.
    pm = torch.tensor([[1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0]], device=device, dtype=torch.float32)

    # Baseline LSA: all directional mics oriented at pi/2.
    # For omni, angle is irrelevant, but keep it as pi/2 for simplicity.
    am = torch.full((1, M), np.pi / 2, device=device, dtype=torch.float32)

    # show beampattern

    h, D, angles = solve_null_constrained_min_norm(freqs_hz=  np.linspace(1000, 1000, 1), deltas=deltas, pm=pm, am=am, theta_s=0)
    
    print("angles (deg):", angles.detach().cpu().numpy() * (180.0/np.pi))
    plot_beampattern_polar(deltas=deltas, pm=pm, am=am, f_hz=1000, steering_vector_3d=steering_vector_3d, h=h, report_minima=True, theta_s=0)
            
    # show WNG and DF
    
    
    # for angle in [0, np.pi/6, np.pi/3, np.pi/2]:
    main(M, L, targetDF, targetWNG, pm, am, deltas, 0)