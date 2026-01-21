'''
Code Purpose: Find Crab files on REALTA and write their details to a .csv 
Author: Owen A. Johnson
'''
import os 
import glob 
import subprocess
import pandas as pd 
from tqdm import tqdm
from pathlib import Path
import your



def main(): 
    file_list = './file-list/crab_files.txt'

    fil_files = []; zst_files = []
    with open(file_list, 'r') as f: 
        lines = f.readlines()
        for line in lines: 
            if line.strip().endswith('.fil'):
                fil_files.append(line.strip())
            elif line.strip().endswith('.fil.zst'):
                zst_files.append(line.strip())
            
    
    print('Number of Crab .fil files found:', len(fil_files))
    print('Number of Crab .fil.zst files found:', len(zst_files))
    
    for fil in fil_files:
        hdr = your.Your(fil).your_header

        source_name.append(hdr.filename.split('/')[-1].split('.')[0])
        filename.append(hdr.filename)
        
        nchan = hdr.native_nchans
        nspec = hdr.native_nspectra
        bits = hdr.native_nbits
        npols.append(hdr.npol)

        tsamp = hdr.tsamp
        tsamp_arr.append(tsamp)
        tobs.append((nspec * tsamp) / 60)  # minutes
        f_res.append(np.round(hdr.foff * 1e3, 5))  # kHz

        size_bits = nchan * nspec * (bits / 8)
        size_gb.append(np.round(size_bits / 1024**3, 2))

        # Coord stuff
        ra = hdr.ra_deg
        dec = hdr.dec_deg

        ra_deg.append(ra)
        dec_deg.append(dec)

        time_ut.append(hdr.tstart_utc)
        time_mjd.append(hdr.tstart)

        coord = SkyCoord(ra=ra*u.deg, dec=dec*u.deg, frame='icrs')
        gal = coord.galactic
        l_deg.append(gal.l.deg)
        b_deg.append(gal.b.deg)

    # ---------------------------
    # Build dataframe
    # ---------------------------
    data = {
        'source_name': source_name,
        'filename': filename,
        'ra_deg': ra_deg,
        'dec_deg': dec_deg,
        'l_deg': l_deg,
        'b_deg': b_deg,
        'time_utc': time_ut,
        'time_mjd': time_mjd,
        'size_gb': size_gb,
        'fres_khz': f_res,
        'tsamp': tsamp_arr,
        'tobs_min': tobs,
        'npol': npols,
        'station': [station]*len(filename)
    }
    
    df = pd.DataFrame(data)
    out_csv = './observation/crab_fil_files.csv'
    df.to_csv(out_csv, index=False)

if __name__ == "__main__":
    main()