"""
Code developped by Paul Malisani
IFP Energies nouvelles
Applied mathematics department
paul.malisani@ifpen.fr


Mathematical details on the methods can be found in

Interior Point Methods in Optimal Control Problems of Affine Systems: Convergence Results and Solving Algorithms
SIAM Journal on Control and Optimization, 61(6), 2023
https://doi.org/10.1137/23M1561233

and

Interior Point methods in Optimal Control, in review,
http://dx.doi.org/10.13140/RG.2.2.20384.76808

Please cite these papers if you are using these methods.
"""
from Goddard.GoddardPrimalDualOCPAD import GoddardPrimalDual
from timeit import default_timer as dtime
from utils_functions import plot_sequence
import matplotlib.pyplot as plt
import pickle
from bvpdae_solver import BVPDAE, BVPSol
import json                               # for saving computations

def main_primal_dual():
    cumul_time = 0.
    eps = 1.
    alpha = .5
    tol = 1e-10
    ocp = GoddardPrimalDual()
    ocp.set_eps(eps)
    time, xp, z = ocp.initialize()
    initial_solution = dict(time=time, xp=xp, z=z)
    bvp_sol = BVPSol(time=time, xp=xp, z=z)
    options = dict(control_odes_error=True, display=1, res_tol=1e-6)
    bvp_solver = BVPDAE(**options)
    convergence = False
    iter = 0
    times, hs, vs, ms, us, p1s, p2s, p3s, mus, nups, nums, qs = [list() for _ in range(12)]

    while not convergence:
        print("eps = ", eps)
        print("alpha = ", alpha)
        ts0 = dtime()
        bvp_sol, infos = bvp_solver.solve(bvp_sol, ocp)
        ts1 = dtime()
        cumul_time += ts1 - ts0
        if not infos.success:
            raise Exception("Primal-dual Goddard problem failed before convergence")
        time, xp, z = bvp_sol.time, bvp_sol.xp, bvp_sol.z
        convergence = eps <= tol
        eps *= alpha
        ocp.set_eps(eps)
        times.append(xp[3, 0] * time)
        hs.append(xp[0, :])
        vs.append(xp[1, :])
        ms.append(xp[2, :])
        qs.append(ocp.dyn_press(xp[0, :], xp[1, :]))
        us.append(z[0, :])
        p1s.append(xp[4, :])
        p2s.append(xp[5, :])
        p3s.append(xp[6, :])
        mus.append(z[1, :])
        nups.append(z[2, :])
        nums.append(z[3, :])
        iter += 1
        print(" ")
    optimal_solution = dict(time=time, xp=xp, z=z, eps=eps / alpha, alpha=alpha, exec_time=cumul_time, iter=iter)
    dict_save = dict(initial_solution=initial_solution, optimal_solution=optimal_solution)
    with open("Goddard/results_goddard_primal_dual.pickle", "wb") as fh:
        pickle.dump(dict_save, fh)
    plot_sequence(times, mus, "$\mu(t)$",
                  "Sequence of optimal penalized state-constraint multiplier $\\bar{\lambda}_\epsilon^g$")
    plot_sequence(times, nups, "$\eta_1(t)$",
                  "Sequence of optimal penalized first mixed-constraint multiplier $\\bar{\lambda}_{1,\epsilon}^c$")
    plot_sequence(times, nums, "$\eta_2(t)$",
                  "Sequence of optimal penalized second mixed-constraint multiplier $\\bar{\lambda}_{2,\epsilon}^c$")
    plot_sequence(times, p3s, "$p_3(t)$", "Sequence of optimal penalized adjoint state $\\bar{p}_{3,\epsilon}$")
    plot_sequence(times, p2s, "$p_2(t)$", "Sequence of optimal penalized adjoint state $\\bar{p}_{2, \epsilon}$")
    plot_sequence(times, p1s, "$p_1(t)$", "Sequence of optimal penalized adjoint state $\\bar{p}_{1, \epsilon}$")
    plot_sequence(times, qs, "$q(t)$", "Sequence of optimal penalized dynamic pressure $q(\\bar{h}_\epsilon, \\bar{v}_\epsilon)$")
    plot_sequence(times, us, "$u(t)$", "Sequence of optimal penalized thrust $\\bar{u}_{\epsilon}$")
    plot_sequence(times, ms, "$m(t)$", "Sequence of optimal penalized mass $\\bar{m}_\epsilon$")
    plot_sequence(times, vs, "$v(t)$", "Sequence of optimal penalized velocity $\\bar{v}_\epsilon$")
    plot_sequence(times, hs, "$h(t)$", "Sequence of optimal penalized altitude $\\bar{h}_\epsilon$")
    plt.figure()
    plt.plot(time * xp[3, 0], z[0])

    print("Time final = ", xp[3, 0])
    print("Altitude = ", xp[0, -1])
    print("Execution time = ", cumul_time)
    print("Number of iterations = ", len(times))
    print("Number of final time steps = ", len(time))

    # save json file
    data_solution = {'t':time.tolist(), 'xp':xp.tolist(), 'z':z.tolist()}
    json_object = json.dumps(data_solution, ensure_ascii=False, indent=4)
    with open("Goddard/results_goddard_primal_dual.json", 'w', encoding='utf-8') as outfile:
        outfile.write(json_object)
        outfile.close()

    return optimal_solution


if __name__ == "__main__":
    _ = main_primal_dual()
    plt.show()