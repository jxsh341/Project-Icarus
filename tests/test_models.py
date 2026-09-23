"""Tests for canonical neuron and synapse records."""

from fly.neurons.models import NeuronRecord
from fly.synapses.models import Synapse


def test_neuron_record_defaults_to_optional_metadata() -> None:
    neuron = NeuronRecord(root_id=123)

    assert neuron.root_id == 123
    assert neuron.cell_type is None
    assert neuron.neurotransmitter is None
    assert neuron.region is None


def test_synapse_preserves_source_target_and_weight() -> None:
    synapse = Synapse(source=1, target=2, weight_or_count=3.5)

    assert synapse.source == 1
    assert synapse.target == 2
    assert synapse.weight_or_count == 3.5
    assert synapse.roi is None


def test_synapse_accepts_optional_roi() -> None:
    synapse = Synapse(source=1, target=2, weight_or_count=4, roi="GNG")

    assert synapse.roi == "GNG"
