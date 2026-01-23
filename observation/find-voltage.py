import os 
import glob 
import argparse 
import pandas as pd 
from datetime import datetime 

def get_args():
    parser = argparse.ArgumentParser(description="Find .fil, .fil.zst and .zst files on REALTA and write their details to a .csv")
    parser.add_argument('-i', '--input', type=str, default='/mnt/ucc1_recording1/data/observations',)
    parser.add_argument('-o', '--output', type=str, default='./file-list/REALTA-Voltage-Files.csv',)
    return parser

def main(): 
    
    args = get_args().parse_args()
    input_dir = args.input
    output_csv = args.output
    hdr_mstr_path = '/mnt/ucc4_data2/data/David/hdrs'
    
    print('Searching for voltage files in:', input_dir)
    
    # grabbing folders that have voltages 
    voltage_files = []
    for root, dirs, files in os.walk(input_dir):
        udp_files = glob.glob(os.path.join(root, 'udp*.zst'))
        if udp_files:
            voltage_files.append((root, len(udp_files)))
            
    # find .sigprochdr file in subdirs of hdr master
    hdr_files = []; hdr_sources = [] 
    for root, dirs, files in os.walk(hdr_mstr_path):
        sigprochdr_files = glob.glob(os.path.join(root, '*.sigprochdr'))
        for f in sigprochdr_files:
            hdr_src = f.split('/')[-1].split('.sigprochdr')[0]
            
            hdr_files.append(f)
            hdr_sources.append(hdr_src)
    
    hdr_dict = dict(zip(hdr_sources, hdr_files)) # (path, source)
            
    # data frame arrays 
    targets = []; dates = []; mjds = []; file_counts = []; file_sizes = []; paths = []; hdr_paths = []
        
    # parse date and target 
    for line in voltage_files:
        path = line[0]
        basename = path.split('/')[-1]
        try: 
            dt = datetime.strptime(basename[0:14], "%Y%m%d%H%M%S")
            formatted_date = dt.strftime("%Y-%m-%d %H:%M:%S")
            mjd = dt.timestamp() / 86400.0 + 40587.0
            target = basename[14:]
            # print("%s - %s - %d files" % (formatted_date, target, line[1]))
            
            targets.append(target)
            dates.append(formatted_date)
            mjds.append(mjd)
            file_counts.append(line[1])
            paths.append(path)
            
            total_size = 0
            for file in glob.glob(os.path.join(path, 'udp*.zst')):
                total_size += os.path.getsize(file)
            file_sizes.append(total_size)
            
            # find corresponding hdr file
            if target in hdr_dict:
                hdr_paths.append(hdr_dict[target])
            else:
                hdr_paths.append('Unknown')
        
        except:  
            formatted_date = 'Unknown'
            print('Could not parse date for:', basename)
            
    # create dataframe
    df = pd.DataFrame({
        'Target': targets,
        'Date': dates,
        'MJD': mjds,
        'Lane Count': file_counts,
        'Total Size (GB)': [file_size / (1024**3) for file_size in file_sizes],
        'Path': paths,
        'Header Path': hdr_paths
    })
    
    # save to csv
    df.to_csv(output_csv, index=False)
    print('Saved voltage file list to:', output_csv)
        
    
if __name__ == "__main__":
    main()    