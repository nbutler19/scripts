#!/usr/bin/perl

use strict;
use warnings;

my ( $file, $age )  = youngest(@ARGV);

print "$file: Last Modified => " . scalar(localtime($age)) . "\n";

sub youngest {
	my $youngest = shift(@_);
	my $youngest_file_age;	
	foreach my $file (@_) {
		open( FILEHANDLE1, $file) or die "Couldn't read file: $!";
		open( FILEHANDLE2, $youngest) or die "Couldn't read file: $!";
		my $file_age = (stat($file))[9];
		$youngest_file_age = (stat($youngest))[9];
		my ($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$size,
    			$atime,$mtime,$ctime,$blksize,$blocks)
    			= stat($file);
		$youngest = $file if $file_age > $youngest_file_age;
		$youngest_file_age = $file_age if $file_age > $youngest_file_age;
		close FILEHANDLE1;
		close FILEHANDLE2;
	}
	return ( $youngest, $youngest_file_age );
}
