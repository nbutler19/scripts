#!/usr/bin/perl

use strict;
use warnings;

my $uid_count = "2040";

$/ = "}\n";

while (<>) {
  chomp;
  s/\s+//g;
  s/(.*)require.*?]],(.*)/$1$2/;
  s/(.*)ensure=>present,(.*)/$1$2/;
  s/(.*)managehome=>true,(.*)/$1$2/;
  s/\"+//g;
  s/\'+//g;

  #print;
  #print "\n";

  next unless m/^\@user/ && m/.*home.*ftp.*/;

  my $name = $_;
  my $values = $_;

  #if ( m/^\@user/ && m/.*home.*ftp.*/) { 
    $name =~ s/\@user{(.*?):.*/$1/; 
    $values =~ s/.*:(.*)/$1/;

    my @values = split(/,/ , $values);

    open(FILE, ">$name.json");

    print FILE "{\n";
    print FILE "  \"id\": \"$name\",\n";

    foreach my $value (@values) {
      $value =~ s/=>/:/;
      if ($value =~ m/uid:(.*)/) {
        $value = "uid:$uid_count";
      }

      if ($value =~ m/home.*ftp.*/) {
        print FILE "  \"groups\": \"ftpuser\",\n";
        $value =~ s/home(.*)/home_dir$1/;
      }

      $value =~ s/(.*):(.*)/\"$1\":\ \"$2\"/;
      $value =~ s/(\"uid\":)\ \"(\d+)\"/$1\ $2/;
      $value =~ s/(\"gid\":)\ \"(\d+)\"/$1\ $2/;

      print FILE "  $value,\n";
    }
    print FILE "  \"ssh_key\": \"\",\n";
    print FILE "  \"active\": \"yes\"\n";
    print FILE "}\n";
    close(FILE);
  #}

  $uid_count++;

}

## Format to parse
#@user{"butlern":ensure=>present,home=>"/home/butlern",uid=>"1001",gid=>"100",groups=>["operator","adm"],comment=>"NathanButler(Ops)",shell=>"/bin/bash",password=>'$1$8dQJPo39$gd6a1mcZcyW9XL8eSMMbJ/',managehome=>true,

## Format to output
