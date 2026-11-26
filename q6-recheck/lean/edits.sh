#!/bin/zsh
# Incremental recheck experiments on Mathlib v4.33.0 after a full build.
cd ~/scratch/q6-mathlib
F=Mathlib/Algebra/Group/Basic.lean
cp $F /tmp/q6-Basic.orig
run() { # name
  echo "== $1 $(date +%T) load=$(sysctl -n vm.loadavg)"
  /usr/bin/time -p lake build Mathlib > ~/scratch/q6-$1.log 2> ~/scratch/q6-$1.time
  echo "rc=$? built=$(grep -c 'Built\|Replayed' ~/scratch/q6-$1.log) $(grep -c '✔ \[.*Built' ~/scratch/q6-$1.log) $(tail -3 ~/scratch/q6-$1.time | tr '\n' ' ')"
}
run e0-noop
# E1: one-line proof change, statement unchanged
sed -i '' 's/  rw \[← mul_assoc, mul_comm a, mul_assoc\]/  rw [← mul_assoc, mul_comm a b, mul_assoc]/' $F
diff /tmp/q6-Basic.orig $F
run e1-proof
cp /tmp/q6-Basic.orig $F; run e2-revert
# E3: add a public lemma (interface change)
printf '\ntheorem q6_probe {M : Type*} [MulOneClass M] (a : M) : a * 1 = a := mul_one a\n' >> $F
run e3-newlemma
cp /tmp/q6-Basic.orig $F; run e4-revert
