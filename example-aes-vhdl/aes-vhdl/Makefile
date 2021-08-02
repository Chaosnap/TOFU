clean:
	rm -f *test_enc.o
	rm -f test_enc
	rm -rf work;
		
test_enc: aes.vhdl aes_tb.vhdl
	mkdir -p work
	ghdl -i --workdir=work aes.vhdl aes_tb.vhdl
	ghdl -m --workdir=work test_enc
	
run: test_enc
	ghdl -r --workdir=work test_enc --vcd=work/aes_test.vcd --ieee-asserts=disable --stop-time=1000ns

test_aes:
	python test_aes.py