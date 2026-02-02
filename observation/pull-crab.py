import pandas as pd


def main():
    obs_df = pd.read_csv('./file-list/REALTA-Observation-Files.csv')
    print(obs_df.keys())
    print('Total observations: {}'.format(len(obs_df)))
    
    source_names = obs_df['source_name']
    str1 = 'crab'; str2 = 'B0531'; str3 = 'Crab'
    
    if any(source_names.str.contains(str1)) or any(source_names.str.contains(str2)) or any(source_names.str.contains(str3)):
        crab_df = obs_df[source_names.str.contains(str1) | source_names.str.contains(str2) | source_names.str.contains(str3)]
        # print(crab_df)
        crab_df.to_csv('./file-list/REALTA-Crab-Files.csv', index=False)
        
    print('Crab observations span from {} to {}'.format(
        crab_df['time_mjd'].min(), crab_df['time_mjd'].max()
    ))
    print('Total Crab observations: {}'.format(len(crab_df)))
    
if __name__ == "__main__":
    main()