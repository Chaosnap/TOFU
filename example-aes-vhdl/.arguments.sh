#!/bin/bash

# the testbench requires key and plaintext as arguments split into 8 parts of 16 bits each
filename="testvector/testvector${1}.tv"
filecontent=$(cat $filename)
args=""

plaintext=$(echo "${filecontent}" | cut -f 1 -d " ")
key=$(echo "${filecontent}" | cut -f 2 -d " ")

# assemble plaintext arguments
for i in $(seq 0 7)
do
    pi=$(echo "${plaintext}" | cut -c $((1 + $i * 4))-$((($i + 1) * 4)))
    args="${args} -gp${i}=16#${pi}#"
done

# assemble key arguments
for i in $(seq 0 7)
do
    ki=$(echo "${key}" | cut -c $((1 + $i * 4))-$((($i + 1) * 4)))
    args="${args} -gk${i}=16#${ki}#"
done

echo $args