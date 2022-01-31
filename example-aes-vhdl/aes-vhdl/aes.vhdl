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
-- Written by the following authors: Filippos Sgouros, Michael Gruber

-- predefine all types and helper functions here to be easy to follow the algorithm
-- consult the specification for the specifics of each of the functions
library IEEE; 
package aes_utils is
    use IEEE.STD_LOGIC_1164.ALL;
    use IEEE.NUMERIC_STD.ALL;
    type aes_word_array is array (natural range <>) of std_logic_vector(31 downto 0);
    type aes_byte_array is array (natural range <>) of std_logic_vector(7 downto 0);
    type s_box_array    is array (natural range <>) of unsigned(7 downto 0);
    type rcon_array     is array (natural range <>) of unsigned(31 downto 0);
    
    function rot_word (temp_in : std_logic_vector(31 downto 0) ) return std_logic_vector;
    function sub_word (temp_in : std_logic_vector(31 downto 0) ) return std_logic_vector;
    function rcon (arg : integer range 1 to 10) return std_logic_vector;
    
    function add_round_key(state : aes_word_array(3 downto 0);  w_in : aes_word_array(43 downto 0); round_in : integer range 0 to 12 ) return aes_word_array;
    function mix_columns(state : aes_word_array(3 downto 0)) return aes_word_array;
    function shift_rows(state : aes_word_array(3 downto 0)) return aes_word_array;
    
    constant s_box : s_box_array(0 to 255) := (
            x"63", x"7C", x"77", x"7B", x"F2", x"6B", x"6F", x"C5", x"30", x"01", x"67", x"2B", x"FE", x"D7", x"AB", x"76",
            x"CA", x"82", x"C9", x"7D", x"FA", x"59", x"47", x"F0", x"AD", x"D4", x"A2", x"AF", x"9C", x"A4", x"72", x"C0",
            x"B7", x"FD", x"93", x"26", x"36", x"3F", x"F7", x"CC", x"34", x"A5", x"E5", x"F1", x"71", x"D8", x"31", x"15",
            x"04", x"C7", x"23", x"C3", x"18", x"96", x"05", x"9A", x"07", x"12", x"80", x"E2", x"EB", x"27", x"B2", x"75",
            x"09", x"83", x"2C", x"1A", x"1B", x"6E", x"5A", x"A0", x"52", x"3B", x"D6", x"B3", x"29", x"E3", x"2F", x"84",
            x"53", x"D1", x"00", x"ED", x"20", x"FC", x"B1", x"5B", x"6A", x"CB", x"BE", x"39", x"4A", x"4C", x"58", x"CF",
            x"D0", x"EF", x"AA", x"FB", x"43", x"4D", x"33", x"85", x"45", x"F9", x"02", x"7F", x"50", x"3C", x"9F", x"A8",
            x"51", x"A3", x"40", x"8F", x"92", x"9D", x"38", x"F5", x"BC", x"B6", x"DA", x"21", x"10", x"FF", x"F3", x"D2",
            x"CD", x"0C", x"13", x"EC", x"5F", x"97", x"44", x"17", x"C4", x"A7", x"7E", x"3D", x"64", x"5D", x"19", x"73",
            x"60", x"81", x"4F", x"DC", x"22", x"2A", x"90", x"88", x"46", x"EE", x"B8", x"14", x"DE", x"5E", x"0B", x"DB",
            x"E0", x"32", x"3A", x"0A", x"49", x"06", x"24", x"5C", x"C2", x"D3", x"AC", x"62", x"91", x"95", x"E4", x"79",
            x"E7", x"C8", x"37", x"6D", x"8D", x"D5", x"4E", x"A9", x"6C", x"56", x"F4", x"EA", x"65", x"7A", x"AE", x"08",
            x"BA", x"78", x"25", x"2E", x"1C", x"A6", x"B4", x"C6", x"E8", x"DD", x"74", x"1F", x"4B", x"BD", x"8B", x"8A",
            x"70", x"3E", x"B5", x"66", x"48", x"03", x"F6", x"0E", x"61", x"35", x"57", x"B9", x"86", x"C1", x"1D", x"9E",
            x"E1", x"F8", x"98", x"11", x"69", x"D9", x"8E", x"94", x"9B", x"1E", x"87", x"E9", x"CE", x"55", x"28", x"DF",
            x"8C", x"A1", x"89", x"0D", x"BF", x"E6", x"42", x"68", x"41", x"99", x"2D", x"0F", x"B0", x"54", x"BB", x"16"
        );
        
    constant mul_2_const : s_box_array(0 to 255) := (
            x"00", x"02", x"04", x"06", x"08", x"0a", x"0c", x"0e", x"10", x"12", x"14", x"16", x"18", x"1a", x"1c", x"1e",
            x"20", x"22", x"24", x"26", x"28", x"2a", x"2c", x"2e", x"30", x"32", x"34", x"36", x"38", x"3a", x"3c", x"3e",
            x"40", x"42", x"44", x"46", x"48", x"4a", x"4c", x"4e", x"50", x"52", x"54", x"56", x"58", x"5a", x"5c", x"5e",
            x"60", x"62", x"64", x"66", x"68", x"6a", x"6c", x"6e", x"70", x"72", x"74", x"76", x"78", x"7a", x"7c", x"7e",
            x"80", x"82", x"84", x"86", x"88", x"8a", x"8c", x"8e", x"90", x"92", x"94", x"96", x"98", x"9a", x"9c", x"9e",
            x"a0", x"a2", x"a4", x"a6", x"a8", x"aa", x"ac", x"ae", x"b0", x"b2", x"b4", x"b6", x"b8", x"ba", x"bc", x"be",
            x"c0", x"c2", x"c4", x"c6", x"c8", x"ca", x"cc", x"ce", x"d0", x"d2", x"d4", x"d6", x"d8", x"da", x"dc", x"de",
            x"e0", x"e2", x"e4", x"e6", x"e8", x"ea", x"ec", x"ee", x"f0", x"f2", x"f4", x"f6", x"f8", x"fa", x"fc", x"fe",
            x"1b", x"19", x"1f", x"1d", x"13", x"11", x"17", x"15", x"0b", x"09", x"0f", x"0d", x"03", x"01", x"07", x"05",
            x"3b", x"39", x"3f", x"3d", x"33", x"31", x"37", x"35", x"2b", x"29", x"2f", x"2d", x"23", x"21", x"27", x"25",
            x"5b", x"59", x"5f", x"5d", x"53", x"51", x"57", x"55", x"4b", x"49", x"4f", x"4d", x"43", x"41", x"47", x"45",
            x"7b", x"79", x"7f", x"7d", x"73", x"71", x"77", x"75", x"6b", x"69", x"6f", x"6d", x"63", x"61", x"67", x"65",
            x"9b", x"99", x"9f", x"9d", x"93", x"91", x"97", x"95", x"8b", x"89", x"8f", x"8d", x"83", x"81", x"87", x"85",
            x"bb", x"b9", x"bf", x"bd", x"b3", x"b1", x"b7", x"b5", x"ab", x"a9", x"af", x"ad", x"a3", x"a1", x"a7", x"a5",
            x"db", x"d9", x"df", x"dd", x"d3", x"d1", x"d7", x"d5", x"cb", x"c9", x"cf", x"cd", x"c3", x"c1", x"c7", x"c5",
            x"fb", x"f9", x"ff", x"fd", x"f3", x"f1", x"f7", x"f5", x"eb", x"e9", x"ef", x"ed", x"e3", x"e1", x"e7", x"e5"
        );
    constant mul_3_const : s_box_array(0 to 255) := (
            x"00", x"03", x"06", x"05", x"0c", x"0f", x"0a", x"09", x"18", x"1b", x"1e", x"1d", x"14", x"17", x"12", x"11",
            x"30", x"33", x"36", x"35", x"3c", x"3f", x"3a", x"39", x"28", x"2b", x"2e", x"2d", x"24", x"27", x"22", x"21",
            x"60", x"63", x"66", x"65", x"6c", x"6f", x"6a", x"69", x"78", x"7b", x"7e", x"7d", x"74", x"77", x"72", x"71",
            x"50", x"53", x"56", x"55", x"5c", x"5f", x"5a", x"59", x"48", x"4b", x"4e", x"4d", x"44", x"47", x"42", x"41",
            x"c0", x"c3", x"c6", x"c5", x"cc", x"cf", x"ca", x"c9", x"d8", x"db", x"de", x"dd", x"d4", x"d7", x"d2", x"d1",
            x"f0", x"f3", x"f6", x"f5", x"fc", x"ff", x"fa", x"f9", x"e8", x"eb", x"ee", x"ed", x"e4", x"e7", x"e2", x"e1",
            x"a0", x"a3", x"a6", x"a5", x"ac", x"af", x"aa", x"a9", x"b8", x"bb", x"be", x"bd", x"b4", x"b7", x"b2", x"b1",
            x"90", x"93", x"96", x"95", x"9c", x"9f", x"9a", x"99", x"88", x"8b", x"8e", x"8d", x"84", x"87", x"82", x"81",
            x"9b", x"98", x"9d", x"9e", x"97", x"94", x"91", x"92", x"83", x"80", x"85", x"86", x"8f", x"8c", x"89", x"8a",
            x"ab", x"a8", x"ad", x"ae", x"a7", x"a4", x"a1", x"a2", x"b3", x"b0", x"b5", x"b6", x"bf", x"bc", x"b9", x"ba",
            x"fb", x"f8", x"fd", x"fe", x"f7", x"f4", x"f1", x"f2", x"e3", x"e0", x"e5", x"e6", x"ef", x"ec", x"e9", x"ea",
            x"cb", x"c8", x"cd", x"ce", x"c7", x"c4", x"c1", x"c2", x"d3", x"d0", x"d5", x"d6", x"df", x"dc", x"d9", x"da",
            x"5b", x"58", x"5d", x"5e", x"57", x"54", x"51", x"52", x"43", x"40", x"45", x"46", x"4f", x"4c", x"49", x"4a",
            x"6b", x"68", x"6d", x"6e", x"67", x"64", x"61", x"62", x"73", x"70", x"75", x"76", x"7f", x"7c", x"79", x"7a",
            x"3b", x"38", x"3d", x"3e", x"37", x"34", x"31", x"32", x"23", x"20", x"25", x"26", x"2f", x"2c", x"29", x"2a",
            x"0b", x"08", x"0d", x"0e", x"07", x"04", x"01", x"02", x"13", x"10", x"15", x"16", x"1f", x"1c", x"19", x"1a"
        );
        
    function mul_2(arg : std_logic_vector(7 downto 0)) return std_logic_vector;
    function mul_3(arg : std_logic_vector(7 downto 0)) return std_logic_vector;
        
    function mix_single_col(arg : std_logic_vector(31 downto 0); i : integer range 0 to 3) return std_logic_vector;
end aes_utils;

package body aes_utils is
    
    --rot_word
    function rot_word (temp_in : std_logic_vector(31 downto 0) ) return std_logic_vector is
    begin
        return temp_in(23 downto 16) & temp_in(15 downto 8) & temp_in(7 downto 0) & temp_in(31 downto 24);
    end function rot_word;
    
    --sub_word
    function sub_word (temp_in : std_logic_vector(31 downto 0) ) return std_logic_vector is
        variable s1 : std_logic_vector (7 downto 0);
        variable s2 : std_logic_vector (7 downto 0);
        variable s3 : std_logic_vector (7 downto 0);
        variable s4 : std_logic_vector (7 downto 0);
    
    begin
        s1 := std_logic_vector(s_box(to_integer(unsigned(temp_in(31 downto 24)))));
        s2 := std_logic_vector(s_box(to_integer(unsigned(temp_in(23 downto 16)))));
        s3 := std_logic_vector(s_box(to_integer(unsigned(temp_in(15 downto 8)))));
        s4 := std_logic_vector(s_box(to_integer(unsigned(temp_in(7 downto 0)))));
        return s1 & s2 & s3 & s4;
    end function sub_word;
    
    --rcon
    function rcon (arg : integer range 1 to 10) return std_logic_vector is
        constant rcon_sbox : rcon_array(1 to 10) := (
            x"01000000", x"02000000", x"04000000", x"08000000", x"10000000", 
            x"20000000", x"40000000", x"80000000", x"1B000000", x"36000000"
        );
    begin
        return std_logic_vector(rcon_sbox(arg));
    end function rcon;
    
    --add_round_key
    function add_round_key(state : aes_word_array(3 downto 0); w_in : aes_word_array(43 downto 0); round_in: integer range 0 to 12) return aes_word_array is
        variable output_var: aes_word_array(3 downto 0);
    begin
        output_var(0) := state(0) xor w_in(round_in*4);
        output_var(1) := state(1) xor w_in(round_in*4 + 1);
        output_var(2) := state(2) xor w_in(round_in*4 + 2);
        output_var(3) := state(3) xor w_in(round_in*4 + 3);
        return output_var;
    end function add_round_key;
    
    --mix_columns
    function mix_columns(state : aes_word_array(3 downto 0)) return aes_word_array is
        variable output_var: aes_word_array(3 downto 0);
    begin
       for i in 0 to 3 loop
        output_var(i) := mix_single_col(state(i), 0) & mix_single_col(state(i), 1) & mix_single_col(state(i), 2) & mix_single_col(state(i), 3);
       end loop;
       return output_var;
    end function mix_columns;
    
    --shift_rows
    function shift_rows(state : aes_word_array(3 downto 0)) return aes_word_array is
        variable output_var  : aes_word_array(3 downto 0);
        variable hold_temp   : std_logic_vector(127 downto 0);
        variable output_temp : std_logic_vector(127 downto 0);
    begin
        hold_temp(127 downto 96) := state(3);
        hold_temp(95 downto 64)  := state(2);
        hold_temp(63 downto 32)  := state(1);
        hold_temp(31 downto 0)   := state(0);
    
        for i in 0 to 3 loop
            output_temp(127 - 32*i downto 120 -32*i) := hold_temp(127 - 32*i downto 120 -32*i);
            output_temp(119 - 32*i downto 112 -32*i) := hold_temp(119 - 32*((i+3) mod 4) downto 112 -32*((i+3) mod 4));
            output_temp(111 - 32*i downto 104 -32*i) := hold_temp(111 - 32*((i+2) mod 4) downto 104 -32*((i+2) mod 4));
            output_temp(103 - 32*i downto 96 -32*i)  := hold_temp(103 - 32*((i+1) mod 4) downto 96 -32*((i+1) mod 4));
        end loop; 
    
        output_var(3) := output_temp(127 downto 96);
        output_var(2) := output_temp(95 downto 64);
        output_var(1) := output_temp(63 downto 32);
        output_var(0) := output_temp(31 downto 0);
        return output_var;
    end function shift_rows;
    
    -- mul_2 and mul_3 needed for mix_columns
    function mul_2(arg : std_logic_vector(7 downto 0)) return std_logic_vector is
    begin
        return std_logic_vector(mul_2_const(to_integer(unsigned(arg))));
    end function mul_2;
    
    function mul_3(arg : std_logic_vector(7 downto 0)) return std_logic_vector is
    begin
        return std_logic_vector(mul_3_const(to_integer(unsigned(arg))));
    end function mul_3;
    
    --mul_i unifying the above
    function mix_single_col(arg : std_logic_vector(31 downto 0); i : integer range 0 to 3) return std_logic_vector is
    begin
        if i=0 then
            return mul_2(arg(31 downto 24)) xor mul_3(arg(23 downto 16)) xor arg(15 downto 8)        xor arg(7 downto 0);
        elsif i=1 then
            return arg(31 downto 24)        xor mul_2(arg(23 downto 16)) xor mul_3(arg(15 downto 8)) xor arg(7 downto 0);
        elsif i=2 then
            return arg(31 downto 24)        xor arg(23 downto 16)        xor mul_2(arg(15 downto 8)) xor mul_3(arg(7 downto 0));
        else
            return mul_3(arg(31 downto 24)) xor arg(23 downto 16)        xor arg(15 downto 8)        xor mul_2(arg(7 downto 0));
        end if;
    end function mix_single_col;
end package body aes_utils;

-- 8-bit lame entity that simply stores the output of the sbox
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
entity sbox_byte is
    port(
        input_byte : in std_logic_vector(7 downto 0);
        output_byte : out std_logic_vector(7 downto 0)
    );
end sbox_byte;

architecture a_simple_byte of sbox_byte is
begin
    output_byte <= input_byte;
end architecture;

-- a 128-bit simple entity that applies the sbox
-- here is the signal used for the dpa
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;
library work;
use work.aes_utils.all;
entity sub_bytes_ent is
    port (
           input_text : in aes_word_array(3 downto 0);
           output_text : out std_logic_vector(127 downto 0)
          );
end sub_bytes_ent;

architecture a_simple_sbox of sub_bytes_ent is
    
    component sbox_byte is
    port(
        input_byte : in std_logic_vector(7 downto 0);
        output_byte : out std_logic_vector(7 downto 0)
    );
    end component;
    
    signal temp : std_logic_vector(127 downto 0);
    signal first_byte : std_logic_vector(7 downto 0);
begin
      -- conversion between std_logic_vector array and aes_word_array
      -- is redundant but necessary so that the vcd picks this signal up and handles it
      -- then it is visible to the ntofu parser.
      temp(127 downto 96) <= sub_word(input_text(0));
      temp(95 downto 64)  <= sub_word(input_text(1));
      temp(63 downto 32)  <= sub_word(input_text(2));
      temp(31 downto 0)   <= sub_word(input_text(3));
      
      gen : for i in 0 to 15 generate
            sbox_inst : sbox_byte port map(
                                        input_byte  => temp((i + 1)*8 - 1 downto i*8),
                                        output_byte => output_text((i + 1)*8 - 1 downto i*8)
                                       );
      end generate gen;
            
      --output_text(119 downto 0) <= temp(119 downto 0);
      --first_byte <= temp(127 downto 120);
      --output_text(127 downto 120) <= first_byte;
      
end architecture;

-- a 128-bit aes register which stores the result
-- of each of the 10 rounds. The register is 'temp'
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;
library work;
use work.aes_utils.all;
entity register_128 is
    port (
           clk : in std_logic;
           in_plaintext     : in aes_word_array(3 downto 0);
           exp_key          : in aes_word_array(43 downto 0);
           aes_round_sig    : in unsigned(3 downto 0);
           sub_bytes_result : in std_logic_vector(127 downto 0);
           q : out aes_word_array(3 downto 0)
          );
end register_128;

architecture a_simple_reg of register_128 is
begin
    process(clk)
        -- temp is synthesized as a register. This is key for the program to
        -- retain the final result unless the whole program is reset
        variable temp : aes_word_array(3 downto 0);
        variable sbox_result_converted : aes_word_array(3 downto 0);
    begin
        if clk'EVENT and clk='1' then
            
            -- conversion between std_logic_vector array and aes_word_array
            -- is redundant but necessary so that the vcd picks this signal up and handles it
            -- then it is visible to the ntofu parser.
            sbox_result_converted(0) := sub_bytes_result(127 downto 96);
            sbox_result_converted(1) := sub_bytes_result(95 downto 64);
            sbox_result_converted(2) := sub_bytes_result(63 downto 32);
            sbox_result_converted(3) := sub_bytes_result(31 downto 0);
        
            if aes_round_sig = 0 then
                temp := add_round_key(in_plaintext, exp_key, to_integer(aes_round_sig));
            elsif aes_round_sig < 10 then
                temp := add_round_key(mix_columns(shift_rows(sbox_result_converted)), exp_key, to_integer(aes_round_sig));
            elsif aes_round_sig = 10 then
                temp := add_round_key(shift_rows(sbox_result_converted), exp_key, to_integer(aes_round_sig));
            else
            end if;
            q <= temp;
        end if;
    end process;
    
end architecture;

-- expand keys as a separate entity
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;
library work;
use work.aes_utils.all;
entity expand_keys is
    port (
           key_pure: in std_logic_vector(127 downto 0);
          expanded_keys: out aes_word_array(43 downto 0)
          );
end expand_keys;

architecture no_clk of expand_keys is
    signal key_in : aes_byte_array(15 downto 0);
    signal temp : aes_word_array(4 to 43);
    signal w: aes_word_array(43 downto 0);
begin
    -- format key
    copy_key: for i in 0 to 15 generate
        key_in(15-i) <= key_pure(8*(i+1)-1 downto 8*i);
    end generate;
    
    -- the fireset element is the key itself
    w(0) <= key_in(0) & key_in(1) & key_in(2) & key_in(3);
    w(1) <= key_in(4) & key_in(5) & key_in(6) & key_in(7);
    w(2) <= key_in(8) & key_in(9) & key_in(10) & key_in(11);
    w(3) <= key_in(12) & key_in(13) & key_in(14) & key_in(15);
    
    -- this follows the aes algorithm specification 1:1 unrolled
    exp_key: for i in 4 to 43 generate
        exp_modded: if i mod 4 /= 0 generate
            temp(i) <= w(i-1);
        end generate;
        exp_no_mod: if i mod 4 = 0 generate
            temp(i) <= sub_word(rot_word(w(i-1))) xor rcon(i/4);
        end generate;
        w(i) <= w(i-4) xor temp(i);
    end generate; 
    expanded_keys <= w;
end architecture;


-- aes round as a separate entity
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;
library work;
use work.aes_utils.all;
entity aes_round is
    port (clk : in STD_LOGIC;
          in_plaintext   : in aes_word_array(3 downto 0);
          exp_key         : in aes_word_array(43 downto 0);
          aes_round_sig  : in unsigned(3 downto 0);
          out_ciphertext : out aes_word_array(3 downto 0)
          );
end aes_round;

architecture multi_cycle_round of aes_round is 
    component sub_bytes_ent is
    port (
           input_text : in aes_word_array(3 downto 0);
           output_text : out std_logic_vector(127 downto 0)
          );
    end component;
    component register_128 is
    port (
           clk : in std_logic;
           in_plaintext     : in aes_word_array(3 downto 0);
           exp_key          : in aes_word_array(43 downto 0);
           aes_round_sig    : in unsigned(3 downto 0);
           sub_bytes_result : in std_logic_vector(127 downto 0);
           q : out aes_word_array(3 downto 0)
          );
    end component;
    signal sub_bytes_result :std_logic_vector(127 downto 0);
    signal temp_signal : aes_word_array(3 downto 0);
begin
    --unnecessary complexity but needed for the dpa to work correctly
    sub_bytes_inst : sub_bytes_ent port map (temp_signal, sub_bytes_result);
    aes_register_inst : register_128 port map (clk, in_plaintext, exp_key, aes_round_sig, sub_bytes_result, temp_signal);
    
    out_ciphertext <= temp_signal;
end architecture;


-- final combined architecture
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;
library work;
use work.aes_utils.all;
entity simple_aes is
    Port ( clk : in STD_LOGIC;
           reset : in std_logic;
           done: out std_logic := '0';
           key        : in  std_logic_vector(127 downto 0);
		   plaintext  : in  std_logic_vector(127 downto 0);
		   ciphertext : out std_logic_vector(127 downto 0) 
           );
end simple_aes;

architecture multi_cycle of simple_aes is
    signal in_key : std_logic_vector(127 downto 0);
    signal in_plaintext : aes_word_array(3 downto 0);
    signal out_ciphertext : aes_word_array(3 downto 0);
    signal expanded_key : aes_word_array(43 downto 0);
    signal aes_round_sig : unsigned(3 downto 0);
    
    component expand_keys is
    port (
           key_pure: in std_logic_vector(127 downto 0);
          expanded_keys: out aes_word_array(43 downto 0)
          );
    end component;
    
    component aes_round is
    port (clk : in STD_LOGIC;
          in_plaintext : in aes_word_array(3 downto 0);
          exp_key         : in aes_word_array(43 downto 0);
          aes_round_sig : in unsigned(3 downto 0);
          out_ciphertext : out aes_word_array(3 downto 0)
          );
    end component;
begin

    -- the clk process just copies the input data to the circuit
    -- and also increments or resets the round counter.
    process(clk)
        variable plaintext_temp  : aes_word_array(3 downto 0);
        variable ciphertext_temp : aes_word_array(3 downto 0);
        variable aes_round_var   : unsigned(3 downto 0);
    begin
        if clk'EVENT and clk='1' then
            -- key must remain constant while done /= '0'
            in_key <= key;
                
            -- convert plaintext into little endian
            plaintext_temp(0) := plaintext(127 downto 96);
            plaintext_temp(1) := plaintext(95 downto 64);
            plaintext_temp(2) := plaintext(63 downto 32);
            plaintext_temp(3) := plaintext(31 downto 0);
            in_plaintext <= plaintext_temp;
                
            if reset = '1' then
                
                -- reset round
                aes_round_var := "0000";
                aes_round_sig <= aes_round_var;
                done <= '0';
            else                
                -- incr round (aes_round_var is flipflop)
                if aes_round_var < 11 then
                    aes_round_var := aes_round_var + 1;
                    done <= '0';
                else
                    done <= '1';
                end if;
                aes_round_sig <= aes_round_var;
                
            end if;
        end if;
    end process;
    
    aes_round_entity : aes_round   port map (clk, in_plaintext, expanded_key, aes_round_sig, out_ciphertext);
    exp_keys         : expand_keys port map (in_key, expanded_key);
    
    -- correct ciphertext into big endian
    ciphertext(127 downto 96) <= out_ciphertext(0);
    ciphertext(95 downto 64) <= out_ciphertext(1);
    ciphertext(63 downto 32) <= out_ciphertext(2);
    ciphertext(31 downto 0) <= out_ciphertext(3);
   
end multi_cycle;
