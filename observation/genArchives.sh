fb_path=$1
basedir=$(dirname "$fb_path") 
template="/mnt/ucc4_data2/data/Owen/software/Crab-Giant-Pulses/lofar.template"
echo "Basedir: $basedir"    

# grab .cands folder from transientx_output
cand_path=$(find "$basedir"/transientx_output -type f -name "*.cands" | head -n 1)

if [ -z "$cand_path" ]; then
    echo "No .cands folder found in transientx_output. Exiting."
    exit 1
fi

echo "Found .cands file: $cand_path"

cd $basedir 
replot_fil -a --template "$template" --snrcutoff 20 --candfile "$cand_path" -f "$fb_path" 
