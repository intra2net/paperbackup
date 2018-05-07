#!/bin/bash

# restore data backed up with paperbackup.py

# give one file containing all qrcodes as parameter

# Check $1 that the chunk sequence numbers are monotonicaly
# increasing and it ends with the expected count. Report
# any missing chunks.
check_sorted() {
	check_sorted_failed=false
	declare -a chunks
	IFS=$'\0' readarray -d '' chunks < $1
	#echo "count=${#chunks[@]}"
	IFS=
	i=1
	count=0
	failed=false
	for chunk in ${chunks[@]}; do
		OLDIFS=$IFS
		IFS="/" read -d ' ' sn cnt <<< "$chunk"
		if [[ "$sn" != "" && "$cnt" != "" ]]; then
			# strip leading zeros
			seqnum=$(sed -e "s/[0]*//" <<< "$sn")
			count=$(sed -e "s/[0]*//" <<< "$cnt")

			#echo "seqnum:$seqnum count:$count"
			if (( $i != $seqnum )); then
				echo "missing: $i"
				check_sorted_failed=true
				i=$((seqnum+1))
			else
				i=$((i+1))
			fi
		fi
		IFS=$OLDIFS
	done
	i=$((i-1))
	if (( $i < $count )); then
		echo "missing chunks $((i+1)) through $count at end"
		check_sorted_failed=true
	fi
	if (( $i > $count )); then
		echo "$((i-count)) extra chunks at end of the file"
		check_sorted_failed=true
	fi
}

SCANNEDFILE=$1

if [ -z "$SCANNEDFILE" ]; then
    echo "give one file containing all qrcodes as parameter"
    exit 1
fi

if ! [ -f "$SCANNEDFILE" ]; then
    echo "$SCANNEDFILE is not a file"
    exit 1
fi

if [ ! -x "/usr/bin/zbarimg" ]; then
    echo "/usr/bin/zbarimg missing"
    exit 2
fi

# zbarimg ends each scanned code with a newline

# each barcode content begins with ^<number><space>
# so convert that to \0<number><space>, so sort can sort on that
# then remove all \n\0<number><space> so we get the originial without newlines added

raw_file="$SCANNEDFILE".raw
/usr/bin/zbarimg --raw -Sdisable -Sqrcode.enable "$SCANNEDFILE" > $raw_file
zero_file="$SCANNEDFILE".zero
cat $raw_file | sed -e "s/\^/\x0/g" > $zero_file
sorted_file="$SCANNEDFILE".sorted
cat $zero_file | sort -z -n > $sorted_file
check_sorted $sorted_file
cat $sorted_file | sed ':a;N;$!ba;s/\n\x0[0-9]*\/[0-9]* //g;s/\x0[0-9]*\/[0-9]* //g;s/\n\x0//g'
if [ "$check_sorted_failed" == "false" ]; then
	rm $raw_file $zero_file $sorted_file
else
	echo "Error: in sequence numbers"
	exit 1
fi
