

previous=`ls *112211_10pm*`

for seq in $previous
do
	new=`echo $seq | sed s/_10pm/_new/`
#	echo "diff $seq $new"
	diff $seq $new
done
