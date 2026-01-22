'''
Code Purpose: Find Crab files on REALTA and write their details to a .csv 
Author: Owen A. Johnson
'''
from glob import glob
import numpy as np
from astropy.coordinates import SkyCoord
import astropy.units as u
import your
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.transforms as mtransforms
import matplotlib.image as mpimg
from datetime import date
import argparse
from tqdm import tqdm
import pwd 
import os 
from zst_head_reader import zstheader
import struct

def get_args():
    parser = argparse.ArgumentParser(description="Find .fil, .fil.zst and .zst files on REALTA and write their details to a .csv")
    parser.add_argument('-i', '--input', type=str, default='./file-list/REALTA-Observation-files.txt',)
    parser.add_argument('-o', '--output', type=str, default='./file-list/REALTA-Observation-Files.csv',)
    return parser

def raj2deg(raj_hhmmss: float) -> float:
    """Convert SIGPROC src_raj in HHMMSS.S to degrees."""
    if raj_hhmmss is None:
        return float("nan")
    hh = int(raj_hhmmss // 10000)
    mm = int((raj_hhmmss - hh * 10000) // 100)
    ss = raj_hhmmss - hh * 10000 - mm * 100
    return (hh + mm / 60.0 + ss / 3600.0) * 15.0

def dej2deg(dej_ddmmss: float) -> float:
    """Convert SIGPROC src_dej in ±DDMMSS.S to degrees."""
    if dej_ddmmss is None:
        return float("nan")
    sign = -1.0 if dej_ddmmss < 0 else 1.0
    x = abs(dej_ddmmss)
    dd = int(x // 10000)
    mm = int((x - dd * 10000) // 100)
    ss = x - dd * 10000 - mm * 100
    return sign * (dd + mm / 60.0 + ss / 3600.0)

def main():
    args = get_args().parse_args()
    file_list = args.input

    fil_files = []; zst_files = []
    
    with open(file_list, 'r') as f: 
        lines = f.readlines()
        for line in lines: 
            if line.strip().endswith('.fil'):
                fil_files.append(line.strip())
            elif line.strip().endswith('.fil.zst'):
                zst_files.append(line.strip())
            
    
    print('Number of .fil files found:', len(fil_files))
    print('Number of .fil.zst files found:', len(zst_files))
    
    source_name = []; filename = []; ra_deg = []; dec_deg = []; l_deg = []; b_deg = []
    time_ut = []; time_mjd = []; size_gb = []; f_res = []; tsamp_arr = []; tobs = []; npols = []
    file_owners = [] 
    

    print('Reading .fil headers...')
    for fil in tqdm(fil_files):

        try:
            hdr = your.Your(fil).your_header
            header_ok = True
        except (struct.error, EOFError, ValueError, OSError, TypeError) as e:
            header_ok = False

        # ---- filename / ownership ----
        source_name.append(os.path.basename(fil).split('.')[0])
        filename.append(fil)

        file_owner = pwd.getpwuid(os.stat(fil).st_uid).pw_name
        file_owners.append(file_owner)

        if not header_ok:
            # fill dataframe with error markers
            npols.append("hdr error")
            tsamp_arr.append("hdr error")
            tobs.append("hdr error")
            f_res.append("hdr error")
            size_gb.append("hdr error")

            ra_deg.append("hdr error")
            dec_deg.append("hdr error")
            l_deg.append("hdr error")
            b_deg.append("hdr error")

            time_ut.append("hdr error")
            time_mjd.append("hdr error")
            continue
            
        
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

        time_ut.append(hdr.tstart_utc)
        time_mjd.append(hdr.tstart)
        
        try:
            coord = SkyCoord(ra=ra*u.deg, dec=dec*u.deg, frame='icrs')
            gal = coord.galactic

            ra_deg.append(ra)
            dec_deg.append(dec)
            l_deg.append(gal.l.deg)
            b_deg.append(gal.b.deg)

        except (TypeError, ValueError):
            ra_deg.append(np.nan)
            dec_deg.append(np.nan)
            l_deg.append(np.nan)
            b_deg.append(np.nan)
            continue
    
    print('Reading .fil.zst headers...')
    for zst in tqdm(zst_files):

        try:
            hdr = zstheader(zst)
            header_ok = True
        except Exception:
            hdr = {}
            header_ok = False

        source_name.append(os.path.basename(zst).split('.')[0])
        filename.append(zst)

        file_owner = pwd.getpwuid(os.stat(zst).st_uid).pw_name
        file_owners.append(file_owner)

        if not header_ok:
            npols.append("hdr error")
            tsamp_arr.append("hdr error")
            tobs.append("hdr error")
            f_res.append("hdr error")
            size_gb.append("hdr error")

            ra_deg.append("hdr error")
            dec_deg.append("hdr error")
            l_deg.append("hdr error")
            b_deg.append("hdr error")

            time_ut.append("hdr error")
            time_mjd.append("hdr error")

            continue

        # ---- header-backed values ----
        nchan = hdr.get("nchans")
        bits = hdr.get("nbits")
        tsamp = hdr.get("tsamp")

        nspec = np.nan

        npols.append(hdr.get("nifs", np.nan))

        tsamp_arr.append(tsamp)
        tobs.append(np.nan)  
        f_res.append(np.round(hdr.get("foff", np.nan) * 1e3, 5))

        size_gb.append(np.round(os.path.getsize(zst) / 1024**3, 2)) 
        # ---- coordinates ----
        ra = raj2deg(hdr.get("src_raj"))
        dec = dej2deg(hdr.get("src_dej"))

        time_mjd.append(hdr.get("tstart"))
        time_ut.append("hdr error")  

        try:
            coord = SkyCoord(ra=ra*u.deg, dec=dec*u.deg, frame='icrs')
            gal = coord.galactic

            ra_deg.append(ra)
            dec_deg.append(dec)
            l_deg.append(gal.l.deg)
            b_deg.append(gal.b.deg)

        except Exception:
            ra_deg.append("np.nan")
            dec_deg.append("np.nan")
            l_deg.append("np.nan")
            b_deg.append("np.nan")


    # ---------------------------
    # Build dataframe
    # ---------------------------
    data = {
        'source_name': source_name,
        'filename': filename,
        'file_owner': file_owners,
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
        'npol': npols
    }
    
    df = pd.DataFrame(data)
    out_csv = args.output
    df.to_csv(out_csv, index=False)
    
    # --- CSV with date for backup --- 
    today = date.today().strftime("%Y%m%d")
    dated_csv = out_csv.replace('.csv', f'_{today}.csv')
    df.to_csv(dated_csv, index=False)


if __name__ == "__main__":
    main()