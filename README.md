# Paxton RFID clock and data decoder for Sigrok

Sigrok protocol decoder for clock and data output from Paxton RFID readers.
Paxton RFID readers output the fob/card serial number as a clock and data output.
characters are encoded as 4 bits little endian number + 1 bit odd parity
eg 3 = 1100(1)

The output is of the format:  
10 bits leadin  
start character "B"  
card number  
stop character "F"  
LRC  
10 bits leadout  

If a switch2 fob or card is scanned additional data is generated with the character "d" as a seperator between these fields.
This has not been fully decoded yet and investigating this is why I wrote this decoder.

Screenshot from PulseView:
![Decoder example](screenshot.png)

# Installation

Copy the paxton folder and its contents to  
`~/.local/share/libsigrokdecode/decoders` (Linux) or  
`%ProgramData%\libsigrokdecode\decoders` (Windows).  
