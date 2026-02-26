#!/home/ojohnson/djarin/bin/python
import argparse
import glob as glob
import os as os
import numpy as np 
import scipy.stats as stats
import img2pdf
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import scienceplots 
import subprocess
plt.style.use(['science', 'no-latex'])

def fetch_args(): 
    '''
    Fetches the arguments from the command line 
    '''
    parser = argparse.ArgumentParser(description='Single Pulse Analysis Crab Gian Pulses.')
    parser.add_argument('-i', '--input', type=str, help='Input directory(s)', required=True)
    parser.add_argument('-t', '--threshold', type=float, help='Threshold for single pulse detection (default = 0)', required=False)
    parser.add_argument('-dm', '--dm', type=float, help='DM thresehold to plot (default = 0)', required=False)
    parser.add_argument('-pdf', '--pdf', help='Save as pdf (default = False)', required=False, action='store_true')
    parser.add_argument('-convert', '--convert', help='Use imagik convert function for pdf (default = False)', required=False, action='store_true')
    parser.add_argument('-n', '--nplots',type=int,help='Maximum number of highest-SNR pulse plots to save to PDF',required=False)
    
    return parser.parse_args()

def read_transientx(cands_file):
    mjd, dm, width, snr, png, ifile = np.loadtxt(cands_file, usecols=(2, 3, 4, 5, 8, 10), unpack=True, dtype=str)
    mjd = mjd.astype(float); dm = dm.astype(float); width = width.astype(float); snr = snr.astype(float)
    time = mjd - mjd.min()
    
    return time, dm, width, snr, png, ifile, mjd 

def marker_scaling(sig, threshold=10.0):
    """
    Scales the marker size based on S/N. Mimicing what is done by PRESTO in the same plot. 
    """
    min_size = 20; max_size = 1000 
        
    log_base = 30.0  # Higher values give a stronger effect
    marker_sizes = min_size + log_base * np.log1p(sig - threshold)
    
    return marker_sizes

def main(): 
    
    args = fetch_args()
    
    if args.threshold is None:
        args.threshold = 0.0
    if args.dm is None:
        args.dm = 0 
    
    # Read in the transientx file
    if ' ' in args.input:
        input_dirs = args.input.split(' ')
    else:
        input_dirs = [args.input]
   
    cands_files = []
    for d in input_dirs:
        cands_files.extend(glob.glob(f"{d}/**/*.cands", recursive=True))
    
    if len(cands_files) == 0:
        print('No candidates files found in {}'.format(args.input))
        exit(0)
        
    filterbank_files = []
    for d in input_dirs:
        filterbank_files.extend(glob.glob(f"{d}/**/*.fil", recursive=True))
        
    filterbank_files = [f.replace('_8bit.fil', '').replace('.fil', '') for f in filterbank_files]
    filterbank_files = list(set(filterbank_files))
    
    print('Number of candidates files:', len(cands_files))
    print('Number of filterbank files:', len(filterbank_files))
    
    base_path = '/'.join(args.input.split('/')[0:-2])
    
    # Cat all the candidates
    time = []; dm = []; width = []; snr = []; png = []; ifile = []; mjd = []
    
    for cands_file in cands_files:
        time_, dm_, width_, snr_, png_, ifile_, mjd_ = read_transientx(cands_file)
        
        time.extend(time_)
        dm.extend(dm_)
        width.extend(width_)
        snr.extend(snr_)
        png.extend(png_)
        ifile.extend(ifile_)
        mjd.extend(mjd_)
    
    print(f"Read in {len(time)} candidates from {cands_file}")

   # --- Convert to numpy arrays ---
    snr   = np.asarray(snr)
    dm    = np.asarray(dm)
    time  = np.asarray(time)
    width = np.asarray(width)
    png   = np.asarray(png)
    ifile = np.asarray(ifile)
    mjd   = np.asarray(mjd)

    # --- Build combined mask ---
    mask = np.ones_like(snr, dtype=bool)

    # S/N threshold
    if args.threshold is not None:
        mask &= snr > args.threshold

    # DM cut
    if args.dm is not None:
        mask &= dm > args.dm

    # Remove any entries containing '_replot'
    mask &= np.char.find(png.astype(str), '_replot') < 0

    # --- Apply mask once ---
    snr, time, width, dm, png, ifile, mjd = [
        arr[mask] for arr in (snr, time, width, dm, png, ifile, mjd)
    ]

    if snr.size == 0:
        print(f'⚠️ No single pulses found in {cands_file} for current setup')
        return

    # --- Sort by time then S/N ---
    order = np.lexsort((snr, time))
    snr_s, time_s, width_s, dm_s, png_s, ifile_s, mjd_s = [
        arr[order] for arr in (snr, time, width, dm, png, ifile, mjd)
    ]

    # --- Keep highest S/N per unique time ---
    keep = np.r_[time_s[1:] != time_s[:-1], True]

    snr, time, width, dm, png, ifile, mjd = [
        arr[keep] for arr in (snr_s, time_s, width_s, dm_s, png_s, ifile_s, mjd_s)
    ]

    print("Number of unique times (kept highest S/N):", time.size)

    # --- Order by descending S/N for plotting ---
    order = np.argsort(snr)[::-1]
    snr, time, width, dm, png, ifile, mjd = [
        arr[order] for arr in (snr, time, width, dm, png, ifile, mjd)
    ]
    
    print("--- Top 5 candidates ---")
    for t, d, w, s, p, i, m in zip(time[:5], dm[:5], width[:5], snr[:5], png[:5], ifile[:5], mjd[:5]):
        print(f"Time: {t:.2f} s, DM: {d:.2f} pc cm^-3, Width: {w:.2f} ms, S/N: {s:.2f}, png: {p}, ifile: {i}, MJD: {m}")
        
    print(f"\nSummary statistics: {len(cands_files)/len(filterbank_files)*100:.2f}% Processing Done | Total Pulses: {len(snr)}")
    print(f"S/N > 300: {(snr > 300).sum()}")
    print(f"S/N > 200: {(snr > 200).sum()}")
    print(f"S/N > 100: {(snr > 100).sum()}")
    print(f"S/N > 50: {(snr > 50).sum()}")
    print(f"S/N > 30: {(snr > 30).sum()}")
    print(f"S/N > 10: {(snr > 10).sum()}")
    print(f"Mean S/N: {snr.mean():.2f}, Std S/N: {snr.std():.2f}")
    
    filename = ifile[0].split('.')[0]
    
    # --- Plot Histogram of S/N --- Bins of 10 up to max S/N
    plt.figure(figsize=(6, 4))
    bins = np.arange(0, snr.max() + 10, 10)
    plt.hist(snr, bins=bins, color='black', histtype='step')
    plt.xlabel('S/N')
    plt.ylabel('Number of Pulses')
    plt.xlim(0, snr.max() + 10)
    plt.yscale('log')
    plt.savefig('Crab_GP_SNR_dist.png', dpi=300, bbox_inches='tight')
    
    # -- Events per hour vs MJD ---
    from datetime import datetime, timedelta

    # --- Convert MJD to UTC datetime ---
    def mjd_to_datetime(mjd):
        mjd_epoch = datetime(1858, 11, 17)  # MJD reference
        return np.array([mjd_epoch + timedelta(days=float(d)) for d in mjd])

    utc_times = mjd_to_datetime(mjd)

    # --- Bin by hour ---
    # Round down to the hour
    utc_hours = np.array([t.replace(minute=0, second=0, microsecond=0) for t in utc_times])

    # Count events per hour
    unique_hours, counts = np.unique(utc_hours, return_counts=True)

    # --- Plot ---
    plt.figure(figsize=(6, 4))
    plt.scatter(unique_hours, counts, color='black')
    plt.xlabel('UTC Time')
    plt.ylabel('Number of Pulses per Hour')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('Crab_GP_events_per_hour_UTC.png', dpi=300)


    # # Top row (3 plots)
    # ax1 = plt.subplot(gs[0, 0])
    # ax2 = plt.subplot(gs[0, 1])
    # ax3 = plt.subplot(gs[0, 2])
    # ax5 = plt.subplot(gs[0, 3])

    # # Bottom row (1 plot spanning 3 columns)
    # ax4 = plt.subplot(gs[1, :])

    # # Histogram of S/N
    # ax1.hist(snr, bins=100, color='black', histtype='step')
    # ax1.set_xlabel('S/N')
    # ax1.set_ylabel('Pulses')
    # ax1.set_xlim(snr.min(), snr.max())

    # # Histogram of DM
    # ax2.hist(dm, bins=60, color='black', histtype='step')
    # ax2.set_xlabel('DM (pc cm$^{-3}$)')
    # ax2.set_ylabel('Pulses')
    # ax2.set_xlim(dm.min(), dm.max())

    # # DM vs. S/N scatter plot
    # ax3.scatter(dm, snr, color='black', s=1)
    # ax3.axhline(snr.mean(), color='red', linestyle='--')
    # ax3.text(0.05, 0.95, 'Mean S/N: %.2f' % snr.mean(), transform=ax3.transAxes, verticalalignment='top')
    # ax3.set_xlabel('DM (pc cm$^{-3}$)')
    # ax3.set_ylabel('S/N')
    # ax3.set_xlim(dm.min(), dm.max())
    # ax3.set_ylim(snr.min(), snr.max())
    
    # # SNR vs. Width scatter plot
    # ax5.scatter(width, snr, color='black', s=1)
    # ax5.axhline(snr.mean(), color='red', linestyle='--')
    # ax5.text(0.05, 0.95, 'Mean S/N: %.2f' % snr.mean(), transform=ax5.transAxes, verticalalignment='top')
    # ax5.set_xlabel('Width (ms)')
    # ax5.set_ylabel('S/N')
    # ax5.set_xlim(width.min(), width.max())
    # ax5.set_ylim(snr.min(), snr.max())
    
    # # Time vs. DM scatter plot spanning full bottom row
    # t_fact = 24*60*60 # Convert days to seconds
    # time = time * t_fact
    # marker_sizes = snr**2
    
    # ax4.scatter(time, dm,  s = marker_sizes, edgecolor='black', facecolor='none', alpha=0.3)
    # ax4.set_xlabel('Time (s)')
    # ax4.set_ylabel('DM (pc cm$^{-3}$)')
    # ax4.set_xlim(0, float(time.max()))
    # ax4.set_ylim(dm.max(), dm.max())
    
    # plt.tight_layout()
    # output_file = os.path.join(args.input, f'{filename}_transx_t{args.threshold}_DM{args.dm}.png')
    # plt.savefig(output_file)
    # print(f"Saved summary plot to {output_file}")

    # Save pngs to a single pdf
    if args.pdf:
        os.chdir(base_path)
        
        snr_sort = np.argsort(snr)[::-1]
        png_sorted = png[snr_sort]
        png_sorted = [os.path.normpath(str(p)) for p in png_sorted]

        # Limit number of plots if requested
        if args.nplots is not None:
            png_sorted = png_sorted[:args.nplots]

        # Put your summary plot first
        png_sorted.insert(0, output_file)

        pdf_name = os.path.join(args.input, f'{filename}_transx_t{args.threshold}_DM{args.dm}.pdf')

        # Write PDF
        with open(pdf_name, "wb") as f:
            f.write(img2pdf.convert(png_sorted))

        print(f"Saved {pdf_name}")
        print(f"Included {len(png_sorted) - 1} pulse plots (highest S/N first)")


if __name__ == "__main__":
    main()