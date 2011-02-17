#!/usr/bin/perl

use strict;
use warnings;
use Date::Calc qw(Delta_DHMS Day_of_Week Today_and_Now);
use Net::Amazon::EC2;
use Getopt::Long;

my $aws_access_key_id = ENV{'AWS_ACCESS_KEY_ID'}; 
my $aws_secret_key_id = ENV{'AWS_SECRET_KEY_ID'};


my $debug = 0;
my $verbose = 0;
my $all = undef;
my $hostname = undef;
my $hours = undef;
my $dryrun = undef;
my $info = undef;
my $weeks = undef;
my $days = undef;

GetOptions ("debug!" => \$debug,
            "verbose!" => \$verbose,
            "dryrun!" => \$dryrun,
            "all" => \$all,
            "hostname=s" => \$hostname,
            "weeks=i" => \$weeks,
            "days=i" => \$days,
            "hours=i" => \$hours,
            "info!" => \$info);

sub get_snapshots {
    my $method_call = "describe_snapshots";
    my %method_args = (Owner => '742987638236');
    my $snapshots = error_check($method_call,%method_args);
    return @$snapshots;
}

sub delete_snapshot {
    my $snapshot = shift;
    my $dryrun = shift;
    my $method_call = "delete_snapshot";
    my %method_args = (SnapshotId => $snapshot->snapshot_id);

    if (defined($dryrun)) {
        debug_delete_snapshot($snapshot,$dryrun) if $info;
        return;
    } else {
        debug_delete_snapshot($snapshot) if $info;
        error_check($method_call,%method_args);
        return;
    }
}


sub rotate_hourly_snapshots {
    my $hostname = shift;
    my $hours = shift;
    my $dryrun = shift;
    my $days;
    ($days,$hours) = get_days_hours_from_hours($hours);

    foreach my $snapshot (get_snapshots()) {
        my @snapshot_time = get_normalized_snapshot_time($snapshot->start_time);
        my @current_time = get_todays_time();
        my $delta_days = get_delta_days_hours("days",@snapshot_time,@current_time);
        my $delta_hours = get_delta_days_hours("hours",@snapshot_time,@current_time);
        my $next_day = $days + 1;

        next if (!defined($snapshot->description));
        next if ($snapshot->description !~ m/-hourly-/);
        next if ($snapshot->description !~ m/$hostname-hourly/);
        next if ($delta_days <= $days);
        next if (($delta_days == $next_day) && ($delta_hours <= $hours));

        #if ($delta_days <= $days) {
        #    print "SnapshotID: " . $snapshot->snapshot_id . " Start Time: " . $snapshot->start_time . " Day Delta: $delta_days Hour Delta: $delta_hours\n";
        #    next;
        #}

        #if (($delta_days == $next_day) && ($delta_hours <= $hours)) {
        #    print "SnapshotID: " . $snapshot->snapshot_id . " Start Time: " . $snapshot->start_time . " Day Delta: $delta_days Hour Delta: $delta_hours\n";
        #    next;
        #}

        delete_snapshot($snapshot,$dryrun);
        debug_rotate_hourly_snapshot($snapshot,$delta_days,$delta_hours,@snapshot_time) if $verbose;
    }
}

sub rotate_daily_snapshots {
    my $snapshot = shift;
    my $weeks = shift;
    my $days = shift;
    my $dryrun = shift;
    my @snapshot_time = get_normalized_snapshot_time($snapshot->start_time);
    my @current_time = get_todays_time();
    my $delta = get_delta_days_hours("days",@snapshot_time,@current_time);

    if (is_sunday(@snapshot_time) != 1) {
        delete_snapshot($snapshot,$dryrun);
        debug_rotate_daily_snapshot($snapshot,$delta,@snapshot_time) if $verbose;
        return;

    }

    if ($delta > ($days + (7 * $weeks))) {
        delete_snapshot($snapshot,$dryrun);
        debug_rotate_daily_snapshot($snapshot,$delta,@snapshot_time) if $verbose;
        return;
    } 
}

sub rotate_snapshots {
    my $hostname = shift;
    my $weeks = shift;
    my $days = shift;
    my $dryrun = shift;

    foreach my $snapshot (get_snapshots()) {
        my @snapshot_time = get_normalized_snapshot_time($snapshot->start_time);
        my @current_time = get_todays_time();
        my $delta = get_delta_days_hours("days",@snapshot_time,@current_time);

        next if (!defined($snapshot->description));
        next if ($snapshot->description =~ m/-hourly-/);
        next if ($snapshot->description !~ m/$hostname-(snap|vol)/);
        next if (is_first_of_month(@snapshot_time) == 1);   

        next if ($delta < $days);

        rotate_daily_snapshots($snapshot,$weeks,$days,$dryrun);
    }
}

sub do_api_call {
    my $method_call = shift;
    my %method_args = @_;
    my $ec2 = Net::Amazon::EC2->new(
        AWSAccessKeyId => $aws_access_key_id,
        SecretAccessKey => $aws_secret_key_id,
        debug => "$debug"
    );

    return $ec2->$method_call(%method_args);

}

sub error_check {
    my $method_call = shift;
    my %method_args = @_;
    my $obj = do_api_call($method_call,%method_args);
    my $num_wait = 5; 
    my $sec_wait = 5; 

    while ((check_for_errors($obj) == 1) && ($num_wait >= 0)) { 
        my @errors = get_error_message($obj);
        my $error_code = $errors[0];
        my $error_message = $errors[1];
        die "error: Retries exhausted\n" if $num_wait == 0;
        print "error: " . $error_code . ", " . $error_message . "\n" if $verbose;
        print "error: Retry #$num_wait: Sleeping $sec_wait seconds\n"if $verbose;
        $num_wait--; 
        sleep $sec_wait;
        $obj = do_api_call($method_call,%method_args);
    }   
    return $obj;
}


sub check_for_errors {
    my $obj = shift;

    if (ref($obj) eq 'Net::Amazon::EC2::Errors') {
        return 1;
    }
}

sub get_error_message {
    my $obj = shift;
    return $obj->errors->[0]->code, $obj->errors->[0]->message; 
}

sub debug_rotate_hourly_snapshot {
    my $snapshot = shift;
    my $delta_days = shift;
    my $delta_hours = shift;
    my @snapshot_time = @_;
    print "debug: Snapshot       => " . $snapshot->snapshot_id . "\n";
    print "debug: Description    => " . $snapshot->description . "\n";
    print "debug: Timestamp      => @snapshot_time\n";
    print "debug: Delta_in_Days  => " . $delta_days . "\n";
    print "debug: Delta_in_Hours => " . $delta_hours . "\n";
    print "debug: \n";
}

sub debug_rotate_weekly_snapshot {
    my $snapshot = shift;
    my $delta = shift;
    my @snapshot_time = @_;
    print "debug: Snapshot       => " . $snapshot->snapshot_id . "\n";
    print "debug: Description    => " . $snapshot->description . "\n";
    print "debug: Timestamp      => @snapshot_time\n";
    print "debug: Delta_in_Days  => " . $delta . "\n";
    print "debug: Day_of_Week    => " . get_day_of_week(@snapshot_time) . "\n";
    print "debug: Day_of_Month   => " . get_day_of_month(@snapshot_time) . "\n";
    print "debug: \n";
}

sub debug_delete_snapshot {
    my $snapshot = shift;
    my $dryrun = shift;

    if (defined($dryrun)) {
        print "info: DRYRUN! Deleting Snapshot => " . $snapshot->snapshot_id . " Start Time => " . $snapshot->start_time . "\n";
    } else {
        print "info: Deleting Snapshot => " . $snapshot->snapshot_id . " Start Time => " . $snapshot->start_time . "\n";
    }
}

sub get_normalized_snapshot_time {
    my $date = shift;
    $date =~ s/(\d+)-(\d+)-(\d+)T(\d+):(\d+):(\d+).*/$1-$2-$3-$4-$5-$6/;
    return my ($yr,$mo,$day,$hr,$min,$sec) = split(/-/, $date, 6) if $date;
}

sub get_todays_time {
    return my ($yr,$mo,$day,$hr,$min,$sec) = Today_and_Now();
}

sub get_delta_days_hours {
    my ($result,$yr1,$mo1,$day1,$hr1,$min1,$sec1,$yr2,$mo2,$day2,$hr2,$min2,$sec2) = @_;

    my ($Dd,$Dh,$Dm,$Ds) =
        Delta_DHMS($yr1,$mo1,$day1,$hr1,$min1,$sec1,
                   $yr2,$mo2,$day2,$hr2,$min2,$sec2);

    return $Dd if $result =~ m/days/;
    return $Dh if $result =~ m/hours/;
    return undef;
}

sub get_day_of_week {
    my $yr = shift;
    my $mo = shift;
    my $day = shift;

    my $dow = Day_of_Week($yr,$mo,$day);
    return $dow;
}

sub get_day_of_month {
    my $yr = shift;
    my $mo = shift;
    my $day = shift;

    return $day;
}

sub get_current_month {
    my $yr = shift;
    my $mo = shift;

    return $mo;
}

sub is_first_of_month {
    my $yr = shift;
    my $mo = shift;
    my $day = shift;

    return 1 if ($day == 1);

    return 0;
}

sub is_sunday {
    my $yr = shift;
    my $mo = shift;
    my $day = shift;

    return 1 if (get_day_of_week($yr,$mo,$day) == 7);

    return 0;
}

sub get_days_hours_from_hours {
    use integer;
    my $hours = shift;
    my $days = ($hours / 24) - 1;
    $hours = $hours % 24;
    return $days,$hours;
}

sub usage {
    die  "
Usage:\n
Example: $0 --hostname author01-uat --weeks 8 --days 7
Example: $0 --hostname author01-uat --hours 24 \n\n";
}

#MAIN

if (!defined($hostname)) {
    usage();    
}

if (defined($hours)) {
    rotate_hourly_snapshots($hostname,$hours,$dryrun);
} elsif (defined($weeks) && defined($days)) {
    rotate_snapshots($hostname,$weeks,$days,$dryrun);
} else {
    usage();
}
