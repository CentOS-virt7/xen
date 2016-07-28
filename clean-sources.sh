#!/bin/bash

(perl -ne 'if(/^Version.* ([0-9.]+)$/) { $version=$1; } if(/^Patch[0-9]+: (.*)$/ || /^Source[0-9]+: (.*)$/) { $f=$1; if($f=~/http:.*\/([^\/]+)$/) {$f=$1;} $f=~s/%{version}/$version/; print "$f\n"; }' SPECS/xen.spec && ls SOURCES) | sort | uniq -u | (cd SOURCES; xargs rm)
