bar() {
    i=$1
    count=$2
    printf "\r["
    if [[ "$i" > "0" ]]; then
        printf "%0.s#" $(seq 1 $i)
    fi
    if [[ "$i" < "$count" ]]; then
        printf "%0.s " $(seq 1 $((count-i)))
    fi
    printf "]"
}

run() {
    count=$(ls *.py | wc -l)
    i=0
    bar $i $count 1>&2
    for script in *.py; do
        t=$(python $script)
        printf "${t}_$script\n"
        i=$((i+1))
        bar $i $count 1>&2
    done
    printf "\n" 1>&2
}

R=$(run)
for line in $R; do
    echo $line
done | sort
