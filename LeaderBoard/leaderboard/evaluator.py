import awkward as ak
import numpy as np
import uproot

def EvaluateDIRC(submit, reference):
    accuracy = -1.0
    e = None
    try:
        reference = uproot.open({reference: "events"})
        submit = uproot.open({submit: "events"})
        reference_target = reference["_DIRCBarrelParticleIDPIDTarget_int64Data"].array()
        reference_target_is_pion = reference_target[:,0] == 1
        reference_target_is_kaon = reference_target[:,1] == 1
        assert ak.all(reference_target_is_pion | reference_target_is_kaon)
        assert not ak.any(reference_target_is_pion & reference_target_is_kaon)
        submitted_pdg = submit["ReconstructedChargedWithRealDIRCParticles.PDG"].array()

        def is_correct_pdg_array(pdg):
            if not ak.all(ak.count(submitted_pdg, axis=1) == 1):
                return False
            t0 = ak.type(pdg)
            if not isinstance(t0, ak.types.ArrayType):
                return False
            t1 = t0.content
            if not isinstance(t1, ak.types.ListType):
                return False
            t2 = t1.content
            if not isinstance(t2, ak.types.NumpyType):
                return False
            return True

        if not is_correct_pdg_array(submitted_pdg):
            1/0

        accuracy = ak.mean(
            (reference_target_is_pion & (np.abs(submitted_pdg) == 211))
            +
            (reference_target_is_kaon & (np.abs(submitted_pdg) == 321))
        )
    except Exception as _e:
        e = str(_e)

    return accuracy, e

def EvaluateLowQ2(submit, reference):
    accuracy = -1.0
    e = None
    # TODO: Implement the evaluation logic
    return accuracy, e