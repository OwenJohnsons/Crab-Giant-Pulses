obs_dir=$1
# basedir=$(dirname "$fb_path") 
template="/mnt/ucc4_data2/data/Owen/software/Crab-Giant-Pulses/lofar.template"
echo "Input Directory: $obs_didr"    

# grab .cands folder from transientx_output
cand_paths=$(find "$obs_dir"/transientx_output -type f -name "*fbf00000.cands")

if [ -z "$cand_paths" ]; then
    echo "No .cands files found in $obs_dir/transientx_output"
    exit 1
fi

for cand_path in $cand_paths; do
    echo "Found .cands file: $cand_path"
    cand_bf=$(awk '$6 > 100 && $5 < 45 {count++} END {print count}' $cand_path)
    echo "Number of candidates before replot: $cand_bf" 

    # --- define a new .cands file --- 
    new_cand_path="${cand_path%.cands}_filtered.cands"
    snr_cutoff=80
    awk -v snr_cutoff="$snr_cutoff" '$6 > snr_cutoff && $5 < 60' "$cand_path" > "$new_cand_path"
    cand_af=$(wc -l < "$new_cand_path")

    while [ "$cand_af" -eq 0 ] && [ "$snr_cutoff" -gt 0 ]; do
        snr_cutoff=$((snr_cutoff - 10))
        echo "No candidates found; retrying with SNR cutoff > $snr_cutoff"
        awk -v snr_cutoff="$snr_cutoff" '$6 > snr_cutoff && $5 < 60' "$cand_path" > "$new_cand_path"
        cand_af=$(wc -l < "$new_cand_path")
    done

    if [ "$cand_af" -eq 0 ]; then
        echo "No candidates found even after lowering SNR cutoff. Skipping this run."
        continue
    fi

    echo "Filtered .cands file created: $new_cand_path"
    echo "Number of candidates to recalculate SN for: $cand_af"

    fil_file=$(awk '{print $NF}' $new_cand_path | head -n 1)
    echo "Associated .fil file: $fil_file"

    obs_dir="$(dirname "$fil_file")"
    cd "$obs_dir" || exit 1
    echo "Changed directory to: $obs_dir"

    ar_count=$(find "$obs_dir"/transientx_output -type f -name "*.ar" | wc -l)
    # if equal or greater, then skip replotting
    if [ "$cand_bf" -le "$ar_count" ]; then
        echo "Number of candidates before replot ($cand_bf) is less than or equal to the number of .ar files ($ar_count). Skipping replotting."
        continue
    fi

    replot_fil -v -a -c --template "$template" --widthcutoff 0.060 --snrcutoff 100  --candfile "$new_cand_path" -f "$fil_file" 

done 


