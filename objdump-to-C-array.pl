#!/usr/bin/perl -w
# given some objdump --disassemble output, yield lines which
# can be inserted into a C array

if (-t STDIN) {
  # stdin is a tty
  print("usage:\n",
        "  objdump --disassemble file.o | $0\n");
  exit(0);
}

while (defined($line = <STDIN>)) {
  # match disassembly lines
  ($offset, $opcodes, $assembler) = 
    ($line =~ /^([0-9a-f ]+):\s+([0-9a-f ]+)  \s+(\S.*)$/);
  if (defined($opcodes)) {
    # match
    #print("opcodes=\"$opcodes\", assembler=\"$assembler\"\n");

    # split the opcodes into a list
    @oplist = split(' ', $opcodes);
    if (@oplist == 0) {
      # no opcodes, probably misinterpreted the file format string or something
      next;
    }

    print("  ");
    $width=2;     # track how many chars we've written

    for ($i=0; $i < @oplist; $i++) {
      print("0x$oplist[$i], ");
      $width += 6;
    }

    # pad out to 40th column
    while ($width < 40) {
      print(" ");
      $width++;
    }

    # make perl think 'offset' is used (since its actual use
    # is commented-out now)
    $offset = $offset;

    # write assembler as a comment
    #print("// $offset: $assembler\n");
    print("// $assembler\n");
    next;
  }

  # try to match function headers; this is useful for outputting
  # separators between the functions
  ($funcName) = ($line =~ /[0-9a-f]+\s+<(.*)>:/);
  if (defined($funcName)) {
    print("// beginning of $funcName\n");
  }
}

