import argparse
import os 
import numpy as np
import your
from astropy.time import Time

def get_args():
    '''
    getting arguments... 
    '''
    parser = argparse.ArgumentParser(description='Slice transientX pulses into individual .fil files.')
    parser.add_argument('input_file', type=str, help='Path to the input .fil file.')
    parser.add_argument('-t', '--threshold', type=float, default=30, help='Threshold for SNR (default: 30).')
    parser.add_argument('-transx', '--transientx', help='Path to transientX .cands file.')
    parser.add_argument('-v', '--verbose', action='store_true', help='Print verbose output.')
    
    return parser.parse_args()

def read_transientx(cands_file):
    mjd, dm, width, snr, png, ifile = np.loadtxt(cands_file, usecols=(2, 3, 4, 5, 8, 10), unpack=True, dtype=str)
    mjd = mjd.astype(float); dm = dm.astype(float); width = width.astype(float); snr = snr.astype(float)
    time = mjd - mjd.min()
    time *= 24 * 3600
    
    return time, dm, width, snr, png, ifile

def main(): 
    args = get_args()
    
    fil_path = args.input_file
    threshold = args.threshold  
    transx_path = args.transientx
    
    print(f"Input .fil file: {fil_path}")
    print(f"TransientX .cands file: {transx_path}")
    print(f"SNR Threshold: {threshold}")
    
    # Read in the transientx file
    time, dm, width, snr, png, ifile = read_transientx(transx_path)
    mask = snr > threshold
    time = time[mask]; dm = dm[mask]; width = width[mask]; snr = snr[mask]; png = png[mask]; ifile = ifile[mask]
    
    order = np.lexsort((snr, time))
    time_s = time[order]
    snr_s  = snr[order]
    dm_s   = dm[order]
    width_s = width[order]
    png_s  = png[order]
    ifile_s = ifile[order]
    
    print(f"Number of candidates above threshold: {len(time)}")

    # Keep only the last occurrence of each unique time (== highest SNR due to sorting)
    last_of_time = np.r_[time_s[1:] != time_s[:-1], True]

    time  = time_s[last_of_time]
    snr   = snr_s[last_of_time]
    dm    = dm_s[last_of_time]
    width = width_s[last_of_time]
    png   = png_s[last_of_time]
    ifile = ifile_s[last_of_time]

    print("Number of unique times (kept highest S/N):", len(time))
    
    fil_obj = your.Your(fil_path)
    fil_hdr = fil_obj.your_header
    start_mjd = fil_hdr.tstart
    start_utc = Time(start_mjd, format='mjd').to_datetime()
    start_utc_str = start_utc.strftime('%Y-%m-%dT%H:%M')
    print(f"Filterbank start time (UTC): {start_utc_str}")
    
    output_dir = '/'.join(fil_path.split('/')[0:-1]) + '/sliced_pulses/'
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Output directory for sliced pulses: {output_dir}")
    
    if args.verbose: 
        print(f"\n{fil_hdr}\n")
        
    block_strt = 5; block_length = 55
        
    for i in range(len(time)):
        t_burst = int(time[i]/fil_hdr.tsamp)
    
        if args.verbose:
            print(f"Candidate {i+1}: Time={time[i]:.2f}s, DM={dm[i]:.2f}pc/cm^3, Width={width[i]:.2f}ms, SNR={snr[i]:.2f}, Burst Start Sample={t_burst}")
        
        if time[i] == 0:
            print("Candidate at time 0s, skipping...")
            continue
        
        nstrt=t_burst - block_strt
       
        if args.verbose: 
            fil_data = fil_obj.get_data(nstart=nstrt, nsamp=block_length)
            print(f"Extracted data shape: {fil_data.shape}, Time range: {nstrt*fil_hdr.tsamp:.2f}s to {(nstrt+block_length)*fil_hdr.tsamp:.2f}s\n")
            
        outname_str = f"Crab_{start_utc_str}_cand_{i}"
        
        writer_object = your.Writer(
            fil_obj,
            outdir=output_dir,
            outname=outname_str,
            nstart=nstrt,
            nsamp=block_length)
        
        writer_object.to_fil()
            
        
  
if __name__ == "__main__":
    main()