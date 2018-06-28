#!/usr/bin/perl -w
# mutation-tester.pl
# crude stab at a mutation tester

use strict;

runUnitTests();

# True to print lines subject to mutation.
my $scan = 0;

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
        "  --help          print this message\n" .
        "  --scan          print lines subject to mutation\n" .
        "  --              end options list\n" .
        "");
      exit(0);
    }
    elsif ($opt eq "--scan") {
      $scan = 1;
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

print("$scan $fname\n");

if (!$scan) {
  die("unimplemented: no --scan\n");
}

open(IN, "<$fname") or die("cannot open $fname: $!\n");
my @lines = <IN>;
close(IN) or die;

print("read " . (scalar(@lines)) . " lines\n");

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
