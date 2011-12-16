#!/usr/bin/perl

use strict;
use warnings;
use POSIX qw(strftime);
use Getopt::Long;
use DBI;

my $BACKUPDIR = "/d0/archive/backup/databases/";

my $debug = 0;
my $verbose = 0;
my $all = undef;
my $dbhost = undef;
my $dbport = undef;
my $dbuser = undef;
my $dbpass = undef;
my $db = undef;
my $dryrun = undef;
my $info = undef;
my $single_transaction = undef;

GetOptions ("debug!" => \$debug,
            "verbose!" => \$verbose,
            "all" => \$all,
            "dbhost=s" => \$dbhost,
            "dbport=i" => \$dbport,
            "dbuser=s" => \$dbuser,
            "dbpass=s" => \$dbpass,
            "db=s" => \$db,
            "dryrun!" => \$dryrun,
            "info!" => \$info,
            "single_transaction" => \$single_transaction);

sub usage {
    die "
Usage:\n
Example: $0 --dbhost some.host --dbuser jdoe --dbpass p\@ss --database foo
Example: $0 --dbhost some.host --dbport 3308 --dbuser jdoe --dbpass p\@ss --database foo
Example: $0 --dbhost some.host --dbuser jdoe --dbpass p\@ss --all\n\n"
}

sub get_all_databases {
    my $db = "mysql";
    my $dbhost = shift;
    my $dbport = shift;
    my $dbuser = shift;
    my $dbpass = shift;
    my @databases = DBI->data_sources("mysql",
                    {"host" => $dbhost, "port" => $dbport, "user" => $dbuser, password => $dbpass});
    return @databases;
}

sub debug_get_all_databases {
}

sub make_db_backup_dir {
}

sub get_backup_time {
}

sub get_backup_options {
}

sub is_mysql {
}

sub do_backup {
}

die usage();

# System Command Variables
my $mysqldump	= $ARGV[0];
my $mysqlhost	= $ARGV[1];
my $mysqlport	= $ARGV[2];
my $mysqluser	= "";
my $mysqlpass	= '';
my $gzip	= "/bin/gzip";
# End System Command Variables

my @time = localtime();
my $time = sprintf("%02d%02d%02d%02d%02d",$time[5]+1900,$time[4]+1,$time[3], $time[2], $time[1]);

my @databases = ();

# First three are mysqldump binary, mysql hostname and mysql port
shift @ARGV;
shift @ARGV;
shift @ARGV;
# Grab out the databases passed into the @database array
foreach my $database (@ARGV) {
	push (@databases, $database);
}
#print "@databases\n";

my $backupdir = "/d0/archive/backup/databases/"; # Don't forget Trailing Slash
my $option = "--skip-lock-table --single-transaction";

die "\n$backupdir doesn\'t exist\n" if ! -d $backupdir;

my $keep = 30;

foreach my $database (@databases) {
	my $dir;
	if ( $database =~ 'mysql' ) {
        	$option = '';
		$dir = $backupdir . $mysqlhost . "-" . $mysqlport . "_" . $database . "/";
	    }
	else {
		$dir = $backupdir . $database . "/";
	    }
	if ( (! -e $dir) && (! -d $dir) ) {
		#print "mkdir $dir,0755 or die \"Can't make directory $dir\n\"\n";
		mkdir $dir,0755 or die "Can\'t make directory $dir\n";
	    }
		my $filename 	= "$dir" . "$database.$time.sql.gz"; 
		#print "$filename\n";

		system("$mysqldump -h $mysqlhost -P $mysqlport -u $mysqluser -p$mysqlpass $option $database | $gzip > $filename");
}
