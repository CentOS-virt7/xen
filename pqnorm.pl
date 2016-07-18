#!/usr/bin/env perl

open(QIN, "<", "SOURCES/xen-queue.am") or die "Can't open xen-queue.am!";

@lines = <QIN>;

close(QIN);

open(QOUT, ">", "SOURCES/xen-queue.am") or die "Can't open xen-queue.am!";

$after_diff_end = 0;
foreach $_ (@lines) {
    
    # Replace the commit hash (which will be different for each tree)
    # with a stock value
    if(/From [0-9a-f]* Mon Sep 17 00:00:00 2001/) {
	print QOUT "From git-format-patch Mon Sep 17 00:00:00 2001\n";
	next;
    }

    # Get rid of the version number after the diff
    if($after_diff_end && /^[0-9.]+$/) {
	$after_diff_end = 0;
	next;
    }

    # Detect the end of the diff
    if(/^-- $/) {
	#print "Setting after diff end\n";
	$after_diff_end = 1;
    } else {
	$after_diff_end = 0;
    }
    print QOUT $_;
}
