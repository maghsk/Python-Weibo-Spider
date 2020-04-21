#!/bin/bash
find -regex ".*\.\(pdf\|py\|ui\|txt\|model\|md\)" -exec tar -rvf submit.tar {} \;
xz -z -9 submit.tar
mv submit.tar.xz '期中大作业.tar.xz'
