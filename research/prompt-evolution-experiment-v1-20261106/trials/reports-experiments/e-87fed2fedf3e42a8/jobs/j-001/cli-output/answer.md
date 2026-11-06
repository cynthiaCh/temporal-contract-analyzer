The Personnel editor now loads its local JSON configuration and waits until the form API is ready before applying it, preserving the parent values and picker behavior. The Structure editor is unchanged.

I verified the JSON fields and confirmed that only Structure still calls `getStaticConfig`. The candidate has no test or build script, so I did not run a Vue runtime test.