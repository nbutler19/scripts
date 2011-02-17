#!/usr/bin/perl

#TODO:
# 1. Return 'not found' if no volumes attached
# 2. Return 'no match' if device name doesn't match any attached devices

use strict;
use warnings;
use Date::Manip;
use Net::Amazon::EC2;
use Net::DNS;
use POSIX qw(strftime);
use Getopt::Long;

my $aws_access_key_id = ENV{'AWS_ACCESS_KEY_ID'};
my $aws_secret_key_id = ENV{'AWS_SECRET_KEY_ID'};

# Debug flags. $debug is useful for seeing the entire api response. $verbose is just internal script print statements.
my $debug = 0;
my $verbose = 0;
my $all = undef;
my $instance_id = undef;
my $hostname = undef;
my $ipaddress = undef;
my $description = undef;
my $device = undef;
my $dryrun = undef;
my $info = undef;

GetOptions ("debug!" => \$debug,
            "verbose!" => \$verbose,
            "dryrun!" => \$dryrun,
            "all" => \$all,
            "instanceid=s" => \$instance_id,
            "ipaddress=s" => \$ipaddress,
            "hostname=s" => \$hostname,
            "description=s" => \$description,
            "info!" => \$info,
            "device=s" => \$device);

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

sub get_instanceid_from_hostname { 
    my $hostname = shift;
    my $method_call = "describe_instances";
    my $reservationinfo = error_check($method_call);

    foreach my $reservation (@$reservationinfo) {
        foreach my $instance ($reservation->instances_set) {
            if ($instance->instance_state->name eq "running") {
                if ( does_hostname_match($hostname, $instance->dns_name,$instance->private_dns_name,$instance->ip_address,$instance->private_ip_address) ) {
                    debug_instance($instance) if $verbose;
                    return $instance->instance_id;
                }
            }
        }
     }
     return undef
}

sub debug_instance {
    my $instance = shift;
    print "debug: matched instance => " . $instance->instance_id . " with public hostname => " . $instance->dns_name . " to $hostname\n";
    print "debug: \n";
}

sub get_attached_volumeids {
    my $instance_id = shift;
    my $method_call = "describe_instances";
    my %method_args = (InstanceId => $instance_id);
    my $reservationinfo = error_check($method_call,%method_args);

    foreach my $reservation (@$reservationinfo) {
        foreach my $instance ($reservation->instances_set) {
            my @volumeids = get_block_device_volumeids($instance->block_device_mapping);
            return \@volumeids;
        }
    }
}

sub get_block_device_volumeids {
    my $block_device_mapping = shift;
    my @volumeids = ();
    foreach my $block_device (@$block_device_mapping) {
        push @volumeids,$block_device->ebs->volume_id;
    }
    return @volumeids;
}

sub get_volume_info {
    my $volume_id = shift;
    my $method_call = "describe_volumes";
    my %method_args = (VolumeId => $volume_id);
    my $volume_set = error_check($method_call, %method_args);
    my %volume_info = ();

    foreach my $volume_attr (@$volume_set) {
        my $size = $volume_attr->size;
        foreach my $attachments ($volume_attr->attachments) {
            foreach my $volume (@$attachments) {
                $volume_info{'volume_id'} = $volume->volume_id;
                $volume_info{'instance_id'} = $volume->instance_id;
                $volume_info{'status'} = $volume->status;
                $volume_info{'attach_time'} = $volume->attach_time;
                $volume_info{'device'} = $volume->device;
                $volume_info{'size'} = $size;
                debug_volume_info($volume, $size) if $verbose;
            }
        }
        return \%volume_info;
    }
}

sub debug_volume_info {
    my $volume = shift;
    my $size = shift;

    print "debug: VolumeId   => " . $volume->volume_id . "\n";
    print "debug: InstanceId => " . $volume->instance_id . "\n";
    print "debug: Status     => " . $volume->status . "\n";
    print "debug: AttachTime => " . $volume->attach_time . "\n";
    print "debug: Device     => " . $volume->device . "\n";
    print "debug: Size       => " . $size . "\n";
    print "debug: \n";
}

sub does_hostname_match {
    my $host = shift;
    my $ec2_public_fqdn = shift;
    my $ec2_private_fqdn = shift;
    my $ec2_public_ip = shift;
    my $ec2_private_ip = shift;
    my ($resolved_host , $resolved_class) = dns_lookup($host);

    if ($resolved_class eq "address") {
        return does_resolved_host_match_public_private($resolved_host, $ec2_public_ip, $ec2_private_ip);
    } elsif (($resolved_class eq "cname") or ($resolved_class eq "ptrdname")) {
        return does_resolved_host_match_public_private($resolved_host, $ec2_public_fqdn, $ec2_private_fqdn);
    }
}

sub does_resolved_host_match_public_private {
    my $resolved_host = shift;
    my $public = shift;
    my $private = shift;

    if ($resolved_host eq $public) {
        return 1;
    } elsif ($resolved_host eq $private) {
        return 1;
    }
    return 0;
}

sub dns_lookup { 
    my $host = shift;
    my $res = Net::DNS::Resolver->new;
    my $query = $res->search($host);
  
    if (!$query) {
        die "error: " . $res->errorstring . "\n";
    }

    foreach my $rr ($query->answer) {
        if ($rr->type eq "CNAME") {
            return $rr->cname, "cname";
        } elsif ($rr->type eq "A") {
            return $rr->address, "address";
        } elsif ($rr->type eq "PTR") {
            return $rr->ptrdname, "ptrdname";
        } else {
            next;
        }
    }
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
        print "error: " . $error_code . ", " . $error_message . "\n";
        print "error: Retry #$num_wait: Sleeping $sec_wait seconds\n";
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

sub get_description {
    my $hostname = shift;
    my $instance_id = shift;
    my $volume_id = shift;
    my $device = shift;
    my $desc = shift;
    my $timestamp = strftime "%Y-%m-%d-%H:%M", localtime;

    my $description = "snap-$volume_id-$device-$timestamp";

    if (defined($desc)) {
        $description = "$desc-" . $description;
    }

    if (defined($hostname)) {
        $description = "$hostname-" . $description;
    }
    else {
        $description = "$instance_id-" . $description;
    }

    return $description;
}

sub do_snapshot {
    my $hostname = shift; 
    my $instance_id = shift;
    my $volume_id = shift;
    my $device = shift;  
    my $description = shift;
    my $desc = get_description($hostname,$instance_id,$volume_id,$device,$description);

    if (defined($dryrun)) {
        print "info: created snapshot with description => $desc\n" if $info;
        return;
    }

    my $method_call = "create_snapshot";
    my %method_args = (VolumeId => $volume_id, Description => $desc);

    my $snapshot_id = error_check($method_call,%method_args);
    print "info: created snapshot with snapshotid => " . $snapshot_id->snapshot_id . " with description => $desc\n" if $info;
}

sub run_all_snapshots {
    my $hostname = shift;
    my $instance_id = shift;
    my $volume_ids = shift;

    foreach my $volume_id (@$volume_ids) {
        my $volume_info = get_volume_info($volume_id);
        do_snapshot($hostname,$instance_id,$volume_id,$volume_info->{device},$description);
    }
}

sub run_snapshot_for_device {
    my $hostname = shift;
    my $instance_id = shift;
    my $volume_ids = shift;

    foreach my $volume_id (@$volume_ids) {
        my $volume_info = get_volume_info($volume_id);
        next unless ($volume_info->{device} eq $device);
        print "debug: volume $volume_id with attached device " . $volume_info->{device} . " matches device $device parameter\n" if $verbose;
        do_snapshot($hostname,$instance_id,$volume_id,$volume_info->{device},$description);
    }

}

sub run_snapshot {
    my $hostname = shift;
    my $instance_id = shift;
    my $volume_ids = get_attached_volumeids($instance_id);
    if (defined($all)) {
        run_all_snapshots($hostname, $instance_id, $volume_ids);
    } elsif (defined($device)) {
        run_snapshot_for_device($hostname, $instance_id, $volume_ids);
    } else {
        die "error: either supply the --all option or specify a device e.g. --device /dev/sdj\n";
    }
}

#MAIN

if (!defined($instance_id) && !defined($hostname)) {
    die "\nUsage:\n\nExample: $0 --hostname author01-uat --device /dev/sdj\nExample: $0 --instanceid i-1234567 --all\n\n";
}

$instance_id = get_instanceid_from_hostname($hostname) if (!defined($instance_id));
die "error: no instance found!\n" if (!defined($instance_id));

run_snapshot($hostname,$instance_id);
