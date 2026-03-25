import pandas as pd  
import argparse 
# import your 
from astropy.time import Time

def date2mjd(date):
    '''
    Input: i.e. 15/12/2011
    '''
    t = Time(date, format='iso', scale='tai')
    return t.mjd

def get_args():
    parser = argparse.ArgumentParser(description="Grab Jodrell Bank Ephermis for the crab data.")
    parser.add_argument("-f", help="Input filterbank path")
    parser.add_argument("-o", help="Output par file path", default="pulsar.par")
    parser.add_argument("-mjd", help="MJD of the observation", type=float, required=False)
    parser.add_argument("--print", action="store_true", help="Print f0 and DM content to stdout")
    return parser.parse_args()

# TODO: Scarp and convert to .csv
def main():
    args = get_args()
    df = pd.read_csv("../data/Crab_post2011.csv")
    
    if args.mjd is None:
        import your 
        header = your.Your(args.f).your_header
        obs_mjd = header.tstart 
        
    else:        
        obs_mjd = args.mjd
    
    print(obs_mjd)
    # find cloest MJD in the df that happens before the obs_mjd
    closest_mjd = df[df['MJD'] <= obs_mjd]['MJD'].max()
    
    print("Obs date:", Time(obs_mjd, format='mjd').iso)
    print("Closest MJD in Jodrell Bank Ephermis:", closest_mjd, "->", Time(closest_mjd, format='mjd').iso)
    row = df[df['MJD'] == closest_mjd].iloc[0]
    
    if args.print:
        print(f"F0: {row['nu_Hz']}")
        print(f"DM: {row['DM_pc_cm-3']}")
        return
    
    else: 
        par_content = f"""PSRJ            J0534+2200
RAJ             05:34:31.973                  5.000e-03
DECJ            +22:00:52.06                  6.000e-02
DM              {row['DM_pc_cm-3']}                        2.400e-04
PEPOCH          {closest_mjd}
F0              {row['nu_Hz']}                     1.000e-06
F1              {row['nudot_1e-15_s-2']}E-15                        1.000e-12
PMRA            -14.7                         8.000e-01
PMDEC           2.0                           8.000e-01
POSEPOCH        {closest_mjd}
DMEPOCH         {closest_mjd}
F2              1.1147E-20                    5.000e-24
EPHEM           DE405
RM              -45.44                        8.000e-02
F3              -2.73E-30                     4.000e-32
EPHVER          2
UNITS           TDB
    """
    
        print(par_content)
        with open(args.o, "w") as f:
            f.write(par_content)
            
        print(f"Par file saved to {args.o}")
            
if __name__ == "__main__":
    main()