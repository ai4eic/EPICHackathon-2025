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

    return accuracy, e, None



def EvaluateLowQ2(submit, reference):
    accuracy = -1.0
    e = None
    rme_momentum, rme_momentum_z, rme_momentum_theta = None, None, None
    try:
        reference = uproot.open({reference: "events"})
        submit = uproot.open({submit: "events"})
            
        # Full data set
        reference_momentum = reference["_TaggerTrackerTargetTensor_floatData"].array()
        submitted_momentum = submit["_TaggerTrackerPredictionTensor_floatData"].array()

        # Select only events with a single track
        num_tracks = submit["_TaggerTrackerPredictionTensor_shape"].array()[:,0]
        reference_momentum = reference_momentum[num_tracks == 1]
        submitted_momentum = submitted_momentum[num_tracks == 1]

        polar_angle = np.arctan2(np.sqrt(reference_momentum[:, 0]**2 + reference_momentum[:, 1]**2), reference_momentum[:, 2])

        # Multiply columns 0 and 1 by 100
        reference_momentum = (np.array(reference_momentum)*np.array([100,100,1]))
        submitted_momentum = (np.array(submitted_momentum)*np.array([100,100,1]))

        # Select only events with z > -0.7
        reference_momentum_z = reference_momentum[reference_momentum[:, 2] > -0.7]
        submitted_momentum_z = submitted_momentum[reference_momentum[:, 2] > -0.7]

        # Select only events where the polar angle is < pi-2 mrad
        reference_momentum_theta = reference_momentum[polar_angle < np.pi-0.002]
        submitted_momentum_theta = submitted_momentum[polar_angle < np.pi-0.002]

        rme_momentum = np.sqrt(np.mean((reference_momentum - submitted_momentum)**2))
        rme_momentum_z = np.sqrt(np.mean((reference_momentum_z - submitted_momentum_z)**2))
        rme_momentum_theta = np.sqrt(np.mean((reference_momentum_theta - submitted_momentum_theta)**2))
        
        score_sum = rme_momentum + rme_momentum_z + rme_momentum_theta
        if score_sum > 1.0:
            accuracy = 0.0
        else:
            accuracy = 1.0 - (np.exp(score_sum) - 1.0) / (np.exp(1.0) - 1.0)
    except Exception as _e:
        e = str(_e)
    _ = None if not rme_momentum else (rme_momentum, rme_momentum_z, rme_momentum_theta)
    return accuracy*100.0, e, _
