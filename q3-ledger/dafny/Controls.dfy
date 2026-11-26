// Broken retraction variants. Expected result: verification FAILS on both methods.
include "Ledger.dfy"

// noseed: forgets to re-seed with still-enabled assumptions downstream of a.
method DoRetractNoSeed(s: Ledger, a: nat) returns (t: Ledger)
  requires Inv(s)
  ensures Inv(t)
{
  var en := s.enabled - {a};
  var D := Down(s.J, a);
  var seed := s.believed - D;
  forall n | n in seed ensures InCl(n, en, s.J) { Avoid(n, s.enabled, s.J, a, D); }
  var b := Close(s.J, en, seed);   // precondition en <= seed fails
  t := Ledger(en, s.J, b, s.log + [Retract(a)]);
}

// naive (Doyle without well-foundedness): drop a, keep anything with a locally valid justification.

ghost method DoRetractNaive(s: Ledger, a: nat) returns (t: Ledger)
  requires Inv(s)
  ensures Inv(t)
{
  var en := s.enabled - {a};
  var b :| b <= s.believed - {a} && LocallySupported(b, en, s.J) && en <= b;
  t := Ledger(en, s.J, b, s.log + [Retract(a)]);
}
