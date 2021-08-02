---------------------------------------------------------------------------------------------------
--Copyright (c) Technical University of Munich, Chair for Security in Information Technology.
--All Rights Reserved.
--For internal use only.
---------------------------------------------------------------------------------------------------
--Author: Michael Gruber m.gruber@tum.de, Florian Kasten
--Date:   30.06.2021
---------------------------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use std.textio.all; 


entity test_enc is 
    generic (
    	-- plaintext
        p0 : integer := 0;
        p1 : integer := 0;
        p2 : integer := 0;
        p3 : integer := 0;
        p4 : integer := 0;
        p5 : integer := 0;
        p6 : integer := 0;
        p7 : integer := 0;

        -- key
        k0 : integer := 0;
        k1 : integer := 0;
        k2 : integer := 0;
        k3 : integer := 0;
        k4 : integer := 0;
        k5 : integer := 0;
        k6 : integer := 0;
        k7 : integer := 0
    );
end test_enc;


architecture simul_behavior of test_enc is
	component simple_aes
		port(
			clk        : in  std_logic;
			reset      : in  std_logic;
			key        : in  std_logic_vector(127 downto 0);
			plaintext  : in  std_logic_vector(127 downto 0);
			ciphertext : out std_logic_vector(127 downto 0);
			done       : out std_logic
		);		
	end component simple_aes;	
	
	signal clk : std_logic := '0';
	signal reset : std_logic := '0';
	signal plaintext : std_logic_vector(127 downto 0);
	signal key : std_logic_vector(127 downto 0);	
	
	signal done : std_logic;
	signal ciphertext : std_logic_vector(127 downto 0);	
	
	constant clk_period : time := 2 ms;
	
begin
	enc_inst : simple_aes
		port map(
			clk        => clk,
			reset      => reset,
			key        => key,
			plaintext  => plaintext,
			ciphertext => ciphertext,
			done       => done
		);	
	
	-- Simulation process
	sim_proc : process is
	begin
		-- Initialize Inputs
		plaintext(15 downto 0)    <= std_logic_vector(to_unsigned(p7, 16));
		plaintext(31 downto 16)   <= std_logic_vector(to_unsigned(p6, 16));
		plaintext(47 downto 32)   <= std_logic_vector(to_unsigned(p5, 16));
		plaintext(63 downto 48)   <= std_logic_vector(to_unsigned(p4, 16));
		plaintext(79 downto 64)   <= std_logic_vector(to_unsigned(p3, 16));
		plaintext(95 downto 80)   <= std_logic_vector(to_unsigned(p2, 16));
		plaintext(111 downto 96)  <= std_logic_vector(to_unsigned(p1, 16));
		plaintext(127 downto 112) <= std_logic_vector(to_unsigned(p0, 16));

		key(15 downto 0)    <= std_logic_vector(to_unsigned(k7, 16));
		key(31 downto 16)   <= std_logic_vector(to_unsigned(k6, 16));
		key(47 downto 32)   <= std_logic_vector(to_unsigned(k5, 16));
		key(63 downto 48)   <= std_logic_vector(to_unsigned(k4, 16));
		key(79 downto 64)   <= std_logic_vector(to_unsigned(k3, 16));
		key(95 downto 80)   <= std_logic_vector(to_unsigned(k2, 16));
		key(111 downto 96)  <= std_logic_vector(to_unsigned(k1, 16));
		key(127 downto 112) <= std_logic_vector(to_unsigned(k0, 16));

		reset <= '1';
		-- Hold reset state for one cycle		
		wait for clk_period * 1;
		reset <= '0';
		wait until done = '1';
		wait for clk_period;			
		--std.env.finish;
		report "finished";
	end process sim_proc;
	
	clk_proc : process is
	begin
		clk <= '0';
		wait for clk_period/2;
		clk <= '1';
		wait for clk_period/2;
	end process clk_proc;
	
end architecture simul_behavior;
