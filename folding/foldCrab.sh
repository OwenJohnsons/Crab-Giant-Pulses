path=$1

find "$path" -name '*P000.fil' -print0 | while IFS= read -r -d '' fil; do

  echo "" 
  echo "Processing $fil"
  header_mjd=$(header "$fil" | awk 'NR==15' | awk -F:  '{print $2}')
  echo "Header MJD: $header_mjd"  

  output=$(python ./grabJBephem.py -f "$fil" -o ./pulsar.par -mjd $header_mjd --print)
  DM=$(echo "$output" | grep "DM:" | awk '{print $2}')
  F0=$(echo "$output" | grep "F0:" | awk '{print $2}')
  echo "Using DM: $DM, F0: $F0"
  P=$(awk "BEGIN {print 1.0 / $F0}")
  echo "Calculated period: $P seconds"

  if [[ -f "${fil%.fil}_8bit.fil" ]]; then
    fil="${fil%.fil}_8bit.fil"
    echo "Found 8-bit version: $fil"
  else
    echo "No 8-bit version found, creating one: $fil"
    digifil -b 8 "$fil" "${fil%.fil}_8bit.fil"
    fil="${fil%.fil}_8bit.fil"
  fi

  basename=$(basename "$fil" .fil)
  basepath=$(dirname "$fil")
  echo "Base path: $basepath, Base name: $basename"

  folding_dir="$basepath/folding"
  mkdir -p "$folding_dir"
  cd "$folding_dir" || exit 1
  echo "Changed directory to: $folding_dir"

  # --- PRESTO RFI Excision ---
  if [[ -f "$folding_dir/${basename}_mask_rfifind.mask" ]]; then
    echo "Found existing rfifind mask: $folding_dir/${basename}_mask_rfifind.mask"
  else
    echo "No rfifind mask found, creating one: $folding_dir/${basename}_mask_rfifind.mask"
    rfifind -zapchan 0:250,3850:3903 -time 1.0 "$fil" -o "${basename}_mask"
  fi

  if [[ -f "$folding_dir/${basename}_0mask_rfifind.mask" ]]; then
    echo "Found existing rfifind mask: $folding_dir/${basename}_0mask_rfifind.mask"
  else
    echo "No 0dm rfifind mask found, creating one: $folding_dir/${basename}_0mask_rfifind.mask"
    rfifind -zapchan 0:250,3850:3903 -time 1.0 "$fil" -zerodm -mask "$folding_dir/${basename}_mask_rfifind.mask" -o "${basename}_0mask"
  fi

  # --- PRESTO Folding ---
  if compgen -G "$folding_dir/${basename}_0fold_lowfreq*.pfd" > /dev/null; then
    echo "Found existing low-frequency fold"
  else
    prepfold -noxwin -ignorechan 1600:3903 -f "$F0" -dm "$DM" "$fil" -ncpus 16 -mask "$folding_dir/${basename}_0mask_rfifind.mask" -zerodm -nsub 3904  -nopdsearch -ndmfact 4 -npfact 10 -n 256 -o "${basename}_0fold_lowfreq"
  fi

  if compgen -G "$folding_dir/${basename}_0fold_hifreq*.pfd" > /dev/null; then
    echo "Found existing high-frequency fold"
  else
    prepfold -noxwin -ignorechan 0:3000,3850:3903 -f "$F0" -dm "$DM" "$fil" -ncpus 16 -mask "$folding_dir/${basename}_0mask_rfifind.mask" -zerodm -nsub 3904  -nopdsearch -ndmfact 4 -npfact 10 -n 256 -o "${basename}_0fold_hifreq"
  fi

  if compgen -G "$folding_dir/${basename}_0fold_*.pfd" > /dev/null; then
    echo "Found existing full-frequency fold"
  else
    prepfold -noxwin -ignorechan 0:250,3850:3903 -f "$F0" -dm "$DM" "$fil" -ncpus 16 -mask "$folding_dir/${basename}_0mask_rfifind.mask" -zerodm -nsub 3904  -nopdsearch -ndmfact 4 -npfact 10 -n 256 -o "${basename}_0fold"
  fi

  # --- Making Weights for DSPSR --- 
  # python /home/soft/presto/bin/rfifind_stats.py $folding_dir/${basename}_0mask_rfifind.mask
  # paz -e zap -Z '0 250' -z 625 -z 757 -z 772 -z 1056 -z 1099 -z 1207 -z 1211 -Z '1224 1231' -z 1242 -z 1253 -z 1311 -Z '1350 1351' -Z '1359 1360' -z 1365 -z 1368 -z 1392 -Z '1414 1423' -z 1427 -z 1442 -z 1452 -Z '1776 1780' -Z '1782 1783' -Z '2085 2086' -z 2091 -z 2093 -Z '2312 2319' -z 2488 -z 2496 -z 2594 -z 2596 -z 2607 -z 2610 -Z '3362 3367' -Z '3372 3374' -Z '3453 3456' -Z '3850 3903'

  pfd_file=$(compgen -G "$folding_dir/${basename}_0fold_2*Cand.pfd.bestprof" | head -n 1)
  echo "Best profile file: $pfd_file"
  new_DM=$(cat "$pfd_file" | awk 'NR==15 {print $5}')
  new_F0=$(cat "$pfd_file" | awk 'NR==16 {print $5}')
  echo "Refined DM: $new_DM, Refined F0: $new_F0"
  
  length=30

  if [[ -f "${basename}_L${length}_folded.ar" ]]; then
    echo "Found existing folded archive: ${basename}_L${length}_folded.ar"
  else
    dspsr -L $length -D "$new_DM" -c "$(awk "BEGIN{print 1/$new_F0}")" -b 256 -A -O "${basename}_L${length}_folded" "$fil"
  fi

  ar_file=$folding_dir/${basename}_L${length}_folded.ar

  if [[ -f "${ar_file%.ar}.zap" ]]; then
    echo "archive already zapped: ${ar_file%.ar}.zap"
  else
    paz -e zap -Z '0 250' -z 625 -z 757 -z 772 -z 1056 -z 1099 -z 1207 -z 1211 -Z '1224 1231' -z 1242 -z 1253 -z 1311 -Z '1350 1351' -Z '1359 1360' -z 1365 -z 1368 -z 1392 -Z '1414 1423' -z 1427 -z 1442 -z 1452 -Z '1776 1780' -Z '1782 1783' -Z '2085 2086' -z 2091 -z 2093 -Z '2312 2319' -z 2488 -z 2496 -z 2594 -z 2596 -z 2607 -z 2610 -Z '3362 3367' -Z '3372 3374' -Z '3453 3456' -Z '3850 3903' $ar_file
  fi

  # echo "Finished processing $fil"
  break

done
