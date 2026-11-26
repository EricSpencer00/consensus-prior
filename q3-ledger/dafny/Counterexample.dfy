// Concrete ledger on which naive retraction keeps an unsupported belief.
include "Ledger.dfy"

lemma NaiveCycle()
  ensures var J := {Just({0}, 2), Just({3}, 2), Just({2}, 3)};
          // after retracting assumption 0: x=2, y=3 support each other
          LocallySupported({2, 3}, {}, J) && !InCl(2, {}, J)
{
  var J := {Just({0}, 2), Just({3}, 2), Just({2}, 3)};
  assert Just({3}, 2) in J && Just({2}, 3) in J;
  assert Closed({}, J);
}
