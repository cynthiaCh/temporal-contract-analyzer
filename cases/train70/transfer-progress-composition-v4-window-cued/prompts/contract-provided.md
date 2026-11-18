# Provided contract

Apply the complete contract below together with `README.md`: register before warm
start; admit frames only while the attempt is current and not aborted; finish
and audit every admitted decode once; publish UI only for the current visit and
never behind a newer arrival; treat listener cleanup as a synchronous navigation
boundary where later-started commands win; preserve retry ownership and record
shape. The optional authorization alone adds `byteCount`.

Frame arrival order is visit-owned and continues across retry attempts. Accepted
decode always records audit once even after retirement; visible publication also
requires the originating visit and a token newer than its last published frame.
Removing a listener may synchronously navigate, so a later-started cleanup
navigation supersedes the older outer command before its destination starts.
The diagnostic telemetry consumer is delta-only: it intentionally starts before
attaching and must not receive cached bootstrap.
