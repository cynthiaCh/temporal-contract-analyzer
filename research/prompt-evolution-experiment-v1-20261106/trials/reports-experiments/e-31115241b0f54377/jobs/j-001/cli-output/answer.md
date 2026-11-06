The Personnel editor now loads its local JSON configuration instead of requesting the retired endpoint. It waits for the form API before writing parent values, so the earlier config load does not lose that write. The Structure editor is unchanged.

Targeted source checks passed. I could not run a Vue runtime test because this workspace has no test script or Vue runtime setup.