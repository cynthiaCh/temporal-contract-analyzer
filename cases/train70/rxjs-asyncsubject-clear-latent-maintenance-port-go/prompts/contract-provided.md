Additional contract information:

Once completion has committed to delivering a final value, that terminal decision must remain observable throughout callbacks, even before the outer complete call returns. A clear invoked from such a callback must not erase the value or completion seen by a subscription created inside the callback or by later subscribers. Preserve the distinction between final-value delivery in progress and an active subject.
