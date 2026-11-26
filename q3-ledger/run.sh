#!/bin/sh
# Reproduce every Q3 check. Tools: tools/tla2tools.jar, tools/apalache-0.63.0 (see results.md),
# lean via elan, dafny via brew.
set -x
cd "$(dirname "$0")"
TLC="java -XX:+UseParallelGC -cp ../tools/tla2tools.jar tlc2.TLC -deadlock -workers auto"
APA=../tools/apalache-0.63.0/bin/apalache-mc

(cd tla
 for m in correct naive noseed; do $TLC -config Ledger_$m.cfg Ledger.tla > tlc_$m.log; done
 $TLC -config Ledger_naive_I2.cfg Ledger.tla > tlc_naive_I2.log
 $TLC -config Ledger_correct_ops4.cfg Ledger.tla > tlc_correct_ops4.log
 # inductive: Init => IndJ, IndJ /\ Next => IndJ', IndJ => I3
 $APA check --config=Apalache_correct_a1.cfg --length=0 --inv=IndJ Ledger.tla > apa_init_implies_indJ_a1.log
 for m in correct naive noseed; do
   $APA check --config=Apalache_${m}_a1.cfg --init=InitIndJ --length=1 --inv=IndJ Ledger.tla > apa_indJ_${m}_a1.log
 done
 $APA check --config=Apalache_correct_a2.cfg --init=InitIndJ --length=1 --inv=IndJ Ledger.tla > apa_indJ_correct_a2.log
 $APA check --config=Apalache_correct_a1.cfg --init=InitIndJ --length=0 --inv=I3_Complete Ledger.tla > apa_indJ_implies_I3_a1.log
 $APA check --config=Apalache_correct_a1.cfg --init=InitIndL3 --length=1 --inv=IndL3 Ledger.tla > apa_indL3_correct_a1.log
 # bounded model checking from Init
 $APA check --config=Apalache_noseed_a1.cfg --length=6 --inv=I3_Complete Ledger.tla > apa_bmc_noseed_a1.log
 $APA check --config=Apalache_naive_a1.cfg --length=8 --inv=I1q_LiveSupport Ledger.tla > apa_bmc_naive_a1.log
)
(cd lean && lake build)
(cd dafny && dafny verify Ledger.dfy && dafny verify Counterexample.dfy; dafny verify Controls.dfy || echo "Controls.dfy failed as expected")
