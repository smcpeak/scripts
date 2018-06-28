#!/usr/bin/perl -w
# mutation-tester.pl
# crude stab at a mutation tester

use strict;

runUnitTests();

# True to print lines subject to mutation.
my $scan = 0;

# Command to run to compile the program.
my $compileStep = "";

# Command to run to test the program.
my $testStep = "";

# Test step timeout as a 'timeout' duration.
my $timeoutDuration = "1s";

# True to stop after one, which is useful when developing the
# compile and test command lines.
my $stopAfterOne = 0;

while (@ARGV >= 1 && $ARGV[0] =~ m/^-/) {
  my $opt = $ARGV[0];
  if ($opt =~ m/^-/) {
    if ($opt eq "--") {
      shift @ARGV;
      last;
    }
    elsif ($opt eq "--help") {
      print(
        "usage: $0 [options] file-to-test.cc\n" .
        "\n" .
        "options\n" .
        "  --help             print this message\n" .
        "  --scan             print lines subject to mutation, then stop\n" .
        "  --compile <cmd>    command to compile mutant.cc\n" .
        "  --test <cmd>       command to test compiled program\n" .
        "  --one              stop after first candidate mutant\n" .
        "");
      exit(0);
    }
    elsif ($opt eq "--scan") {
      $scan = 1;
    }
    elsif ($opt eq "--compile") {
      shift @ARGV;
      if (scalar(@ARGV) == 0) {
        die("missing command after --compile\n");
      }
      $compileStep = $ARGV[0];
    }
    elsif ($opt eq "--test") {
      shift @ARGV;
      if (scalar(@ARGV) == 0) {
        die("missing command after --test\n");
      }
      $testStep = $ARGV[0];
    }
    elsif ($opt eq "--one") {
      $stopAfterOne = 1;
    }
    else {
      die("unknown option: $opt\ntry --help\n");
    }
    shift @ARGV;
  }
}

if (@ARGV != 1) {
  die("must specify exactly one file name; try --help\n");
}

my $fname = $ARGV[0];


if (!$scan) {
  if ($compileStep eq "") {
    die("must pass --compile option; try --help\n");
  }
  if ($testStep eq "") {
    die("must pass --test option; try --help\n");
  }
}


# Read the file to test.
open(IN, "<$fname") or die("cannot open $fname: $!\n");
my @lines = <IN>;
close(IN) or die;
#print("read " . (scalar(@lines)) . " lines\n");


# Collect the 0-based line numbers of lines to mutate.
my @linesToMutate = ();

# Number of unbalanced open-parens seen so far.
my $totalParens = 0;

for (my $i=0; $i < @lines; $i++) {
  my $line = $lines[$i];
  chomp($line);

  # True if I want to mutate this line.
  my $wantLine = 1;

  # Basic desired structure:
  #   - start with a space
  #   - end with a semicolon
  #   - possibly has a comment
  my $nonStmt = 0;
  if ($line !~ m,^ .*;\s*(//.*)?$,) {
    $nonStmt = 1;
    $wantLine = 0;
  }

  # Skip blank and whitespace.
  my $blank = 0;
  if ($line =~ m,^\s*(//.*)?$,) {
    $blank = 1;
    $wantLine = 0;
  }

  # Skip lines with braces.
  my $braces = 0;
  if ($line =~ m/[{}]/) {
    $braces = 1;
    $wantLine = 0;
  }

  # Exclude return, unless it is just "return;", because I might
  # be making the function not return a value if I delete it.
  my $return = 0;
  if ($line =~ m/\breturn\b(?!\s*;)/) {
    $return = 1;
    $wantLine = 0;
  }

  my $assert = 0;
  if ($line =~ m/\b(xassert|assert|selfCheck)\b/) {
    $assert = 1;
    $wantLine = 0;
  }

  my $decl = isDeclaration($line);
  if ($decl) {
    $wantLine = 0;
  }

  my $parens = 0;
  my $len = length($line);

  if (!$blank) {
    for (my $j=0; $j < $len; $j++) {
      my $c = substr($line, $j, 1);
      if ($c eq "(") {
        $parens++;
      }
      elsif ($c eq ")") {
        $parens--;
      }
    }
  }

  $totalParens += $parens;

  my $rejParens = ($totalParens != 0 || $parens != 0);
  if ($rejParens) {
    $wantLine = 0;
  }

  if ($scan) {
    printf("%6d %2d %2d  %s %s\n",
           $i+1,
           $totalParens,
           $parens,
           ($wantLine?    "***" :
            $nonStmt?     "   " :
            $blank?       "  _" :
            $braces?      "  b" :
            $return?      "  r" :
            $assert?      "  a" :
            $decl?        "  d" :
            $rejParens?   "  p" :
                          "???"),
           $line);
  }

  if ($wantLine) {
    push @linesToMutate, ($i);
  }
}

if ($scan) {
  exit(0);
}


mkdir("mut");     # ignore any error

# Set of 1-based line numbers for which tests need to be improved.
my @survivingMutants = ();

# Stats on results.
my $compileFailed = 0;
my $mutantSurvived = 0;
my $mutantKilled = 0;

# Process each line.
foreach my $lineNumber (@linesToMutate) {
  my $linePlusOne = $lineNumber + 1;
  print("Testing mutant $linePlusOne ...\n");

  # Write out a modified version of the file.
  open(OUT, ">mutant.cc") or die("cannot write mutant.cc: $!\n");
  for (my $i=0; $i < @lines; $i++) {
    my $line = $lines[$i];
    if ($i == $lineNumber) {
      print OUT ("//REMOVED: $line\n");
    }
    else {
      print OUT ("$line\n");
    }
  }
  close(OUT) or die;

  # Run the compile step.
  my $compileOutFname = "mut/m$linePlusOne.compile.out";
  if (0!=mysystem("$compileStep >$compileOutFname 2>&1")) {
    $compileFailed++;
    print("  Compile step failed, see $compileOutFname\n");
    next;
  }

  # Run test step.
  my $testOutFname = "mut/m$linePlusOne.test.out";
  my $code = mysystem("timeout $timeoutDuration $testStep >$testOutFname 2>&1");
  if ($code == 0) {
    print("  Mutant survived, see $testOutFname\n");
    push @survivingMutants, ($linePlusOne);
    $mutantSurvived++;
  }
  else {
    my $how;
    if ($code != 0) {
      if ($code >= 256) {
        $how = "exit " . ($code >> 8);
      }
      else {
        $how = "signal $code";
      }
    }
    print("  Mutant killed ($how), as desired.\n");
    $mutantKilled++;
  }

  if ($stopAfterOne) {
    print("Stopping after first mutant candidate due to --one option.\n");
    last;
  }
}

printf("Tester complete.  Stats:\n");
printf("  Total candidates:  %6d\n", scalar(@linesToMutate));
printf("  Compile failed:    %6d\n", $compileFailed);
printf("  Killed mutants:    %6d\n", $mutantKilled);
printf("  Surviving mutants: %6d\n", $mutantSurvived);

if ($mutantSurvived) {
  print("\nSurvivors: @survivingMutants\n");
  exit(1);
}
else {
  exit(0);
}


sub isDeclaration {
  my ($line) = @_;

  my ($type, $mods, $var) =
    ($line =~ m/^\s*                   # leading ws
                (\b\w+\b)              # $type: word
                (                      # $mods: sequence of type modifiers
                  (?:                    # one type modifier
                    \s*                    # space before modifier
                    (?:                    # the modifier itself
                      \b\w+\b |              # word
                      \*      |              # pointer
                      <(?!<)  |              # open angle-bracket
                      >(?!>)                 # close angle-bracket
                    )
                  )
                  *                      # more modifiers?
                )
                \s*
                (\b\w+\b)              # variable name
                \s*
                [=;,\(]                # init, semi, multivar, or ctor
                                       # no anchor; anything can follow
               /x );                   # "/x" modifier for readable regex

  if (!defined($var)) {
    return 0;
  }

  #print("type='$type' mods='$mods' var='$var'\n");

  return 1;
}


# like system, except bail if underlying command died by ctrl-c
sub mysystem {
  my (@cmd) = @_;

  my $code = system(@cmd);
  if ($code == 2) {
    die("Interrupted by Ctrl+C.\n");
  }
  return $code;
}


# ----------------------- unit tests ----------------------------
sub testIsDeclaration {
  my @positiveExamples = (
    "TextCoord const m = this->mark();",
    "TextCoord selLow, selHigh;",
    "int h = m_lastVisible.line - m_firstVisible.line;",
    "bool center = false;",
    "bool ok = walkCursor(this->core(), tc, textLen);",
    "char *buf = new char[len+1];",
    "stringBuilder sb;",
    "int endLine = (selHigh.column==0? selHigh.line-1 : selHigh.line);",
    "GrowArray<char> contents;",
    "int contents(10);",
    "GrowArray<char> contents(10);",
  );

  foreach my $e (@positiveExamples) {
    if (!isDeclaration($e)) {
      die("should have been recognized as a declaration: '$e'");
    }
  }

  my @negativeExamples = (
    "sb << getTextRange(TextCoord(i, 0), lineEndCoord(i));",
    "sb << ch;",
  );

  foreach my $e (@negativeExamples) {
    if (isDeclaration($e)) {
      die("should NOT have been recognized as a declaration: '$e'");
    }
  }
}


sub runUnitTests {
  testIsDeclaration();
}


# EOF
