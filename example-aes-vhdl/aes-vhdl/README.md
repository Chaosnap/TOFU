## Simple AES in VHDL

This project is an implementation of the AES specification using VHDL in 400 lines of code. It uses 13 clk cycles to compute the final output.
It is designed to be used with tofu. For this reason it has a *first_byte* signal that is used to apply the sbox and is attacked through a Differential Power Analysis.