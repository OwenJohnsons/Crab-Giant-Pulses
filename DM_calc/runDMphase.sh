#!/bin/bash
archive=$1

psredit -m \
  -c "freq=149.902466" \
  -c "bw=-95.312256" \
  -c "ext:obsfreq=149.902466" \
  -c "ext:obsbw=-95.312256" \
  -c "ext:obsnchan=3904" \
  $archive 

# pam -m -E ./newpolyco.dat $archive
# pam -m -E pulsar.par --ephver tempo2 "$archive"

t_obs=$(psrstat -c length $archive | awk '{print $2}' | awk -F = '{print $2}')
echo "file length $t_obs seconds"

start_mjd=$(psrstat -c ext:stt_imjd $archive | awk '{print $2}' | awk -F = '{print $2}')
start_smjd=$(psrstat -c ext:stt_smjd $archive | awk '{print $2}' | awk -F = '{print $2}')
start_offs=$(psrstat -c ext:stt_offs $archive | awk '{print $2}' | awk -F = '{print $2}')
mjd=$(awk -v mjd="$start_mjd" \
           -v smjd="$start_smjd" \
           -v offs="$start_offs" \
           'BEGIN { printf "%.12f", mjd + (smjd + offs)/86400 }')

echo "start MJD: $mjd"

new_DM=$(python /mnt/ucc4_data2/data/Owen/software/DM_phase/DM_phase_parallel.py \
    --mjd $mjd --tobs $t_obs --csv \
    -no_plots -DM_s 56.6 -DM_e 56.9 -DM_step 0.001 "$archive" \
    | tee /dev/tty \
    | grep -oP 'DM:\s*\K[0-9.]+' )

# echo "new DM: $new_DM"
# pam -m -d $new_DM -D $new_DM $archive

# psrstat -c dm $archive

# ext:stt_imjd     Start MJD                                         61073
# ext:stt_smjd     Start second                                      70268
# ext:stt_offs     Start fractional second                           0.391150177001236
# old DM=56.73 