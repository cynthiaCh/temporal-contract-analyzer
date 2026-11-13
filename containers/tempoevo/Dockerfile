# Reuse the provisioned public solver toolchains; never copy benchmark scorers.
ARG BASE=swe-tempoc:solver-sol61-low-g-20261021
FROM ${BASE}
USER root
RUN ln -s /runtime/node16/bin/node /runtime/node
ENV PATH="/runtime/node16/bin:/runtime/bin:/opt/go1.13.8/bin:/usr/local/bin:/usr/bin:/bin"
ENV NODE_PATH=/runtime/frontend/node_modules
