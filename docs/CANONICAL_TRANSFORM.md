# Canonical transformation

neuPrint snapshot rows are transformed into in-project canonical records via:
- `fly.data.transform.load_neuron_records_from_snapshot`
- `fly.data.transform.load_synapses_from_snapshot`
- `fly.data.transform.load_snapshot_directory`
- `fly.data.transform.summarize_snapshot_validation`

Current field mapping:
- neuron `bodyId` -> `NeuronRecord.root_id`
- neuron `type` -> `NeuronRecord.cell_type`
- neuron `instance` -> `NeuronRecord.instance`
- neuron `region` -> `NeuronRecord.region` when present in source rows
- adjacency `bodyId_pre` -> `Synapse.source`
- adjacency `bodyId_post` -> `Synapse.target`
- adjacency `weight` -> `Synapse.weight_or_count`

Current structural checks:
- neuron count
- edge count
- missing cell type count
- missing instance count
- missing region count
- dangling source count
- dangling target count
- self connection count
- duplicate edge count
