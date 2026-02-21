#!/bin/bash
path=$1

files=$(find "$path" -name "*8bit.fil" -print)
echo "Number of .fil files found:" $(echo "$files" | wc -l)

for file in $files; do

    start_time=$(date +%s)

    basename=$(basename "$file" .fil)
    basepath=$(dirname "$file")
    basename="Crab"

    cd "$basepath"

   

    output_directory="transientx_output"
    # current working 
    echo "${basepath}/${output_directory}/*.cand"

    # check if .cands file already exists
    cand_n=$(echo "${basepath}/${output_directory}/*.cands" | wc -l) 

    if compgen -G "${basepath}/${output_directory}/*.cands" > /dev/null; then
        echo "Cand file already exists for $file, skipping transientx_fil."
        continue
    fi

    if [ ! -d "$output_directory" ]; then
        mkdir "$output_directory"
    fi

    transientx_fil -v --iqr -l 10 --dms 56 --ddm 0.01 --overlap 0.1 --ndm 100 --minw 0.003 --maxw 0.05 --thre 7.3 -o ${output_directory}/${basename} -f ${file} -r 16 -k 3 

    end_time=$(date +%s)
    elapsed_time=$((end_time - start_time))
    echo "Processing of $file completed in $elapsed_time seconds."
done