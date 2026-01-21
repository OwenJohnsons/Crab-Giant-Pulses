sudo find /mnt -type f \
  \( -iname "crab*.fil" -o -iname "crab*.fil.zst" \) \
  > crab_files.txt 2>/dev/null

