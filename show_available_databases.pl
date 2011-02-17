#!/usr/bin/perl -w 
use DBI; 
use strict; 

my $host = "";
my $port = "";
my $user = "";
my $pass = "";

my @databases = DBI->data_sources("mysql",
                {"host" => $host, "port" => $port, "user" => $user, password => $pass});


foreach my $db (@databases) {
    print "$db\n";
}
