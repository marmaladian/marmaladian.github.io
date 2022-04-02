_header(.:Uxn assembly notes:.)m4_dnl
<p>Loose notes as I figure out how to use Uxn assembly.</p>
<figure><img src="../media/img/codex/uxn-jumble.png" class="wide"><figcaption>Transferring tile map data to the screen</figcaption></figure>
<ul>
	<li>_link(.:uxn - XXIIVV:., .:https://wiki.xxiivv.com/site/uxn.html:.)</li>
	<li>_link(.:nihilazo's uxn notes:., .:https://tilde.town/~nihilazo/uxn.html:.)</li>
</ul>
<h2>Opcodes</h2>
<table>
<tr><th>Opcode</th><th>Stack before</th><th>Stack after</th><th>Details</th></tr>
<tr><th colspan="4">Stack</th></tr>
<tr><td>BRK</><td></td><td></td><td>Break</td></tr>
<tr><td>LIT</td><td>??</td><td></td><td>Literal</td></tr>
<tr><td>---</td><td></td><td></td><td></td></tr>
<tr><td>POP</td><td>a</td><td></td><td>Pop</td></tr>
<tr><td>DUP</td><td>a</td><td>aa</td><td>Duplicate</td></tr>
<tr><td>SWP</td><td>a b</td><td>b a</td><td>Swap</td></tr>
<tr><td>OVR</td><td>a b</td><td>a b a</td><td>Over</td></tr>
<tr><td>ROT</td><td>a b c</td><td>b c a</td><td>Rotate. Rotates left. This is also handy when you want to swap a BYTE with a SHORT, e.g. a bc > bc a. Guess ROT ROT would be necessary to switch a SHORT with a BYE e.g. ab c > b c a > c ab</td></tr>
<tr><th colspan="4">Memory</th></tr>
<tr><td>LDZ</td><td>a</td><td>val</td><td>LoadZeropage. Loads value from address in the 0x0000 to 0x00FF range?</td></tr>
<tr><td>STZ</td><td>val a</td><td></td><td>STore Zero page. Stores to addresses in the 0x0000 to 0x00FF range?</td></tr>
<tr><td>LDR</td><td>a</td><td>val</td><td>LoaD Relative. Relative addresses are at labels defined in the program, not a specific memory address?</td></tr>
<tr><td>STR</td><td>val a</td><td>AFT</td><td>STore Relative. Can be a position +0x7f -0x80 forward or back from the current position.</td></tr>
<tr><td>LDA</td><td>a*</td><td>val</td><td>LoaD Absolute. This will always work (as opposed to relative and zero page) but takes more space to specify the full address. NB: Actually, it doesn't seem to load values that are in the 0100 area correctly? I had issues using it but they disappeared when I changed calls to LDZ.</td></tr>
<tr><td>STA</td><td>val a*</td><td></td><td>STore Absolute.</td></tr>
<tr><td>DEI</td><td>a</td><td>val</td><td>DEvice In. Reads from the specified device port.</td></tr>
<tr><td>DEO</td><td>val a</td><td></td><td>DEvice Out. Writes value to the specified device port.</td></tr>
<tr><th colspan="4">Logic</th></tr>
<tr><td>EQU</td><td>a b</td><td>flag</td><td>EQUal. Tests if a and b are equal, if so adds a 0x01 to the stack, otherwise 0x00.</td></tr>
<tr><td>NEQ</td><td>a b</td><td>flag</td><td>Not EQual. is this the same as EQU, but returns opposite flags?</td></tr>
<tr><td>GTH</td><td>a b</td><td>flag</td><td>Greater THan. If a > b, returns 0x01 otherwise 0x00.</td></tr>
<tr><td>LTH</td><td>a b</td><td>flag</td><td>Less THan. Same as GTH, but tests a < b.</td></tr>
<tr><td>JMP</td><td>a</td><td></td><td>JuMP. Program control moves to the address a.</td></tr>
<tr><td>JCN</td><td>flag a</td><td></td><td>Jump CoNditional. If flag is 0x01, control moves to the address a. Otherwise, continues on to next instruction.</td></tr>
<tr><td>JSR</td><td>a</td><td>rs</td><td>Jump Stash. Places program counter on return stack then jumps. JMP2r can be used to return to the point JSR was called.</td></tr>
<tr><td>STH</td><td>a</td><td>rs</td><td>Stash. Places value on the return stack. STH2r pops the top item from the return stack and puts it on the working stack.</td></tr>
<tr><th colspan="4">Arithmetic</th></tr>
<tr><td>ADD</td><td>a b</td><td>result</td><td>ADD. Adds two numbers together. What happens with overflow?</td></tr>
<tr><td>SUB</td><td>a b</td><td>result</td><td>SUBtract. Subtracts b from a.</td></tr>
<tr><td>MUL</td><td>a b</td><td>result</td><td>MULtiply. Multiplies a and b.</td></tr>
<tr><td>DIV</td><td>a b</td><td>result</td><td>DIVide. Divides a by b.</td></tr>
<tr><td>AND</td><td>a b</td><td>result</td><td>Logical AND.</td></tr>
<tr><td>ORA</td><td>a b</td><td>result</td><td>Logical OR.</td></tr>
<tr><td>EOR</td><td>a b</td><td>result</td><td>Logical Exclusive OR.</td></tr>
<tr><td>SFT</td><td>a b</td><td>result</td><td>ShiFT. Bitwise shift of a, by b. b is in the format #LR, where L is the number of places to shift left, R is the amount to shift right. e.g. #08 #02 SFT would shift 0x08 2 places right, resulting in 0x02. #08 #20 SFT would shift 2 places left, resulting in 0x20. I assume shifting by #22 would have no effect.</td></tr>
</table>

<h2>Unsorted tips</h2>
<p>Anything in parentheses is a comment, and is ignored by the assembler. There must be white space between the comment parentheses and their content, otherwise the <code>(example</code> woudl be regarded as a non-existent macro.</p>
<p>If you are unexpectedly under/overflowing the stack, check you haven't missed the spaces in a comment somewhere.</p>
<p>You can do <code>#1234 #01 SUB<code> if you're sure that the first byte won't go below zero. Same with ADD.</p>
<p><code>#0a .Console/char DEO</code> will give a new line. #20 will give a space and #21 an exclamation mark. Useful for debugging.</p>

<h2>neralie.usm</h2>
<p>I reviewed the source to some of the programs that accompany the C Uxn emulator to learn how they work.</p>
<pre>(
	app/neralie : clock with arvelie date

	TODO
		- use splash screen when FPS calculation is unstable
)</pre>
<p>Anything in parentheses is a comment, and is ignored by the assembler. There must be white space between the comment parentheses and their content.</p>
<pre>%h { .DateTime/hour   DEI }
%m { .DateTime/minute DEI }
%s { .DateTime/second DEI }
%8** { #30 SFT2 }</pre>
<p>These four lines are defining macros. For example, the macro in the first line causes any occurence of <b>h</b> in the code to be replaced with the code between the curly braces.</p>
<p>The first three macros are for loading the system's date device values into <em>the address preceding the macro identifier?</em></p>
<p>The fourth macro 8** performs an arithmetic shift... #30 is decimal 48, but shifting 48 places doesn't seem right.</p>
<pre>( devices )

|00 @System [ &vector $2 &pad $6 &r $2 &g $2 &b $2 ]
|10 @Console [ &vector $2 &pad $6 &char $1 &byte $1 &short $2 &string $2 ]
|20 @Screen [ &vector $2 &width $2 &height $2 &pad $2 &x $2 &y $2 &addr $2 &color $1 ]
|b0 @DateTime [ &year $2 &month $1 &day $1 &hour $1 &minute $1 &second $1 &dotw $1 &doty $2 &isdst $1 ]</pre>

<p>These lines are mapping the system devices to labels. The |xx values are indicating the place in memory where this device lies, then the @Xxx is defining a label for that address. The rest of the line is then creating offsets from the label using 'sub-labels' - these can be addressed like <b>.Screen/x</b>. The $x indicate padding, how much space is between each of the sub-labels.</p>

<pre>( variables )

|0000

@fps [ &current $1 &next $1 &second $1 ]
@number [ &started $1 &count $1 ]
@lines [ &x1 $2 &x2 $2 &y1 $2 &y2 $2 &addr $1 ]
@neralie [ &n0123 $2 &n4 $1 &n5 $1 &n6 $1 &n7 $1 &n8 $1 &n9 $1 &color $1 &x $2 &y $2 &w $2 &h $2 ]
@mul [ &ahi $1 &alo $1 &bhi $1 &blo $1 ]</pre>

<p>These are memory addresses for variables, arranged into labels and sub-labels. The $x values indicate the padding before the address corresponding to the next label. So, @fps (and @fps/&current) are at memory address 0000. &current is intended to take up 1 byte, so there is a padding of $1 afterwards, then &next is at address 0x0001, and so on. It looks like these run up to 0x0023 (35 bytes).</p>

<pre>( program )

|0100

	( theme )  #03fd .System/r DEO2 #0ef3 .System/g DEO2 #0bf2 .System/b DEO2
	( vectors )  ;on-screen .Screen/vector DEO2
	#01 .fps/current STZ</pre>

<p><code>|0100</code> puts the following code at position 0x0100 in memory. I'm not sure if this was just to leave space for any more variables that started at 0x0000 or there's some other reason for it.</p>
<p><code>a b DEO2</code> will load a 2-byte value <em>a</em> into device port <em>b</em>. Specifically, these are colour values used to set the four system colours. The second line is also inputting a value to a device port, in this case it's an address called <em>on-screen</em> which is being stored in the screen device's vector. The vector will be called every screen frame; presumably @on-screen is defined later in the program and contains instructions for updating the screen.</p>
<p>The last line stores #01 into the address at .fps/current. I'm not sure how STZ (Store Zero Page) works differently from Store Absolute here... perhaps the addresses up to 0x00FF are considered the zero page, and can be declared as variables?</p>

<pre>#000c
	DUP2 .lines/x1 STZ2
	DUP2 .lines/y1 STZ2
	DUP2 .Screen/width DEI2 SWP2 SUB2 #0001 SUB2 .lines/x2 STZ2
	     .Screen/height DEI2 SWP2 SUB2 .lines/y2 STZ2</pre>

<p>Store #000c at <b>lines/x1</b> and <b>lines/y1</b>, then (Screen/width - 12 - 1) and (Screen/height - 12) into x2 and y2. This looks like it's setting up a padding of 12 pixels around the screen.</p>

<pre>	#02 .neralie/color STZ
	.lines/x1 LDZ2 .lines/x2 LDZ2
	OVR2 OVR2 .lines/y1 LDZ2 ;h JSR2
	          .lines/y2 LDZ2 ;h JSR2
	.lines/y1 LDZ2 #0001 SUB2 .lines/y2 LDZ2 #0001 ADD2
	OVR2 OVR2 .lines/x1 LDZ2 ;v JSR2
	          .lines/x2 LDZ2 ;v JSR2</pre>

<p>

_footer(.:recipes:.)m4_dnl
