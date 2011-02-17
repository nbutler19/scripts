#!/usr/bin/perl

#TODO:
# 1. Return 'not found' if no volumes attached
# 2. Return 'no match' if device name doesn't match any attached devices

use strict;
use warnings;
use Net::Amazon::EC2;
use Net::DNS;
use Getopt::Long;

my $aws_access_key_id = ENV{'AWS_ACCESS_KEY_ID'};
my $aws_secret_key_id = ENV{'AWS_SECRET_KEY_ID'};

# Debug flags. $debug is useful for seeing the entire api response. $verbose is just internal script print statements.
my $debug = 0;
my $verbose = 0;
my $hostname = undef;

GetOptions ("debug!" => \$debug,
            "verbose!" => \$verbose,
            "hostname=s" => \$hostname);

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

sub usage {
    die "\nUsage:\n\nExample: $0 --hostname author01-uat\n\n";
}

#MAIN

if (!defined($hostname)) {
    usage();
}

my $instance_id = get_instanceid_from_hostname($hostname);

die "error: no instance_id found!\n" if (!defined($instance_id));

print "InstanceId => $instance_id\n";
