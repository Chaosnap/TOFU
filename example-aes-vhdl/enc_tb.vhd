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


architecture behavior of test_enc is
	component aes_enc
		port(
			clk        : in  std_logic;
			rst        : in  std_logic;
			key        : in  std_logic_vector(127 downto 0);
			plaintext  : in  std_logic_vector(127 downto 0);
			ciphertext : out std_logic_vector(127 downto 0);
			done       : out std_logic
		);		
	end component aes_enc;	
	-- Input signals
	signal clk : std_logic := '0';
	signal rst : std_logic := '0';
	signal plaintext : std_logic_vector(127 downto 0);
	signal key : std_logic_vector(127 downto 0);	
	
	-- Output signals
	signal done : std_logic;
	signal ciphertext : std_logic_vector(127 downto 0);	
	
	-- Clock period definition
	constant clk_period : time := 2 ms;
	
begin
	enc_inst : aes_enc
		port map(
			clk        => clk,
			rst        => rst,
			key        => key,
			plaintext  => plaintext,
			ciphertext => ciphertext,
			done       => done
		);	
	-- clock process definitions
	clk_process : process is
	begin
		clk <= '0';
		wait for clk_period/2;
		clk <= '1';
		wait for clk_period/2;
	end process clk_process;
	
	-- Simulation process
	sim_proc : process is
	begin
		-- Initialize Inputs
		--plaintext <= x"711816261678746845eff616e0724f9a";
		plaintext(15 downto 0)    <= std_logic_vector(to_unsigned(p7, 16));
		plaintext(31 downto 16)   <= std_logic_vector(to_unsigned(p6, 16));
		plaintext(47 downto 32)   <= std_logic_vector(to_unsigned(p5, 16));
		plaintext(63 downto 48)   <= std_logic_vector(to_unsigned(p4, 16));
		plaintext(79 downto 64)   <= std_logic_vector(to_unsigned(p3, 16));
		plaintext(95 downto 80)   <= std_logic_vector(to_unsigned(p2, 16));
		plaintext(111 downto 96)  <= std_logic_vector(to_unsigned(p1, 16));
		plaintext(127 downto 112) <= std_logic_vector(to_unsigned(p0, 16));

		--key <= x"2b7e151628aed2a6abf7158809cf4f3c";
		key(15 downto 0)    <= std_logic_vector(to_unsigned(k7, 16));
		key(31 downto 16)   <= std_logic_vector(to_unsigned(k6, 16));
		key(47 downto 32)   <= std_logic_vector(to_unsigned(k5, 16));
		key(63 downto 48)   <= std_logic_vector(to_unsigned(k4, 16));
		key(79 downto 64)   <= std_logic_vector(to_unsigned(k3, 16));
		key(95 downto 80)   <= std_logic_vector(to_unsigned(k2, 16));
		key(111 downto 96)  <= std_logic_vector(to_unsigned(k1, 16));
		key(127 downto 112) <= std_logic_vector(to_unsigned(k0, 16));

		rst <= '0';
		-- Hold reset state for one cycle		
		wait for clk_period * 1;
		rst <= '1';
		wait until done = '1';
		wait for clk_period;			
		--std.env.finish;
		report "finished";
	end process sim_proc;
	
end architecture behavior;