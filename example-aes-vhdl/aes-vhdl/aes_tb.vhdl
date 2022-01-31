-- This file is part of TOFU
--
-- TOFU is free software: you can redistribute it and/or modify
-- it under the terms of the GNU Lesser General Public License as published by
-- the Free Software Foundation, either version 3 of the License, or
-- (at your option) any later version.
--
-- This program is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
-- GNU Lesser General Public License for more details.
--
-- You should have received a copy of the GNU Lesser General Public License
-- along with this program.  If not, see <https://www.gnu.org/licenses/>.
--
-- Copyright 2022 (C)
-- Technical University of Munich
-- TUM Department of Electrical and Computer Engineering
-- Chair of Security in Information Technology
-- Written by the following authors: Michael Gruber, Filippos Sgouros

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use std.textio.all; 


entity test_enc is 
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
	
	constant clk_period : time := 10 ns;
	
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
		plaintext <= x"3243f6a8885a308d313198a2e0370734";
		key <= x"2b7e151628aed2a6abf7158809cf4f3c";
		-- Hold reset state for one cycle
		reset <= '1';	
		wait for clk_period * 1;
		reset <= '0';		
		wait for clk_period * 13;
		if (ciphertext = x"3925841d02dc09fbdc118597196a0b32") then
		    report "Successful encryption!";
		else
			report "Failed encryption";
			report "AES output should be: 3925841d02dc09fbdc118597196a0b32";
		end if;
		
		--------------------------------------------
		-- Initialize Inputs
		plaintext <= x"00000000000000000000000000000000";
		key <= x"00000000000000000000000000000000";
		-- Hold reset state for one cycle		
		reset <= '1';	
		wait for clk_period * 1;
		reset <= '0';		
		wait for clk_period * 13;		
		if (ciphertext = x"66E94BD4EF8A2C3B884CFA59CA342B2E") then
            report "Successful encryption!";
		else
			report "Failed encryption";
			report "AES output should be: 66E94BD4EF8A2C3B884CFA59CA342B2E";
		end if;
		
		key <= x"6465666768696a6b6c6d6e6f70717273";
		plaintext <= x"6D6BBC9C37845506835BB8050585D23F";
		reset <= '1';	
		wait for clk_period * 1;
		reset <= '0';
		wait for clk_period*13;			
		if (ciphertext = x"07213ebf1c88789ecd949252ea6b7528") then
            report "Successful encryption!";
		else
			report "Failed encryption";
			report "AES output should be: 07213ebf1c88789ecd949252ea6b7528";
		end if;
		wait;
	end process sim_proc;
	
	clk_proc : process is
	begin
		clk <= '0';
		wait for clk_period/2;
		clk <= '1';
		wait for clk_period/2;
	end process clk_proc;
	
end architecture simul_behavior;
