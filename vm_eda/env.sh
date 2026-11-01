#!/usr/bin/env bash
# Process-local setup; never edits the guest account or tool installations.
export KWT_VM_ROOT=/home/eda/kwt_vm_20261101
test "$(id -un)" = eda || return 1
export CDS_LIC_FILE=/opt/eda2/license/cadence.dat
export GENUS_HOME=/opt/eda2/cadence/GENUS212/HOTFIX
export XCELIUM_HOME=/opt/eda2/cadence/XCELIUM2003
export TEMPUS_HOME=/opt/eda2/cadence/SSV211
export KWT_PYROOT=$XCELIUM_HOME/tools.lnx86/mce/python
export PATH=$KWT_PYROOT/bin:$XCELIUM_HOME/tools.lnx86/inca/bin:$GENUS_HOME/bin:$GENUS_HOME/tools.lnx86/bin:$TEMPUS_HOME/bin:$TEMPUS_HOME/tools.lnx86/ssv/bin/64bit:$PATH
export LD_LIBRARY_PATH=$KWT_PYROOT/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
export TMPDIR=$KWT_VM_ROOT/tmp TEMP=$KWT_VM_ROOT/tmp TMP=$KWT_VM_ROOT/tmp
export KWT_GPDK=/opt/eda2/gpdk045/gsclib045_all_v4.4/gsclib045
