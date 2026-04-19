import cps.data.manifest as cps_manifest
import cps.runtime.config as cps_config
import cps.runtime.cohort as cps_cohort
import cps.runtime.phase0_smoke as cps_phase0_smoke
import cps.runtime.phase1_smoke as cps_phase1_smoke
import cps.store.measurement as cps_measurement
import phase0.manifest as legacy_manifest
import phase0.measurement_store as legacy_measurement
import phase0.smoke as legacy_phase0_smoke
import phase1.config as legacy_config
import phase1.run as legacy_run
import phase1.smoke as legacy_smoke


def test_phase0_shims_reexport_cps_symbols():
    assert legacy_manifest.load_manifest is cps_manifest.load_manifest
    assert legacy_manifest.validate_manifest is cps_manifest.validate_manifest
    assert legacy_measurement.append_event is cps_measurement.append_event
    assert legacy_phase0_smoke.run_phase0_smoke is cps_phase0_smoke.run_phase0_smoke


def test_phase1_shims_reexport_cps_symbols():
    assert legacy_config.load_phase1_context is cps_config.load_phase1_context
    assert legacy_smoke.run_phase1_smoke is cps_phase1_smoke.run_phase1_smoke
    assert legacy_run.run_phase1_cohort is cps_cohort.run_phase1_cohort
    assert callable(legacy_smoke.main)
    assert callable(legacy_run.main)
