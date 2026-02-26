import pandas as pd 
from astropy import units as u
from astropy.time import Time
from astropy.coordinates import GCRS, SkyCoord, get_sun
import matplotlib.pyplot as plt
import numpy as np
import scienceplots; plt.style.use(['science','no-latex'])

def sun_separation(coords, mjd):
    '''
    Calculate the separation between the target and the Sun at a given MJD.
    '''
    from astropy.coordinates import get_sun, EarthLocation, AltAz
    from astropy.time import Time
    
    t = Time(mjd, format="mjd")

    sun_gcrs = get_sun(t)                # GCRS(obstime=t)
    crab_gcrs = coords.transform_to(GCRS(obstime=t))

    return crab_gcrs.separation(sun_gcrs).deg

def main():
    crab_df = pd.read_csv('../REALTA-Crab-Files.csv')

    crab_df = crab_df[~crab_df['time_mjd'].str.contains('hdr error')]
    crab_mjd_arr = crab_df['time_mjd'].astype(float)
    
    print("N obs:", len(crab_mjd_arr))
    print("MJD min/max:", crab_mjd_arr.min(), crab_mjd_arr.max())
    print("Span (days):", crab_mjd_arr.max() - crab_mjd_arr.min())
    print("Span (years):", (crab_mjd_arr.max() - crab_mjd_arr.min()) / 365.25)
    print("Start date:", Time(crab_mjd_arr.min(), format="mjd").isot)
    print("End date  :", Time(crab_mjd_arr.max(), format="mjd").isot)

    

    crab = SkyCoord(ra=83.6331*u.deg, dec=22.0174*u.deg, frame="icrs")
    smooth_mjd_arr = np.linspace(crab_mjd_arr.min(), crab_mjd_arr.max(), 200)
    
    sun_separation_vec = np.array([sun_separation(crab, mjd) for mjd in crab_mjd_arr])
    sun_separation_smooth = np.array([sun_separation(crab, mjd) for mjd in smooth_mjd_arr])
 
    t_obs = Time(crab_mjd_arr, format="mjd")
    t_smooth = Time(smooth_mjd_arr, format="mjd")

    years_obs = t_obs.decimalyear
    years_smooth = t_smooth.decimalyear

    plt.figure(figsize=(9, 3))
    plt.scatter(years_obs, sun_separation_vec, alpha=0.5)
    plt.plot(years_smooth, sun_separation_smooth, color='grey', linestyle='--')
    plt.axhline(20, color='red', linestyle=':', label='limit')
    plt.xlabel('Year')
    plt.ylabel('Solar Seperation [deg]')
    plt.tight_layout()
    plt.savefig('crab_sun_separation.png')
    plt.savefig('crab_sun_separation.pdf')
    
    


        

if __name__ == "__main__":
    main()