#!/usr/bin/env python
from __future__ import print_function
import argparse
import pickle
import matplotlib.pyplot as plt
import numpy as np
from mpi4py import MPI
import tb


comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

def main():
    def main(param_file, k_points_file, show, save):

        params = tb.yaml_parser(param_file)

        if k_points_file is None:
            if len(params['primitive_cell']) == 3:
                sym_points = ['L', 'GAMMA', 'X', 'W', 'K', 'L', 'W', 'X', 'K', 'GAMMA']
                num_points = [15, 20, 15, 10, 15, 15, 15, 15, 20]
                wave_vector = tb.get_k_coords(sym_points, num_points)
            else:
                wave_vector = [[0.0, 0.0, 0.0]]
        else:
            wave_vector = np.loadtxt(k_points_file)

        hamiltonian = tb.initializer(**params)

        band_structure = []

        for j, jj in enumerate(wave_vector):
            if j % size != rank:
                continue

            vals, vects = hamiltonian.diagonalize_periodic_bc(jj)
            band_structure.append({'id': j, 'wave_vector': jj, 'eigenvalues': vals, 'eigenvectors': vects})
            print('#{} '.format(j), " ".join(['{:.3f} '.format(element) for element in vals]))

        band_structure = comm.reduce(band_structure, root=0)

        if rank == 0:
            ids = [band_structure[item]['id'] for item in xrange(len(band_structure))]
            print(ids)

            band_structure = [x['eigenvalues'] for _, x in sorted(zip(ids, band_structure))]
            band_structure = np.array(band_structure)

            print(show)

            if show:
                axes = plt.axes()
                axes.set_title('Band structure')
                axes.set_xlabel('Wave vectors')
                axes.set_ylabel('Energy (eV)')
                axes.plot(band_structure)
                plt.show()

            if save:
                with open('./band_structure.pkl', 'wb') as f:
                    pickle.dump(band_structure, f, pickle.HIGHEST_PROTOCOL)


    parser = argparse.ArgumentParser()

    parser.add_argument('param_file', type=str,
                        help='Path to the yaml file containing parameters')

    parser.add_argument('--k_points_file', type=str, default=None,
                        help='Path to the file containing k points coordinates')

    parser.add_argument('--show', '-S', type=int, default=1,
                        help='Show figures, 0/1')

    parser.add_argument('--save', '-s', type=int, default=1,
                        help='Save results of computations on disk, 0/1')

    args = parser.parse_args()
    main(args.param_file, args.k_points_file, args.show, args.save)