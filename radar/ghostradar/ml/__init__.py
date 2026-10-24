"""Data-science layer: survival baselines, ground truth (audits, outcomes, labelling functions) and a calibrated model.

It follows the validation design in reports/Ghost job signals in Germany.md: lifetimes are judged with survival
methods against comparable postings; ground truth is built from audits and outcomes rather than assumed; weak labels
are combined in a label model and never used to declare unlabelled postings genuine; and the hand-set weights are
replaced by a calibrated model only as audited labels arrive, evaluated by precision at a review budget and by
calibration rather than accuracy.
"""
