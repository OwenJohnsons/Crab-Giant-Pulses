#!/bin/bash
path=$1

find /mnt/ucc4_data2/data/filterbanks/Crab/2026-02-04/transientx_output -name '*.ar' -print0 \
| xargs -0 -n 1000 /usr/bin/python /mnt/ucc4_data2/data/Owen/software/DM_phase/DM_phase_parallel_v2.py \
    --auto-header --auto-meta --csv --csv-flush 5 \
    --n-jobs 62 --parallel-backend processes \
    -DM_s 56.6 -DM_e 56.9 -DM_step 0.001