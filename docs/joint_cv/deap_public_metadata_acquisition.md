# DEAP Public Metadata Acquisition

- Decision: **PUBLIC_MIRROR_CONSENSUS_ACQUIRED**
- Installed file: `/home/armin/Downloads/DEAP_metadata/participant_ratings.csv`
- Canonical SHA-256: `ca239332dfb86d3f1ddafa5ebf9650ab4bf576e47bf70af6552571eb26d997e1`
- Successful mirrors: `3`
- Failed mirrors: `0`
- Rows: `1280`
- Participants: `32`
- Trials per participant: `40`
- Every participant contains Experiment_id `1..40` exactly once
- All successfully downloaded mirrors are identical after normalization

## Scientific Verification Boundary

Mirror agreement is not sufficient by itself. The installed CSV must match all local DEAP embedded ratings. The repository resolver performs that independent 32 × 40 × 4 alignment test.

## Sources

- `dweidai/DEAP-JRP-Emotion-Classification` at commit `7c34612f7da98b63c4b9133e787f4e219cd69dcd`
  - download SHA-256: `249a402f167e8726e2d5dcf36ce38ade57815f0a132347a9ba20e81a06a1d88f`
  - normalized SHA-256: `ca239332dfb86d3f1ddafa5ebf9650ab4bf576e47bf70af6552571eb26d997e1`
- `hsiehjackson/Emotion-Recognition-DEAP_GSR` at commit `0d00e8f41f9f61fa732eb806cc44f63dba71e325`
  - download SHA-256: `7bc0c19d31769b01597866ca55b59221635a7bf4237a27c820ef437e1d8ea1b8`
  - normalized SHA-256: `ca239332dfb86d3f1ddafa5ebf9650ab4bf576e47bf70af6552571eb26d997e1`
- `pnvamshi/Prediction-of-Emotions-Using-Machine-Learning` at commit `5cc302657af43d66000e0cfee0bca883dedf165a`
  - download SHA-256: `7bc0c19d31769b01597866ca55b59221635a7bf4237a27c820ef437e1d8ea1b8`
  - normalized SHA-256: `ca239332dfb86d3f1ddafa5ebf9650ab4bf576e47bf70af6552571eb26d997e1`
