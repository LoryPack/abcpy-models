# add to the pythonpath the current folder (otherwise it does not find the script files)
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), os.pardir)))

from algorithms import contrastive_training, triplet_training, sdml_fit
from utilities import compute_similarity_matrix, estimate_params_from_distance, dist2

import numpy as np
import torch
from sklearn.model_selection import LeaveOneOut, train_test_split
from sklearn.preprocessing import MinMaxScaler

from utilities import read_simulations, estimate_TV_distances, estimate_KL_distances

cuda = torch.cuda.is_available()
device = "cuda" if cuda else "cpu"
print(device)

param1, param2, output = read_simulations('training_data.txt')
folder = "cross-valid-results/epsilon_sensitivity_study/"
names = ["contrastive_batch32_epochs400", "triplet_batch16_epochs800", "sdml"]
scaler = MinMaxScaler()

output_train, test_data, train_labels, test_labels = train_test_split(output, np.column_stack((param1, param2)),
                                                                      test_size=100, shuffle=False)
param1_train = train_labels[:, 0]
param2_train = train_labels[:, 1]
param1_test = test_labels[:, 0]
param2_test = test_labels[:, 1]

# epsilon_values = [0.02, 0.04, 0.06, 0.08, 0.10, 0.12, 0.14, 0.16, 0.18, 0.20]
epsilon_values = np.arange(0.02, 1.02, 0.02)

# open the ground truth (i.e. the tre distances on those points)
embedding_distances_true = np.load("cross-valid-results/true_embedding_distances.npy")

for epsilon in epsilon_values:

    print("Epsilon: ", epsilon)

    # compute the similarity matrix
    similarity_set = compute_similarity_matrix(param1_train, param2_train, epsilon)

    for name in names:
        print("Technique: ", name)

        if name == 'contrastive_batch32_epochs400':
            embedding_net = contrastive_training(output_train, similarity_set, cuda, positive_weight=0.4, batch_size=32,
                                                 n_epochs=400)

        if name == 'triplet_batch16_epochs800':
            embedding_net = triplet_training(output_train, similarity_set, cuda, n_epochs=800)

        if name == 'sdml':
            is_sdml = True
            sdml_index = 0

            n_runs = 0
            max_runs = 25
            while n_runs < max_runs:
                n_runs += 1
                try:
                    sdml = sdml_fit(output_train, similarity_set, prior='covariance')
                except:
                    continue
                else:
                    print("It took {} time(s) before the algorithm converged.".format(n_runs))
                    break

            if n_runs == max_runs:  # if the alg does not converges for max_runs times, then skip this observation
                print(
                    "SDML was not able to converge in less than {} attempts. ".format(max_runs))
                continue
        else:
            is_sdml = False

        loo = LeaveOneOut()
        estimated_parameters = []
        true_parameters_list = []
        parameter_distances = []
        embedding_distances = []

        estimated_KL = []
        estimated_TV = []

        for ref_index, obs_index in loo.split(test_data, test_labels):  # this returns the indices

            # split the dataset
            n_samples = len(ref_index)

            output_ref = test_data[ref_index]
            param1_ref = param1_test[ref_index]
            param2_ref = param2_test[ref_index]

            observation = test_data[obs_index]
            param1_obs = param1_test[obs_index]
            param2_obs = param2_test[obs_index]
            true_parameters = np.array([param1_obs, param2_obs]).reshape(-1)

            if name == 'true':
                output_ref_transformed = np.column_stack((param1_ref, param2_ref))
                observation_transformed = true_parameters

            if name == 'naive':
                output_ref_transformed = output_ref
                observation_transformed = observation

            if name in ('contrastive_batch32_epochs150', 'triplet_batch16_epochs800', 'contrastive_batch32_epochs400'):
                observation_transformed = embedding_net(
                    torch.from_numpy(observation.astype("float32")).to(device)).cpu().detach().numpy()
                output_ref_transformed = embedding_net(
                    torch.from_numpy(output_ref.astype("float32")).to(device)).cpu().detach().numpy()

            if name == 'sdml':
                observation_transformed = sdml.transform(observation)[0]
                output_ref_transformed = sdml.transform(output_ref)

            # transform and compute distances

            # compute now the distances:

            distances = np.zeros((n_samples))
            for i in range(n_samples):
                distances[i] = dist2(output_ref_transformed[i].reshape(-1), observation_transformed.reshape(-1))

            embedding_distances.append(distances)

            # estimate parameter from distance (the one with smallest learned distance):
            estimated_parameters.append(estimate_params_from_distance(param1_ref, param2_ref, distances))

            # and compute the distance from the estimated parameter to the true one.
            parameter_distances.append(np.array([param1_obs, param2_obs]).reshape(-1) - estimated_parameters[-1])

            true_parameters_list.append(true_parameters)

            # now compute the divergences:

            if is_sdml:
                if param1_obs == true_parameters_list[sdml_index][0] and param2_obs == true_parameters_list[
                    sdml_index][1]:
                    sdml_index += 1
                else:
                    continue  # skip this split as it was not successful when fitting the sdml technique. 

            test_index = sdml_index - 1 if is_sdml else obs_index[0]

            # select the correct distance now: 
            true_distances = embedding_distances_true[test_index]

            # scale them in [0,1]
            distances = scaler.fit_transform(distances.reshape(-1, 1)).reshape(-1)
            true_distances = scaler.fit_transform(true_distances.reshape(-1, 1)).reshape(-1)

            # estimate the KL and append
            estimated_KL.append(estimate_KL_distances(distances, true_distances, beta=1))
            estimated_TV.append(estimate_TV_distances(distances, true_distances, beta=1))

        if is_sdml:
            # keep this for retro compatibility, even if it is not needed here
            np.save(folder + "/" + name + "_true_params" + "epsilon_{:.2f}".format(epsilon),
                    np.array(true_parameters_list))
        np.save(folder + "/" + name + "_params" + "epsilon_{:.2f}".format(epsilon), np.array(estimated_parameters))
        np.save(folder + "/" + name + "_param_distances" + "epsilon_{:.2f}".format(epsilon),
                np.array(parameter_distances))
        np.save(folder + "/" + name + "_embedding_distances" + "epsilon_{:.2f}".format(epsilon),
                np.array(embedding_distances))
        np.save(folder + "/" + name + "_estimated_KL_IS_distance_functions" + "epsilon_{:.2f}".format(epsilon),
                np.array(estimated_KL))
        np.save(folder + "/" + name + "_estimated_TV_IS_distance_functions" + "epsilon_{:.2f}".format(epsilon),
                np.array(estimated_TV))
