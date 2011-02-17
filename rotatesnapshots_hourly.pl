#!/usr/bin/perl

#############################################################################################
#                                                                                           #
# This script rotates our hourly snapshot backups based on a 24-hour rolling window.        #
# Currently it's set to keep 24 hourly backups.                                             #
#                                                                                           #
#############################################################################################

use strict;
use warnings;
use Date::Manip;
use Net::Amazon::EC2;

my $aws_access_key_id = ENV{'AWS_ACCESS_KEY_ID'};
my $aws_secret_key_id = ENV{'AWS_SECRET_KEY_ID'};

my $server = ();
my $debug = 0;

die "No arguments supplied\n\nExample: $0 misc01\n\n" if ! (@ARGV);

$server = $ARGV[0];

# Set thresholds for when to start thinning out backups

my $hour_thold = 24.9; # Delta_Format function returns hours with granularity of one decimal point so we fudge here

my $ec2 = Net::Amazon::EC2->new(
        AWSAccessKeyId => $aws_access_key_id, 
        SecretAccessKey => $aws_secret_key_id,
        debug => "$debug"
);

my $snapshots_array_ref = $ec2->describe_snapshots(Owner => '742987638236');

my @snapshots = @$snapshots_array_ref;

foreach my $snapshot_hash_ref (@snapshots) {
    my %snapshot = %$snapshot_hash_ref;
    $snapshot{start_time} =~ s/(\d+)-(\d+)-(\d+)T(\d+):(\d+):(\d+).*/$1-$2-$3-$4-$5-$6/; # Normalize Date
    my ($snap_yr, $snap_mo, $snap_day, $snap_hr, $snap_min, $snap_sec) = split(/-/, $snapshot{start_time}, 6) if $snapshot{start_time};
    my $snap_epoch_seconds = Date_SecsSince1970GMT($snap_mo,$snap_day,$snap_yr,$snap_hr,$snap_min,$snap_sec);
    my $err;
    my $tz = Date_TimeZone;
    my $current_time = ParseDate("today");
    $current_time = Date_ConvTZ($current_time,$tz,"UTC");
    my $snapshot_time = ParseDateString("epoch $snap_epoch_seconds");
    my $delta = DateCalc($snapshot_time,$current_time,\$err,0);
    my $delta_in_hours = Delta_Format($delta,,1,"%ht");
    my $snap_id = $snapshot{snapshot_id};
    if (( $snapshot{description} ) && ( $snapshot{description} =~ m/$server-hourly-snap/ ))
        {
        #print "STARTING....\n";
        #print "Snapshot Description: $snapshot{description}\n";
        #print "Snapshot Start Time: $snapshot{start_time}\n";
        #print "Calculated Epoch Seconds: $snap_epoch_seconds\n";
        #print "Converted Epoch Seconds: " . scalar(localtime($snap_epoch_seconds)) . "\n";
        #print "Current Time: $current_time\n";
        #print "Snapshot Time: $snapshot_time\n";
        #print "Calculated Delta: $delta\n";
        #print "Calculated Delta in Hours: $delta_in_hours\n";
        if ($delta_in_hours < $hour_thold)
            {
            #print "KEEPING $snap_id because it is $delta_in_hours which is less than $hour_thold\n";
        }
        else {
            $ec2->delete_snapshot(SnapshotId => "$snap_id"); 
            #print "DELETING $snap_id because it is $delta_in_hours which is older than $hour_thold\n";
        #print "FINISHED!\n\n";
        }
    }
}
