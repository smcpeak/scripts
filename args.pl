#!/usr/bin/perl -w
# print arguments
			    
$n = @ARGV;
print("number of arguments: $n\n");
	 
for ($i = 0; $i < @ARGV; $i++) {
  print("arg $i: $ARGV[$i]\n");
}
