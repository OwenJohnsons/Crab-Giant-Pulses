import argparse 
import glob 
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import LogLocator
import scienceplots; plt.style.use(['science', 'no-latex'])


def fetch_args(): 
    '''
    Fetches the arguments from the command line 
    '''
    parser = argparse.ArgumentParser(description='Single Pulse Analysis Crab Gian Pulses.')
    parser.add_argument('-i', '--input', type=str, help='Input directory', required=True)
    parser.add_argument('-t', '--threshold', type=float, help='Threshold for single pulse detection (default = 0)', required=False)
    
    return parser.parse_args()


def read_transientx(cands_file):
    mjd, dm, width, snr, png, ifile = np.loadtxt(cands_file, usecols=(2, 3, 4, 5, 8, 10), unpack=True, dtype=str)
    mjd = mjd.astype(float); dm = dm.astype(float); width = width.astype(float); snr = snr.astype(float)
    time = mjd - mjd.min()
    
    return time, dm, width, snr, png, ifile

def interp_conv_temp(n, freq_mhz, conv_temp_k, fmin=100.0, fmax=190.0):
    f_new = np.linspace(fmin, fmax, int(n))
    t_new = np.interp(f_new, freq_mhz, conv_temp_k)
    return f_new, t_new


def burst_smin(freq, T_sys, A_phys, SNR_limit, W_burst,
               chan_BW, n_p=2, rfi_mask=None):
    """Compute single burst S_min with quadrature."""
    k_B = 1380
    chan_BW_Hz = chan_BW * 1e6
    if rfi_mask is not None:
        freq = freq[rfi_mask]
        T_sys = T_sys[rfi_mask]
    S_min_i = (T_sys * 2 * k_B) / (A_phys) * \
              (SNR_limit / np.sqrt(n_p * chan_BW_Hz * W_burst))
    S_min_total = 1.0 / np.sqrt(np.sum(1.0 / S_min_i**2))
    return S_min_total * 1000  # mJy

def main(): 
    
    args = fetch_args()
    
    if args.threshold is None:
        args.threshold = 0.0
    
    cands_files = glob.glob(f"{args.input}/**/*.cands", recursive=True)
    print('Number of candidates files:', len(cands_files))
    
    base_path = '/'.join(args.input.split('/')[0:-2])
    
    # Cat all the candidates
    time = []; dm = []; width = []; snr = []; png = []; ifile = []
    
    for cands_file in cands_files:
        time_, dm_, width_, snr_, png_, ifile_ = read_transientx(cands_file)
        
        time.extend(time_)
        dm.extend(dm_)
        width.extend(width_)
        snr.extend(snr_)
        png.extend(png_)
        ifile.extend(ifile_)
    
    print(f"Read in {len(time)} candidates from {cands_file}")
    
    if args.threshold:
        mask = snr > args.threshold
        snr = snr[mask]
        time = time[mask]
        width = width[mask]
        dm = dm[mask]
        png = png[mask]
        ifile = ifile[mask]
        
    snr = np.array(snr); time = np.array(time); width = np.array(width); dm = np.array(dm); png = np.array(png); ifile = np.array(ifile)
    print(f"Highest SNR candidate: {snr.max()}; ifile: {ifile[snr.argmax()]}; png: {png[snr.argmax()]}")
        
    nchans = 3296

    conv_temp_k = np.array([2278.8,1869.7,1558.3,1315.2,1122.0,965.53,838.23,732.6,644.45,570.1], dtype=float)
    freq_mhz = np.array([100.0, 110.0, 120.0, 130.0, 140.0, 150.0, 160.0, 170.0, 180.0, 190.0], dtype=float)
    A_phys = np.array([2400, 2048, 1422, 1152])
    A_phys_freq = np.array([100.0, 120.0, 150.0, 180.0], dtype=float)
    
    f_new, t_new = interp_conv_temp(nchans, freq_mhz, conv_temp_k)
    A_phys_interp = np.interp(f_new, A_phys_freq, A_phys)
    
    # convert width and snr to np.arrays
    width = np.array(width)
    snr = np.array(snr)
    fluxes = []
    
    for w, s in zip(width, snr):
        S_min = burst_smin(f_new, t_new, A_phys_interp, s, w*1e-3, chan_BW=0.2)
        fluxes.append(S_min)
    fluxes = np.array(fluxes)
    
    # plot a flux distribution
    fluxes_jy = fluxes * 1e-3

    # Define logarithmically spaced bins
    bins = np.logspace(
        np.log10(fluxes_jy.min()),
        np.log10(fluxes_jy.max()),
        50
    )

    fluxes_jy = fluxes * 1e-3
    fluxes_jy = fluxes_jy[fluxes_jy > 0]

    # Log-spaced bins
    bins = np.logspace(
        np.log10(fluxes_jy.min()),
        np.log10(fluxes_jy.max()),
        50
    )

    plt.figure(figsize=(8, 6))

    plt.hist(
        fluxes_jy,
        bins=bins,
        edgecolor='black',
        linewidth=1.2,
        facecolor='None'
    )

    plt.xscale('log')
    plt.yscale('log')

    # Major + minor ticks on log x-axis
    ax = plt.gca()
    ax.xaxis.set_major_locator(LogLocator(base=10.0))
    ax.xaxis.set_minor_locator(LogLocator(base=10.0, subs=np.arange(2, 10)*0.1))
    ax.tick_params(axis='x', which='major', length=7)
    ax.tick_params(axis='x', which='minor', length=4)
    
    # add more x ticks
    ax.set_xticks([0.001, 0.01, 0.1, 1, 10, 100])
    ax.get_xaxis().set_major_formatter(plt.ScalarFormatter())

    plt.xlim(fluxes_jy.min(), fluxes_jy.max())

    plt.xlabel('Flux (Jy)')
    plt.ylabel('Number of Bursts')
    plt.tight_layout()
    plt.savefig('flux_distribution.png')
        
if __name__ == "__main__":    main()