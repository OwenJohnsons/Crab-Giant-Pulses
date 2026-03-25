#!/bin/bash

path=$1

find "$path" -name "*P000.fil" -print0 | while IFS= read -r -d '' file; do
    start_time=$(date +%s)

    basepath=$(dirname "$file")
    basename="Crab"
    output_directory="${basepath}/transientx_output"
    skip_this_file=false

    cd "$basepath" || {
        echo "Could not cd into $basepath"
        continue
    }

    echo "Checking for existing .cands files in ${output_directory}"

    if compgen -G "${output_directory}/*.cands" > /dev/null; then
        while IFS= read -r -d '' cand_file; do
            echo "Checking whether $cand_file is associated with $file"

            ifile=$(awk 'NR==1 {print $NF}' "$cand_file")

            if [[ "$ifile" == "$file" ]]; then
                echo "A .cands file already exists for $file"
                skip_this_file=true
                break
            fi
        done < <(find "$output_directory" -maxdepth 1 -name "*.cands" -print0)
    fi

    if [[ "$skip_this_file" == true ]]; then
        echo "Skipping $file"
        continue
    fi

    mkdir -p "$output_directory"

    existing_8bit="${file%.fil}_8bit.fil"

    if [[ "$file" == *"_8bit.fil" ]]; then
        echo "Input file is already an 8-bit file."
        outname="$file"
    elif [[ -f "$existing_8bit" ]]; then
        echo "Existing 8-bit companion found."
        outname="$existing_8bit"
    else
        echo "No 8-bit version detected. Downsampling now."
        outname="$existing_8bit"
        digifil -b 8 "$file" -o "$outname" || {
            echo "digifil failed for $file"
            continue
        }
    fi

    echo "Running transientx_fil on $outname"

    transientx_fil -v -t 64 --iqr -l 10 --dms 56 --ddm 0.01 \
        --overlap 0.1 --ndm 100 --minw 0.003 --maxw 0.05 --thre 7.3 \
        -o "${output_directory}/${basename}" -f "$outname" -r 16 -k 3

    end_time=$(date +%s)
    elapsed_time=$((end_time - start_time))
    echo "Processing of $file completed in $elapsed_time seconds."
done